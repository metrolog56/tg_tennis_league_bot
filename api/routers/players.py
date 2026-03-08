from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.dependencies import (
    get_current_player_id,
    get_supabase,
    optional_api_key,
    require_current_player_id,
    _log_access_denied,
)

router = APIRouter(
    prefix="/players",
    tags=["players"],
    dependencies=[Depends(optional_api_key)],
)


class UpdatePlayerName(BaseModel):
    name: str


@router.get("")
def get_player_by_telegram_id(
    telegram_id: Optional[int] = Query(None, description="Telegram user ID"),
    supabase=Depends(get_supabase),
    current_player_id=Depends(get_current_player_id),
):
    """Get player by telegram_id. Returns single player or null.
    When telegram_id is provided: only returns the player if it is the current caller's player (X-Player-Id).
    """
    if telegram_id is None:
        return None
    if current_player_id is None:
        _log_access_denied("GET /players?telegram_id=...", "X-Player-Id required when querying by telegram_id")
        raise HTTPException(status_code=403, detail="X-Player-Id required to request player by telegram_id")
    r = supabase.table("players").select("*").eq("telegram_id", telegram_id).execute()
    if not r.data or len(r.data) == 0:
        return None
    player = r.data[0]
    if player.get("id") != current_player_id:
        _log_access_denied("GET /players", "player_id does not match X-Player-Id")
        raise HTTPException(status_code=403, detail="Access denied: only your own player can be requested by telegram_id")
    return player


@router.get("/rating")
def get_rating_top(
    limit: int = Query(50, ge=1, le=100),
    supabase=Depends(get_supabase),
):
    """Top players by rating. Uses player_stats view if available (games, wins)."""
    try:
        r = (
            supabase.table("player_stats")
            .select("id, name, rating, telegram_id, games, wins")
            .order("rating", desc=True)
            .limit(limit)
            .execute()
        )
        if r.data is not None:
            return r.data
    except Exception:
        pass
    r = (
        supabase.table("players")
        .select("id, name, rating, telegram_id")
        .order("rating", desc=True)
        .limit(limit)
        .execute()
    )
    rows = r.data or []
    return [{"games": None, "wins": None, **p} for p in rows]


@router.patch("/{player_id}")
def update_player_name(
    player_id: str,
    body: UpdatePlayerName,
    supabase=Depends(get_supabase),
    current_player_id=Depends(require_current_player_id),
):
    """Update player name. Caller may only update their own player (X-Player-Id must match player_id)."""
    if current_player_id != player_id:
        _log_access_denied("PATCH /players/{player_id}", "player_id does not match X-Player-Id")
        raise HTTPException(status_code=403, detail="Access denied: you can only update your own player")
    name = (body.name or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="Имя не может быть пустым")
    r = (
        supabase.table("players")
        .update({"name": name})
        .eq("id", player_id)
        .select("id, name, rating, telegram_id")
        .execute()
    )
    if r.data and len(r.data) > 0:
        return r.data[0]
    raise HTTPException(status_code=404, detail="Player not found")
