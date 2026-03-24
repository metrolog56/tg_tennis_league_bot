"""
Auth: exchange Telegram Web App initData for JWT (validated on server).
"""
import os
import time
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from api.dependencies import get_supabase, optional_api_key
from api.limiter import limiter
from api.telegram_auth import validate_init_data

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    dependencies=[Depends(optional_api_key)],
)


class TelegramAuthBody(BaseModel):
    init_data: str


class WebAuthBody(BaseModel):
    access_token: str


def _get_bot_token() -> str:
    token = (os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN") or "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN or BOT_TOKEN must be set for /auth/telegram")
    return token


def _get_jwt_secret() -> str:
    secret = (os.getenv("JWT_SECRET") or "").strip()
    if not secret:
        raise RuntimeError("JWT_SECRET must be set for /auth/telegram")
    return secret


@router.post("/telegram")
@limiter.limit("10/minute")
def auth_telegram(
    request: Request,
    body: TelegramAuthBody,
    supabase=Depends(get_supabase),
):
    """
    Exchange Telegram Web App initData for a JWT.
    Validates initData signature (HMAC-SHA256) and returns access_token + player_id.
    """
    if not (body.init_data or "").strip():
        raise HTTPException(status_code=401, detail="init_data required")

    try:
        bot_token = _get_bot_token()
        jwt_secret = _get_jwt_secret()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Auth not configured") from e

    payload = validate_init_data(body.init_data.strip(), bot_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired initData")

    telegram_id = payload["telegram_id"]

    # Resolve player_id from DB
    r = supabase.table("players").select("id").eq("telegram_id", telegram_id).execute()
    player_id = None
    if r.data and len(r.data) > 0:
        player_id = r.data[0].get("id")

    exp_seconds = int(os.getenv("JWT_EXPIRATION_SECONDS", "604800"))  # 7 days
    now = int(time.time())
    jwt_payload = {
        "sub": str(telegram_id),
        "telegram_id": telegram_id,
        "player_id": player_id,
        "iat": now,
        "exp": now + exp_seconds,
    }
    access_token = jwt.encode(
        jwt_payload,
        jwt_secret,
        algorithm="HS256",
    )
    if hasattr(access_token, "decode"):
        access_token = access_token.decode("utf-8")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "auth_type": "telegram",
        "player_id": player_id,
        "telegram_id": telegram_id,
        "auth_user_id": None,
    }


@router.post("/web")
@limiter.limit("10/minute")
def auth_web(
    request: Request,
    body: WebAuthBody,
    supabase=Depends(get_supabase),
):
    """
    Exchange Supabase access token for API JWT (web-first mode).
    Creates player row if no linked player exists yet.
    """
    raw_token = (body.access_token or "").strip()
    if not raw_token:
        raise HTTPException(status_code=401, detail="access_token required")

    try:
        jwt_secret = _get_jwt_secret()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Auth not configured") from e

    try:
        user_resp = supabase.auth.get_user(raw_token)
        user = getattr(user_resp, "user", None)
        if not user:
            raise ValueError("empty user")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid web access token") from e

    auth_user_id = str(getattr(user, "id", "") or "").strip()
    if not auth_user_id:
        raise HTTPException(status_code=401, detail="Invalid web user id")
    raw_email = getattr(user, "email", "")
    email = raw_email.strip() if isinstance(raw_email, str) else None
    display_name = (email.split("@")[0] if email else "Новый игрок").strip()[:255] or "Новый игрок"

    player_id = None
    r = supabase.table("players").select("id").eq("auth_user_id", auth_user_id).execute()
    if r.data and len(r.data) > 0:
        player_id = r.data[0].get("id")
    else:
        created = (
            supabase.table("players")
            .insert({
                "auth_user_id": auth_user_id,
                "email": email,
                "name": display_name,
                "rating": 100.0,
                "is_active": True,
            })
            .select("id")
            .execute()
        )
        if created.data and len(created.data) > 0:
            player_id = created.data[0].get("id")

    exp_seconds = int(os.getenv("JWT_EXPIRATION_SECONDS", "604800"))
    now = int(time.time())
    jwt_payload = {
        "sub": auth_user_id,
        "auth_type": "web",
        "auth_user_id": auth_user_id,
        "email": email,
        "player_id": player_id,
        "iat": now,
        "exp": now + exp_seconds,
    }
    access_token = jwt.encode(jwt_payload, jwt_secret, algorithm="HS256")
    if hasattr(access_token, "decode"):
        access_token = access_token.decode("utf-8")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "auth_type": "web",
        "player_id": player_id,
        "telegram_id": None,
        "auth_user_id": auth_user_id,
        "email": email,
    }
