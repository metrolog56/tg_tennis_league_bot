import os
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from api.dependencies import (
    get_current_player_id,
    get_supabase,
    optional_api_key,
    require_current_player_id,
)
from api.limiter import limiter
from api.rating_calc import calculate_match_rating

router = APIRouter(
    prefix="/matches",
    tags=["matches"],
    dependencies=[Depends(optional_api_key)],
)


def _get_division_by_id(supabase, division_id: str):
    r = supabase.table("divisions").select("*, season:seasons(*)").eq("id", division_id).execute()
    if r.data and len(r.data) > 0:
        return r.data[0]
    return None


def _recalc_division_standings(supabase, division_id: str) -> None:
    """
    Пересчитать totals в division_players по таблице matches для заданного дивизиона.
    Используется как защита от рассинхронизации между matches и division_players.
    """
    # Собираем все сыгранные матчи дивизиона
    matches_r = (
        supabase.table("matches")
        .select("player1_id, player2_id, sets_player1, sets_player2, status")
        .eq("division_id", division_id)
        .execute()
    )
    matches = matches_r.data or []

    totals = {}

    def ensure_player(pid: str):
        if pid not in totals:
            totals[pid] = {
                "points": 0,
                "sets_won": 0,
                "sets_lost": 0,
            }

    for m in matches:
        if m.get("status") != "played":
            continue
        p1 = m.get("player1_id")
        p2 = m.get("player2_id")
        s1 = int(m.get("sets_player1") or 0)
        s2 = int(m.get("sets_player2") or 0)
        if p1 is None or p2 is None:
            continue
        if s1 == s2:
            # Нечего считать, результат некорректен
            continue
        ensure_player(p1)
        ensure_player(p2)
        # Сеты
        totals[p1]["sets_won"] += s1
        totals[p1]["sets_lost"] += s2
        totals[p2]["sets_won"] += s2
        totals[p2]["sets_lost"] += s1
        # Очки: 2 за победу, 1 за поражение
        if s1 > s2:
            totals[p1]["points"] += 2
            totals[p2]["points"] += 1
        else:
            totals[p2]["points"] += 2
            totals[p1]["points"] += 1

    # Обновляем division_players только по агрегатам totals, не трогая rating_delta и position
    dp_r = (
        supabase.table("division_players")
        .select("id, player_id, total_points, total_sets_won, total_sets_lost")
        .eq("division_id", division_id)
        .execute()
    )
    for row in dp_r.data or []:
        pid = row.get("player_id")
        agg = totals.get(pid)
        if not agg:
            # Нет сыгранных матчей для этого игрока — оставляем как есть
            continue
        supabase.table("division_players").update(
            {
                "total_points": agg["points"],
                "total_sets_won": agg["sets_won"],
                "total_sets_lost": agg["sets_lost"],
            }
        ).eq("id", row["id"]).execute()


def _apply_match_result_as_played(supabase, match: dict) -> None:
    division_id = match["division_id"]
    p1_id = match["player1_id"]
    p2_id = match["player2_id"]
    sets1 = int(match.get("sets_player1") or 0)
    sets2 = int(match.get("sets_player2") or 0)

    division = _get_division_by_id(supabase, division_id)
    if not division:
        raise ValueError("Дивизион не найден.")
    coef = float(division.get("coef") or 0.25)
    season = division.get("season") or {}
    season_id = season.get("id") or division.get("season_id")
    if not season_id:
        raise ValueError("Сезон дивизиона не найден.")

    r1 = supabase.table("players").select("id, rating").eq("id", p1_id).execute()
    r2 = supabase.table("players").select("id, rating").eq("id", p2_id).execute()
    r1_val = float(r1.data[0]["rating"]) if r1.data else 100.0
    r2_val = float(r2.data[0]["rating"]) if r2.data else 100.0

    winner_id = p1_id if sets1 > sets2 else p2_id
    loser_id = p2_id if sets1 > sets2 else p1_id
    winner_sets = sets1 if sets1 > sets2 else sets2
    loser_sets = sets2 if sets1 > sets2 else sets1
    winner_rating_before = r1_val if sets1 > sets2 else r2_val
    loser_rating_before = r2_val if sets1 > sets2 else r1_val

    delta_winner, delta_loser = calculate_match_rating(
        winner_rating_before, loser_rating_before, winner_sets, loser_sets, coef
    )
    winner_rating_after = round((winner_rating_before + delta_winner) * 100) / 100
    loser_rating_after = round((loser_rating_before + delta_loser) * 100) / 100

    now_iso = datetime.now(timezone.utc).isoformat()
    supabase.table("matches").update({"status": "played", "played_at": now_iso}).eq("id", match["id"]).execute()
    supabase.table("players").update({"rating": winner_rating_after}).eq("id", winner_id).execute()
    supabase.table("players").update({"rating": loser_rating_after}).eq("id", loser_id).execute()

    for pid, pts, swon, slost, delta in [
        (winner_id, 2, winner_sets, loser_sets, delta_winner),
        (loser_id, 1, loser_sets, winner_sets, delta_loser),
    ]:
        dp = (
            supabase.table("division_players")
            .select("id, total_points, total_sets_won, total_sets_lost, rating_delta")
            .eq("division_id", division_id)
            .eq("player_id", pid)
            .execute()
        )
        if dp.data:
            row = dp.data[0]
            supabase.table("division_players").update({
                "total_points": (row.get("total_points") or 0) + pts,
                "total_sets_won": (row.get("total_sets_won") or 0) + swon,
                "total_sets_lost": (row.get("total_sets_lost") or 0) + slost,
                "rating_delta": round((row.get("rating_delta") or 0) + delta, 2),
            }).eq("id", row["id"]).execute()

    supabase.table("rating_history").insert([
        {
            "player_id": winner_id,
            "match_id": match["id"],
            "season_id": season_id,
            "rating_before": winner_rating_before,
            "rating_delta": delta_winner,
            "rating_after": winner_rating_after,
        },
        {
            "player_id": loser_id,
            "match_id": match["id"],
            "season_id": season_id,
            "rating_before": loser_rating_before,
            "rating_delta": delta_loser,
            "rating_after": loser_rating_after,
        },
    ]).execute()

    # После применения результата матча пересчитываем агрегаты standings для дивизиона
    _recalc_division_standings(supabase, division_id)


class SubmitForConfirmationBody(BaseModel):
    division_id: str
    player1_id: str
    player2_id: str
    sets_player1: int
    sets_player2: int
    submitted_by: str


class ConfirmRejectBody(BaseModel):
    confirmed_by_player_id: Optional[str] = None
    rejected_by_player_id: Optional[str] = None


@router.get("/pending")
def get_pending_confirmation(
    player_id: str,
    supabase=Depends(get_supabase),
    current_player_id=Depends(require_current_player_id),
):
    """Matches with status pending_confirm where the given player is the opponent (must confirm).
    Only returns pending matches for the current caller (player_id must equal X-Player-Id).
    """
    if current_player_id != player_id:
        raise HTTPException(status_code=403, detail="Access denied: only your own pending matches")
    r = (
        supabase.table("matches")
        .select("id, division_id, player1_id, player2_id, sets_player1, sets_player2, submitted_by")
        .eq("status", "pending_confirm")
        .or_(f"player1_id.eq.{player_id},player2_id.eq.{player_id}")
        .execute()
    )
    rows = r.data or []
    return [m for m in rows if m.get("submitted_by") != player_id]


@router.get("/{match_id}")
def get_match_by_id(
    match_id: str,
    supabase=Depends(get_supabase),
    current_player_id=Depends(get_current_player_id),
):
    """Single match with player1/player2 names (for confirm screen).
    If X-Player-Id is sent, access is restricted to participants (player1 or player2).
    """
    r = (
        supabase.table("matches")
        .select("id, division_id, player1_id, player2_id, sets_player1, sets_player2, status, submitted_by, division:divisions(id, season_id)")
        .eq("id", match_id)
        .execute()
    )
    if not r.data or len(r.data) == 0:
        raise HTTPException(status_code=404, detail="Match not found")
    match = r.data[0]
    if current_player_id is not None:
        p1, p2 = match.get("player1_id"), match.get("player2_id")
        if current_player_id != p1 and current_player_id != p2:
            raise HTTPException(status_code=403, detail="Access denied: only participants can view this match")
    p1 = supabase.table("players").select("id, name, telegram_id").eq("id", match["player1_id"]).execute()
    p2 = supabase.table("players").select("id, name, telegram_id").eq("id", match["player2_id"]).execute()
    match["player1"] = p1.data[0] if p1.data else None
    match["player2"] = p2.data[0] if p2.data else None
    return match


@router.post("/submit-for-confirmation")
def submit_for_confirmation(
    body: SubmitForConfirmationBody,
    supabase=Depends(get_supabase),
    current_player_id=Depends(require_current_player_id),
):
    """Submit result for opponent confirmation; does not update ratings.
    submitted_by must match X-Player-Id (caller identity).
    """
    if current_player_id != body.submitted_by:
        raise HTTPException(status_code=403, detail="Access denied: submitted_by must be the current player")
    existing = None
    for p1, p2 in [(body.player1_id, body.player2_id), (body.player2_id, body.player1_id)]:
        r = (
            supabase.table("matches")
            .select("id, status")
            .eq("division_id", body.division_id)
            .eq("player1_id", p1)
            .eq("player2_id", p2)
            .execute()
        )
        if r.data and len(r.data) > 0:
            existing = r.data[0]
            break
    if existing and existing.get("status") == "played":
        raise HTTPException(status_code=400, detail="Этот матч уже внесён.")

    payload = {
        "division_id": body.division_id,
        "player1_id": body.player1_id,
        "player2_id": body.player2_id,
        "sets_player1": body.sets_player1,
        "sets_player2": body.sets_player2,
        "status": "pending_confirm",
        "submitted_by": body.submitted_by,
        "played_at": None,
    }
    if existing:
        r = supabase.table("matches").update(payload).eq("id", existing["id"]).select().execute()
    else:
        r = supabase.table("matches").insert(payload).select().execute()
    if r.data and len(r.data) > 0:
        match_row = r.data[0]
        _trigger_instant_notify(match_row["id"])
        return match_row
    raise HTTPException(status_code=500, detail="Failed to save match")


def _trigger_instant_notify(match_id: str) -> None:
    """Вызвать бота для мгновенной отправки уведомления сопернику (без блокировки ответа)."""
    url = (os.getenv("BOT_NOTIFY_URL") or "").strip().rstrip("/")
    if not url:
        return
    secret = (os.getenv("NOTIFY_SECRET") or "").strip()
    headers = {"X-Notify-Secret": secret} if secret else {}
    try:
        with httpx.Client(timeout=5.0) as client:
            client.post(
                f"{url}/notify-pending-match",
                json={"match_id": match_id},
                headers=headers,
            )
    except Exception:
        pass


@router.post("/{match_id}/notify-pending")
@limiter.limit("10/minute")
def notify_pending_match(
    request: Request,
    match_id: str,
    supabase=Depends(get_supabase),
    current_player_id=Depends(require_current_player_id),
):
    """Запросить у бота немедленную отправку уведомления сопернику.
    Only a match participant (player1 or player2) may call this.
    """
    r = supabase.table("matches").select("player1_id, player2_id").eq("id", match_id).execute()
    if not r.data or len(r.data) == 0:
        raise HTTPException(status_code=404, detail="Match not found")
    row = r.data[0]
    if current_player_id not in (row.get("player1_id"), row.get("player2_id")):
        raise HTTPException(status_code=403, detail="Access denied: only participants may request notify")
    url = (os.getenv("BOT_NOTIFY_URL") or "").strip().rstrip("/")
    if not url:
        raise HTTPException(status_code=503, detail="Instant notify not configured")
    secret = (os.getenv("NOTIFY_SECRET") or "").strip()
    headers = {"X-Notify-Secret": secret} if secret else {}
    try:
        r = httpx.post(
            f"{url}/notify-pending-match",
            json={"match_id": match_id},
            headers=headers,
            timeout=5.0,
        )
        if r.status_code == 401:
            raise HTTPException(status_code=502, detail="Notify unauthorized")
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail="Notify failed")
        return r.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail="Notify service unreachable") from e


@router.post("/{match_id}/confirm")
def confirm_match(
    match_id: str,
    body: ConfirmRejectBody,
    supabase=Depends(get_supabase),
    current_player_id=Depends(require_current_player_id),
):
    """Confirm match result (opponent). Applies rating and division stats.
    confirmed_by_player_id must match X-Player-Id (caller identity).
    """
    confirmed_by = body.confirmed_by_player_id
    if not confirmed_by:
        raise HTTPException(status_code=422, detail="confirmed_by_player_id required")
    if current_player_id != confirmed_by:
        raise HTTPException(status_code=403, detail="Access denied: confirmed_by_player_id must be the current player")
    r = supabase.table("matches").select("*").eq("id", match_id).execute()
    if not r.data or len(r.data) == 0:
        raise HTTPException(status_code=404, detail="Матч не найден или уже обработан.")
    row = r.data[0]
    if row.get("status") != "pending_confirm":
        raise HTTPException(status_code=400, detail="Матч не найден или уже обработан.")
    if confirmed_by != row.get("player1_id") and confirmed_by != row.get("player2_id"):
        raise HTTPException(status_code=403, detail="Вы не участник этого матча.")
    if confirmed_by == row.get("submitted_by"):
        raise HTTPException(status_code=400, detail="Подтверждать должен соперник.")
    try:
        _apply_match_result_as_played(supabase, row)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.post("/{match_id}/reject")
def reject_match(
    match_id: str,
    body: ConfirmRejectBody,
    supabase=Depends(get_supabase),
    current_player_id=Depends(require_current_player_id),
):
    """Reject match result (opponent). Resets match to pending.
    rejected_by_player_id must match X-Player-Id (caller identity).
    """
    rejected_by = body.rejected_by_player_id
    if not rejected_by:
        raise HTTPException(status_code=422, detail="rejected_by_player_id required")
    if current_player_id != rejected_by:
        raise HTTPException(status_code=403, detail="Access denied: rejected_by_player_id must be the current player")
    r = supabase.table("matches").select("*").eq("id", match_id).execute()
    if not r.data or len(r.data) == 0:
        raise HTTPException(status_code=404, detail="Матч не найден или уже обработан.")
    row = r.data[0]
    if row.get("status") != "pending_confirm":
        raise HTTPException(status_code=400, detail="Матч не найден или уже обработан.")
    if rejected_by != row.get("player1_id") and rejected_by != row.get("player2_id"):
        raise HTTPException(status_code=403, detail="Вы не участник этого матча.")
    if rejected_by == row.get("submitted_by"):
        raise HTTPException(status_code=400, detail="Отклонить может только соперник.")
    supabase.table("matches").update({
        "status": "pending",
        "sets_player1": 0,
        "sets_player2": 0,
        "submitted_by": None,
        "notification_sent_at": None,
    }).eq("id", match_id).execute()
    return {"ok": True}


@router.post("/admin/divisions/{division_id}/recalc-standings")
def admin_recalc_standings(
    division_id: str,
    supabase=Depends(get_supabase),
    current_player_id=Depends(require_current_player_id),
):
    """
    Админ-эндпоинт для пересборки totals в division_players по таблице matches.
    Защищён через API key (optional_api_key) и X-Player-Id; требует авторизованного игрока.
    """
    _recalc_division_standings(supabase, division_id)
    return {"ok": True}
