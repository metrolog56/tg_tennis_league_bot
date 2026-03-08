"""
Validate Telegram Web App initData (HMAC-SHA256) per
https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
import hmac
import hashlib
import json
import logging
from typing import Any, Optional
from urllib.parse import parse_qsl

logger = logging.getLogger(__name__)

# Reject initData older than this (seconds) to limit replay
AUTH_DATE_MAX_AGE_SECONDS = 24 * 3600  # 24 hours


def validate_init_data(init_data: str, bot_token: str) -> Optional[dict[str, Any]]:
    """
    Validate initData from Telegram.WebApp.initData and return parsed user data.
    Returns dict with at least telegram_id (from user.id), or None if invalid.
    """
    if not init_data or not bot_token:
        return None
    init_data = init_data.strip()
    if not init_data:
        return None

    try:
        pairs = parse_qsl(init_data, keep_blank_values=True)
    except Exception as e:
        logger.debug("initData parse_qsl failed: %s", e)
        return None

    params = dict(pairs)
    received_hash = params.get("hash")
    if not received_hash:
        return None

    # data_check_string: all keys except hash, sorted, key=value joined by \n
    data_check_parts = []
    for key in sorted(params.keys()):
        if key == "hash":
            continue
        data_check_parts.append(f"{key}={params[key]}")
    data_check_string = "\n".join(data_check_parts)

    # secret_key = HMAC_SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        logger.warning("initData hash mismatch")
        return None

    # auth_date: reject too old (replay)
    auth_date_str = params.get("auth_date")
    if auth_date_str:
        try:
            auth_date = int(auth_date_str)
            import time
            if auth_date < (int(time.time()) - AUTH_DATE_MAX_AGE_SECONDS):
                logger.warning("initData auth_date too old")
                return None
        except (ValueError, TypeError):
            return None

    # Parse user (JSON)
    user_json = params.get("user")
    if not user_json:
        return None
    try:
        user = json.loads(user_json)
    except json.JSONDecodeError:
        return None
    if not isinstance(user, dict):
        return None
    telegram_id = user.get("id")
    if telegram_id is None:
        return None
    try:
        telegram_id = int(telegram_id)
    except (TypeError, ValueError):
        return None

    return {
        "telegram_id": telegram_id,
        "user": user,
    }
