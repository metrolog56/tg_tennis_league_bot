from fastapi import APIRouter, Depends

from api.dependencies import get_supabase

router = APIRouter(prefix="/seasons", tags=["seasons"])


@router.get("/current")
def get_current_season(supabase=Depends(get_supabase)):
    """Active season (single)."""
    r = (
        supabase.table("seasons")
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


@router.get("/{season_id}/divisions")
def get_divisions_by_season(
    season_id: str,
    supabase=Depends(get_supabase),
):
    """All divisions of a season, ordered by number."""
    r = (
        supabase.table("divisions")
        .select("id, number, season_id")
        .eq("season_id", season_id)
        .order("number", ascending=True)
        .execute()
    )
    return r.data or []
