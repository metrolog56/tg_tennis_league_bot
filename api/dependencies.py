"""
FastAPI dependencies: Supabase client, optional API key, current player (IDOR protection).
"""
import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import Depends, Header, HTTPException
from fastapi.security import APIKeyHeader
from supabase import Client, create_client

logger = logging.getLogger(__name__)

# Security scheme for OpenAPI/Swagger: enables "Authorize" and X-API-Key in /docs
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False, scheme_name="ApiKey")
# Identity of the caller for access control: only this player's resources may be accessed
player_id_header = "X-Player-Id"

# Load .env from api/ or project root
_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)

_client: Optional[Client] = None


def get_supabase() -> Client:
    global _client
    if _client is not None:
        return _client
    url = (os.getenv("SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_KEY") or "").strip()
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")
    _client = create_client(url, key)
    return _client


def optional_api_key(x_api_key: Optional[str] = Depends(api_key_header)) -> None:
    """If API_KEY is set in env, require X-API-Key header to match."""
    api_key = (os.getenv("API_KEY") or "").strip()
    if not api_key:
        return
    if not x_api_key or x_api_key != api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def get_current_player_id(
    x_player_id: Optional[str] = Header(None, alias=player_id_header),
) -> Optional[str]:
    """Return current player ID from X-Player-Id header, or None if not sent."""
    s = (x_player_id or "").strip()
    return s if s else None


def require_current_player_id(
    current: Optional[str] = Depends(get_current_player_id),
) -> str:
    """Require X-Player-Id for endpoints that must know the actor (access control)."""
    if not current:
        logger.warning("Access denied: missing X-Player-Id (endpoint requires caller identity)")
        raise HTTPException(
            status_code=403,
            detail="X-Player-Id required for this action",
        )
    return current


def _log_access_denied(endpoint: str, reason: str) -> None:
    """Log 403 access denial (OWASP: minimal context, no secrets)."""
    logger.warning("Access denied: endpoint=%s reason=%s", endpoint, reason)
