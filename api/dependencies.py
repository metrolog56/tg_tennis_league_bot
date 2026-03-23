"""
FastAPI dependencies: Supabase client, optional API key, current player (IDOR protection).
Supports Bearer JWT (telegram/web auth).
"""
import os
from pathlib import Path
from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException
from fastapi.security import APIKeyHeader
from supabase import Client, create_client

# Security scheme for OpenAPI/Swagger: enables "Authorize" and X-API-Key in /docs
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False, scheme_name="ApiKey")
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


def _player_id_from_bearer(authorization: Optional[str]) -> Optional[str]:
    """Extract and verify Bearer JWT; return player_id from payload or None."""
    if not authorization or not isinstance(authorization, str):
        return None
    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1]
    secret = (os.getenv("JWT_SECRET") or "").strip()
    if not secret:
        return None
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        pid = payload.get("player_id")
        return str(pid) if pid is not None else None
    except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
        return None


def get_current_player_id(
    authorization: Optional[str] = Header(None),
) -> Optional[str]:
    """Return current player ID from Bearer JWT."""
    return _player_id_from_bearer(authorization)


def require_current_player_id(
    current: Optional[str] = Depends(get_current_player_id),
) -> str:
    """Require Bearer token identity for endpoints that need authenticated actor."""
    if not current:
        raise HTTPException(
            status_code=401,
            detail="Authorization Bearer token required for this action",
        )
    return current
