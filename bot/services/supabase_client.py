"""
Клиент Supabase для бота.
Инициализация из SUPABASE_URL и SUPABASE_KEY.
"""
import os
from datetime import datetime, timezone
from typing import Optional
from supabase import create_client, Client

_client: Optional[Client] = None


def _get_client() -> Client:
    global _client
    if _client is not None:
        return _client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")
    _client = create_client(url, key)
    return _client


def get_supabase_client() -> Optional[Client]:
    """Опциональный клиент (возвращает None если нет переменных окружения)."""
    try:
        return _get_client()
    except RuntimeError:
        return None


def get_player_by_telegram_id(telegram_id: int) -> Optional[dict]:
    """Найти игрока по telegram_id."""
    try:
        r = _get_client().table("players").select("*").eq("telegram_id", telegram_id).execute()
        if r.data and len(r.data) > 0:
            return r.data[0]
        return None
    except Exception:
        return None


def create_player(
    telegram_id: int,
    name: str,
    telegram_username: Optional[str] = None,
    is_admin: bool = False,
) -> Optional[dict]:
    """Создать игрока. Возвращает созданную запись или None при ошибке."""
    try:
        row = {
            "telegram_id": telegram_id,
            "name": name,
            "telegram_username": telegram_username,
        }
        if is_admin:
            row["is_admin"] = True
        r = _get_client().table("players").insert(row).select().execute()
        if r.data and len(r.data) > 0:
            return r.data[0]
        return None
    except Exception:
        return None


def get_active_season() -> Optional[dict]:
    """Получить активный сезон (тур)."""
    try:
        r = (
            _get_client()
            .table("seasons")
            .select("*")
            .eq("status", "active")
            .order("year", desc=True)
            .order("month", desc=True)
            .limit(1)
            .execute()
        )
        if r.data and len(r.data) > 0:
            return r.data[0]
        return None
    except Exception:
        return None


def get_player_division(player_id: str, season_id: Optional[str] = None) -> Optional[dict]:
    """
    Получить дивизион игрока в текущем (или указанном) сезоне.
    Возвращает: { "division": {...}, "season": {...}, "division_players": [...] }
    или None.
    """
    try:
        if not season_id:
            season = get_active_season()
            if not season:
                return None
            season_id = season["id"]

        divs = (
            _get_client()
            .table("divisions")
            .select("id, number, coef, season_id")
            .eq("season_id", season_id)
            .execute()
        )
        if not divs.data:
            return None

        division_ids = [d["id"] for d in divs.data]
        # Найти запись division_players для этого игрока в одном из дивизионов сезона
        for div_id in division_ids:
            dp_r = (
                _get_client()
                .table("division_players")
                .select("*, division:divisions(*), player:players(id, name, rating)")
                .eq("division_id", div_id)
                .eq("player_id", player_id)
                .execute()
            )
            if dp_r.data and len(dp_r.data) > 0:
                # Получить всех участников дивизиона (для списка соперников)
                all_dp = (
                    _get_client()
                    .table("division_players")
                    .select("*, player:players(id, name, telegram_id, telegram_username)")
                    .eq("division_id", div_id)
                    .execute()
                )
                division = dp_r.data[0].get("division") or next(
                    (d for d in divs.data if d["id"] == div_id), None
                )
                if not division:
                    continue
                season_r = (
                    _get_client()
                    .table("seasons")
                    .select("*")
                    .eq("id", division.get("season_id") or season_id)
                    .execute()
                )
                season = season_r.data[0] if season_r.data else None
                return {
                    "division": division,
                    "season": season,
                    "division_players": all_dp.data or [],
                }
        return None
    except Exception:
        return None


def get_division_matches(division_id: str) -> list[dict]:
    """Все матчи дивизиона."""
    try:
        r = (
            _get_client()
            .table("matches")
            .select("*, player1:players!player1_id(id, name), player2:players!player2_id(id, name)")
            .eq("division_id", division_id)
            .execute()
        )
        return r.data or []
    except Exception:
        return []


def get_existing_match(division_id: str, player1_id: str, player2_id: str) -> Optional[dict]:
    """Проверить, есть ли уже матч между двумя игроками в дивизионе (в любом порядке)."""
    try:
        r1 = (
            _get_client()
            .table("matches")
            .select("*")
            .eq("division_id", division_id)
            .eq("player1_id", player1_id)
            .eq("player2_id", player2_id)
            .execute()
        )
        if r1.data and len(r1.data) > 0:
            return r1.data[0]
        r2 = (
            _get_client()
            .table("matches")
            .select("*")
            .eq("division_id", division_id)
            .eq("player1_id", player2_id)
            .eq("player2_id", player1_id)
            .execute()
        )
        if r2.data and len(r2.data) > 0:
            return r2.data[0]
        return None
    except Exception:
        return None


def submit_match_result(
    division_id: str,
    player1_id: str,
    player2_id: str,
    sets_player1: int,
    sets_player2: int,
    submitted_by_id: str,
    division_coef: float,
    season_id: str,
) -> tuple[Optional[dict], Optional[str], dict]:
    """
    Сохранить результат матча, пересчитать рейтинг обоих игроков.
    player1_id / sets_player1 — первый игрок и его сеты, player2_id / sets_player2 — второй.
    Возвращает (match_row, error_message, deltas_by_player_id).
    При ошибке: (None, error_message, {}). При успехе: (match, None, {player_id: delta}).
    """
    from .rating_calculator import calculate_match_rating

    try:
        client = _get_client()
        existing = get_existing_match(division_id, player1_id, player2_id)
        if existing and existing.get("status") == "played":
            return None, "Этот матч уже внесён.", {}

        # Нормализуем порядок: в БД храним player1_id < player2_id по id для единообразия
        # Схема: UNIQUE(division_id, player1_id, player2_id), так что порядок фиксирован
        p1_id, p2_id = player1_id, player2_id
        s1, s2 = sets_player1, sets_player2

        # Получить рейтинги
        pl1 = client.table("players").select("rating").eq("id", p1_id).execute()
        pl2 = client.table("players").select("rating").eq("id", p2_id).execute()
        r1 = float(pl1.data[0]["rating"]) if pl1.data else 100.0
        r2 = float(pl2.data[0]["rating"]) if pl2.data else 100.0

        if s1 > s2:
            winner_id, loser_id = p1_id, p2_id
            winner_sets, loser_sets = s1, s2
            delta_winner, delta_loser = calculate_match_rating(r1, r2, s1, s2, division_coef)
        else:
            winner_id, loser_id = p2_id, p1_id
            winner_sets, loser_sets = s2, s1
            delta_winner, delta_loser = calculate_match_rating(r2, r1, s2, s1, division_coef)

        # Очки: победа 2, поражение 1
        points_winner, points_loser = 2, 1
        # Сеты для обновления division_players
        sets_winner_won, sets_winner_lost = winner_sets, loser_sets
        sets_loser_won, sets_loser_lost = loser_sets, winner_sets

        now_iso = datetime.now(timezone.utc).isoformat()
        if existing:
            match_id = existing["id"]
            client.table("matches").update({
                "sets_player1": s1,
                "sets_player2": s2,
                "status": "played",
                "submitted_by": submitted_by_id,
                "played_at": now_iso,
            }).eq("id", match_id).execute()
        else:
            ins = client.table("matches").insert({
                "division_id": division_id,
                "player1_id": p1_id,
                "player2_id": p2_id,
                "sets_player1": s1,
                "sets_player2": s2,
                "status": "played",
                "submitted_by": submitted_by_id,
                "played_at": now_iso,
            }).select().execute()
            match_id = ins.data[0]["id"] if ins.data else None
            if not match_id:
                return None, "Не удалось создать матч.", {}

        # Обновить рейтинги игроков
        winner_rating_before = r1 if winner_id == p1_id else r2
        loser_rating_before = r2 if loser_id == p2_id else r1
        winner_rating_after = winner_rating_before + delta_winner
        loser_rating_after = loser_rating_before + delta_loser

        client.table("players").update({"rating": round(winner_rating_after, 2)}).eq("id", winner_id).execute()
        client.table("players").update({"rating": round(loser_rating_after, 2)}).eq("id", loser_id).execute()

        # История рейтинга
        client.table("rating_history").insert([
            {
                "player_id": winner_id,
                "match_id": match_id,
                "season_id": season_id,
                "rating_before": winner_rating_before,
                "rating_delta": delta_winner,
                "rating_after": winner_rating_after,
            },
            {
                "player_id": loser_id,
                "match_id": match_id,
                "season_id": season_id,
                "rating_before": loser_rating_before,
                "rating_delta": delta_loser,
                "rating_after": loser_rating_after,
            },
        ]).execute()

        # Обновить очки и сеты в division_players
        for pid, pts, swon, slost in [
            (winner_id, points_winner, sets_winner_won, sets_winner_lost),
            (loser_id, points_loser, sets_loser_won, sets_loser_lost),
        ]:
            dp = (
                client.table("division_players")
                .select("id, total_points, total_sets_won, total_sets_lost, rating_delta")
                .eq("division_id", division_id)
                .eq("player_id", pid)
                .execute()
            )
            if dp.data:
                row = dp.data[0]
                new_pts = (row.get("total_points") or 0) + pts
                new_won = (row.get("total_sets_won") or 0) + swon
                new_lost = (row.get("total_sets_lost") or 0) + slost
                delta_val = delta_winner if pid == winner_id else delta_loser
                new_rating_delta = (row.get("rating_delta") or 0) + delta_val
                client.table("division_players").update({
                    "total_points": new_pts,
                    "total_sets_won": new_won,
                    "total_sets_lost": new_lost,
                    "rating_delta": round(new_rating_delta, 2),
                }).eq("id", row["id"]).execute()

        match_row = (
            client.table("matches").select("*").eq("id", match_id).execute()
        )
        deltas = {winner_id: delta_winner, loser_id: delta_loser}
        return (match_row.data[0] if match_row.data else None), None, deltas
    except Exception as e:
        return None, str(e), {}


def get_rating_top(limit: int = 20) -> list[dict]:
    """Топ игроков по рейтингу."""
    try:
        r = (
            _get_client()
            .table("players")
            .select("id, name, rating, telegram_id")
            .order("rating", desc=True)
            .limit(limit)
            .execute()
        )
        return r.data or []
    except Exception:
        return []
