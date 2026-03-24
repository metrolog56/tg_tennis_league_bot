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
        "player_id": player_id,
        "telegram_id": telegram_id,
    }
