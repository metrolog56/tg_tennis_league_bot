"""
FastAPI dependencies: Supabase client and optional API key.
"""
import os
from pathlib import Path
from typing import Optional

from fastapi import Depends, HTTPException
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
