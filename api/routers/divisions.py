from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_supabase, optional_api_key

router = APIRouter(
    prefix="/divisions",
    tags=["divisions"],
    dependencies=[Depends(optional_api_key)],
)


@router.get("/{division_id}")
def get_division_by_id(
    division_id: str,
    supabase=Depends(get_supabase),
):
    """Division by id with season."""
    r = (
        supabase.table("divisions")
        .select("*, season:seasons(*)")
        .eq("id", division_id)
        .execute()
    )
    if r.data and len(r.data) > 0:
        return r.data[0]
    raise HTTPException(status_code=404, detail="Division not found")


@router.get("/{division_id}/standings")
def get_division_standings(
    division_id: str,
    supabase=Depends(get_supabase),
):
    """Division standings (division_players with player, ordered by position/points)."""
    r = (
        supabase.table("division_players")
        .select(
            "id, position, total_points, total_sets_won, total_sets_lost, rating_delta, "
            "player:players(id, name, rating, telegram_id)"
        )
        .eq("division_id", division_id)
        .order("position", ascending=True, nulls_first=False)
        .execute()
    )
    rows = r.data or []
    if rows and all(r.get("position") is not None for r in rows):
        rows.sort(
            key=lambda x: (
                -(x.get("total_points") or 0),
                -((x.get("total_sets_won") or 0) - (x.get("total_sets_lost") or 0)),
            )
        )
    return rows


@router.get("/{division_id}/matches")
def get_division_matches(
    division_id: str,
    supabase=Depends(get_supabase),
):
    """Matches and players list for division (for matrix view)."""
    r_m = (
        supabase.table("matches")
        .select("id, player1_id, player2_id, sets_player1, sets_player2, status, submitted_by")
        .eq("division_id", division_id)
        .execute()
    )
    r_dp = (
        supabase.table("division_players")
        .select("player_id, player:players(id, name)")
        .eq("division_id", division_id)
        .execute()
    )
    matches = r_m.data or []
    standings = r_dp.data or []
    players = [s.get("player") or {"id": s["player_id"]} for s in standings if s.get("player_id")]
    matrix = {}
    for m in matches:
        k1, k2 = f"{m['player1_id']}-{m['player2_id']}", f"{m['player2_id']}-{m['player1_id']}"
        score = f"{m['sets_player1']}-{m['sets_player2']}" if m.get("status") == "played" else None
        cell = {
            "score": score,
            "status": m.get("status"),
            "matchId": m.get("id"),
            "player1_id": m.get("player1_id"),
            "player2_id": m.get("player2_id"),
            "sets1": m.get("sets_player1"),
            "sets2": m.get("sets_player2"),
            "submitted_by": m.get("submitted_by"),
        }
        matrix[k1] = matrix[k2] = cell
    return {"players": players, "matches": matches, "matrix": matrix}
