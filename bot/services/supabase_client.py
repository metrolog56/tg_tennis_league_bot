"""
Клиент Supabase для бота.
Инициализация из SUPABASE_URL и SUPABASE_KEY.
"""
import logging
import os
from typing import Optional
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

logger = logging.getLogger(__name__)
_client: Optional[Client] = None


def _get_client() -> Client:
    global _client
    if _client is not None:
        return _client
    url = (os.getenv("SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_KEY") or "").strip()
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")
    # Диагностика без вывода ключа: JWT обычно начинается с eyJ, длина сотни символов
    logger.info(
        "Supabase: key length=%d, looks_like_jwt=%s",
        len(key),
        key.startswith("eyJ") if key else False,
    )
    _client = create_client(url, key, options=ClientOptions(postgrest_client_timeout=30))
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
        r = _get_client().table("players").insert(row).execute()
        if r.data and len(r.data) > 0:
            return r.data[0]
        return None
    except Exception as e:
        logger.exception("create_player failed: %s", e)
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


def submit_match_for_confirmation(
    division_id: str,
    player1_id: str,
    player2_id: str,
    sets_player1: int,
    sets_player2: int,
    submitted_by_id: str,
) -> tuple[Optional[str], Optional[str]]:
    """
    Сохранить результат матча со статусом pending_confirm (без пересчёта рейтинга).
    Возвращает (match_id, None) при успехе или (None, error_message) при ошибке.
    """
    try:
        client = _get_client()
        existing = get_existing_match(division_id, player1_id, player2_id)
        if existing and existing.get("status") == "played":
            return None, "Этот матч уже внесён и подтверждён."
        now_iso = datetime.now(timezone.utc).isoformat()
        if existing:
            match_id = existing["id"]
            client.table("matches").update({
                "sets_player1": sets_player1,
                "sets_player2": sets_player2,
                "status": "pending_confirm",
                "submitted_by": submitted_by_id,
                "played_at": now_iso,
                "notification_sent_at": None,
            }).eq("id", match_id).execute()
        else:
            ins = client.table("matches").insert({
                "division_id": division_id,
                "player1_id": player1_id,
                "player2_id": player2_id,
                "sets_player1": sets_player1,
                "sets_player2": sets_player2,
                "status": "pending_confirm",
                "submitted_by": submitted_by_id,
                "played_at": now_iso,
            }).execute()
            match_id = ins.data[0]["id"] if ins.data else None
            if not match_id:
                return None, "Не удалось создать матч."
        return match_id, None
    except Exception as e:
        return None, str(e)


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
