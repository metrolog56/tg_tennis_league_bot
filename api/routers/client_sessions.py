"""
Client sessions (analytics): insert via API so anon key does not need write access.
"""
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.dependencies import get_current_player_id, get_supabase, optional_api_key

router = APIRouter(
    prefix="/client-sessions",
    tags=["client-sessions"],
    dependencies=[Depends(optional_api_key)],
)


class ClientSessionBody(BaseModel):
    device_type: Optional[str] = None
    browser: Optional[str] = None
    browser_version: Optional[str] = None
    resolution: Optional[str] = None
    language: Optional[str] = None
    platform: Optional[str] = None
    player_id: Optional[str] = None


@router.post("")
def create_client_session(
    body: ClientSessionBody,
    supabase=Depends(get_supabase),
    current_player_id=Depends(get_current_player_id),
):
    """Record a client session (analytics). Uses authenticated player_id from Bearer token only."""
    row = {
        "device_type": body.device_type,
        "browser": body.browser,
        "browser_version": body.browser_version,
        "resolution": body.resolution,
        "language": body.language,
        "platform": body.platform,
        "player_id": current_player_id,
    }
    r = supabase.table("client_sessions").insert(row).select("id").execute()
    if r.data and len(r.data) > 0:
        return {"id": r.data[0]["id"]}
    return {}
