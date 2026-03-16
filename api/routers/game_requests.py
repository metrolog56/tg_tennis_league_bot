"""
Game requests: division challenges and open "looking for game" requests.
Requests expire daily at 21:00 Moscow time (UTC+3 = 18:00 UTC).
"""
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from api.dependencies import (
    get_supabase,
    optional_api_key,
    require_current_player_id,
)
from api.limiter import limiter

MOSCOW_TZ = timezone(timedelta(hours=3))

VALID_TYPES = ("division_challenge", "open_league", "open_casual")


def _next_21_moscow() -> datetime:
    """Return the next 21:00 Moscow time as a UTC-aware datetime."""
    now_moscow = datetime.now(MOSCOW_TZ)
    today_21 = now_moscow.replace(hour=21, minute=0, second=0, microsecond=0)
    if now_moscow >= today_21:
        today_21 += timedelta(days=1)
    return today_21.astimezone(timezone.utc)


def _trigger_game_request_notify(request_id: str) -> None:
    url = (os.getenv("BOT_NOTIFY_URL") or "").strip().rstrip("/")
    if not url:
        return
    secret = (os.getenv("NOTIFY_SECRET") or "").strip()
    hdrs = {"X-Notify-Secret": secret} if secret else {}
    try:
        with httpx.Client(timeout=5.0) as client:
            client.post(f"{url}/notify-game-request", json={"request_id": request_id}, headers=hdrs)
    except Exception:
        pass


def _trigger_open_game_request_notify(request_id: str) -> None:
    url = (os.getenv("BOT_NOTIFY_URL") or "").strip().rstrip("/")
    if not url:
        return
    secret = (os.getenv("NOTIFY_SECRET") or "").strip()
    hdrs = {"X-Notify-Secret": secret} if secret else {}
    try:
        with httpx.Client(timeout=5.0) as client:
            client.post(f"{url}/notify-open-game-request", json={"request_id": request_id}, headers=hdrs)
    except Exception:
        pass


def _trigger_game_request_accepted_notify(request_id: str) -> None:
    url = (os.getenv("BOT_NOTIFY_URL") or "").strip().rstrip("/")
    if not url:
        return
    secret = (os.getenv("NOTIFY_SECRET") or "").strip()
    hdrs = {"X-Notify-Secret": secret} if secret else {}
    try:
        with httpx.Client(timeout=5.0) as client:
            client.post(f"{url}/notify-game-request-accepted", json={"request_id": request_id}, headers=hdrs)
    except Exception:
        pass


router = APIRouter(
    prefix="/game-requests",
    tags=["game-requests"],
    dependencies=[Depends(optional_api_key)],
)


class CreateGameRequestBody(BaseModel):
    type: str
    target_player_id: Optional[str] = None
    message: Optional[str] = None
    season_id: Optional[str] = None


@router.post("")
@limiter.limit("20/minute")
def create_game_request(
    request: Request,
    body: CreateGameRequestBody,
    supabase=Depends(get_supabase),
    current_player_id=Depends(require_current_player_id),
):
    """Create a game request. division_challenge requires target_player_id."""
    if body.type not in VALID_TYPES:
        raise HTTPException(status_code=422, detail=f"type must be one of {list(VALID_TYPES)}")

    if body.type == "division_challenge" and not body.target_player_id:
        raise HTTPException(status_code=422, detail="target_player_id required for division_challenge")

    if body.target_player_id and body.target_player_id == current_player_id:
        raise HTTPException(status_code=400, detail="Нельзя отправить вызов самому себе")

    now_utc = datetime.now(timezone.utc).isoformat()

    if body.type == "division_challenge":
        existing = (
            supabase.table("game_requests")
            .select("id")
            .eq("requester_id", current_player_id)
            .eq("target_player_id", body.target_player_id)
            .eq("type", "division_challenge")
            .eq("status", "pending")
            .gt("expires_at", now_utc)
            .execute()
        )
        if existing.data:
            raise HTTPException(status_code=400, detail="Вы уже отправили вызов этому игроку")
    else:
        existing = (
            supabase.table("game_requests")
            .select("id")
            .eq("requester_id", current_player_id)
            .in_("type", ["open_league", "open_casual"])
            .eq("status", "pending")
            .gt("expires_at", now_utc)
            .execute()
        )
        if existing.data:
            raise HTTPException(status_code=400, detail="У вас уже есть активный открытый запрос")

    expires_at = _next_21_moscow()
    msg = (body.message or "").strip() or None
    if msg and len(msg) > 100:
        msg = msg[:100]

    payload = {
        "requester_id": current_player_id,
        "target_player_id": body.target_player_id,
        "type": body.type,
        "message": msg,
        "status": "pending",
        "season_id": body.season_id,
        "expires_at": expires_at.isoformat(),
    }
    r = supabase.table("game_requests").insert(payload).select().execute()
    if not r.data:
        raise HTTPException(status_code=500, detail="Не удалось создать запрос")

    row = r.data[0]
    if body.type == "division_challenge" and body.target_player_id:
        _trigger_game_request_notify(row["id"])
    elif body.type in ("open_league", "open_casual"):
        _trigger_open_game_request_notify(row["id"])
    return row


@router.get("")
def list_game_requests(
    season_id: Optional[str] = None,
    supabase=Depends(get_supabase),
    current_player_id=Depends(require_current_player_id),
):
    """
    Returns:
    - open: active open requests from other players (for the feed)
    - challenges: incoming division challenges addressed to current player
    - mine: current player's own active requests
    """
    now_utc = datetime.now(timezone.utc).isoformat()

    open_q = (
        supabase.table("game_requests")
        .select("id, requester_id, type, message, created_at, expires_at, requester:players!requester_id(id, name)")
        .in_("type", ["open_league", "open_casual"])
        .eq("status", "pending")
        .gt("expires_at", now_utc)
        .neq("requester_id", current_player_id)
    )
    if season_id:
        open_q = open_q.eq("season_id", season_id)
    open_r = open_q.order("created_at", desc=False).execute()

    challenge_r = (
        supabase.table("game_requests")
        .select("id, requester_id, type, message, created_at, expires_at, requester:players!requester_id(id, name)")
        .eq("type", "division_challenge")
        .eq("target_player_id", current_player_id)
        .eq("status", "pending")
        .gt("expires_at", now_utc)
        .order("created_at", desc=False)
        .execute()
    )

    mine_r = (
        supabase.table("game_requests")
        .select("id, requester_id, type, message, created_at, expires_at, target_player_id, target:players!target_player_id(id, name)")
        .eq("requester_id", current_player_id)
        .eq("status", "pending")
        .gt("expires_at", now_utc)
        .order("created_at", desc=False)
        .execute()
    )

    return {
        "open": open_r.data or [],
        "challenges": challenge_r.data or [],
        "mine": mine_r.data or [],
    }


@router.post("/{request_id}/accept")
@limiter.limit("20/minute")
def accept_game_request(
    request: Request,
    request_id: str,
    supabase=Depends(get_supabase),
    current_player_id=Depends(require_current_player_id),
):
    """Accept a game request. Only the target (for division_challenge) or any other player (for open) may accept."""
    now_utc = datetime.now(timezone.utc).isoformat()

    r = supabase.table("game_requests").select("*").eq("id", request_id).execute()
    if not r.data:
        raise HTTPException(status_code=404, detail="Запрос не найден")
    row = r.data[0]

    if row["requester_id"] == current_player_id:
        raise HTTPException(status_code=400, detail="Нельзя принять собственный запрос")
    if row["status"] != "pending":
        raise HTTPException(status_code=400, detail="Запрос уже неактивен")
    if row["expires_at"] <= now_utc:
        raise HTTPException(status_code=400, detail="Срок запроса истёк")

    if row["type"] == "division_challenge":
        if row.get("target_player_id") != current_player_id:
            raise HTTPException(status_code=403, detail="Этот вызов адресован другому игроку")

    upd = (
        supabase.table("game_requests")
        .update({"status": "accepted", "accepted_by_id": current_player_id})
        .eq("id", request_id)
        .eq("status", "pending")
        .select()
        .execute()
    )
    if not upd.data:
        raise HTTPException(status_code=400, detail="Запрос уже был принят другим игроком")

    _trigger_game_request_accepted_notify(request_id)
    return upd.data[0]


@router.post("/{request_id}/cancel")
@limiter.limit("20/minute")
def cancel_game_request(
    request: Request,
    request_id: str,
    supabase=Depends(get_supabase),
    current_player_id=Depends(require_current_player_id),
):
    """Cancel own request or decline an incoming division challenge."""
    r = (
        supabase.table("game_requests")
        .select("id, requester_id, target_player_id, status, type")
        .eq("id", request_id)
        .execute()
    )
    if not r.data:
        raise HTTPException(status_code=404, detail="Запрос не найден")
    row = r.data[0]

    is_requester = row["requester_id"] == current_player_id
    is_target = (
        row.get("type") == "division_challenge"
        and row.get("target_player_id") == current_player_id
    )
    if not is_requester and not is_target:
        raise HTTPException(status_code=403, detail="Нет доступа к этому запросу")

    if row["status"] != "pending":
        raise HTTPException(status_code=400, detail="Запрос уже неактивен")

    supabase.table("game_requests").update({"status": "cancelled"}).eq("id", request_id).execute()
    return {"ok": True}
