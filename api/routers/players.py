from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.dependencies import get_supabase

router = APIRouter(prefix="/players", tags=["players"])


class UpdatePlayerName(BaseModel):
    name: str


@router.get("")
def get_player_by_telegram_id(
    telegram_id: Optional[int] = Query(None, description="Telegram user ID"),
    supabase=Depends(get_supabase),
):
    """Get player by telegram_id. Returns single player or null."""
    if telegram_id is None:
        return None
    r = supabase.table("players").select("*").eq("telegram_id", telegram_id).execute()
    if r.data and len(r.data) > 0:
        return r.data[0]
    return None


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
):
    """Update player name."""
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
