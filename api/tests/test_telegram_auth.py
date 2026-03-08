"""
Tests for Telegram initData validation (api.telegram_auth).
"""
import time

import pytest

from api.telegram_auth import validate_init_data


def test_validate_init_data_empty_returns_none():
    assert validate_init_data("", "token") is None
    assert validate_init_data("   ", "token") is None
    assert validate_init_data("auth_date=123", "token") is None  # no hash


def test_validate_init_data_invalid_hash_returns_none():
    init_data = "auth_date=123\nuser=%7B%22id%22%3A456%7D&hash=invalid"
    assert validate_init_data(init_data, "bot_token_here") is None


def test_validate_init_data_valid_returns_payload():
    """Build valid initData with known bot_token and assert we get telegram_id."""
    bot_token = "test_bot_token_123"
    auth_date = str(int(time.time()))  # current time so not expired
    user_json = '{"id": 789, "first_name": "Test"}'
    from urllib.parse import quote
    user_encoded = quote(user_json, safe="")

    params = {"auth_date": auth_date, "user": user_json}
    data_check_parts = [f"{k}={params[k]}" for k in sorted(params.keys())]
    data_check_string = "\n".join(data_check_parts)

    import hmac
    import hashlib
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

    init_data = f"auth_date={auth_date}&user={user_encoded}&hash={computed_hash}"
    result = validate_init_data(init_data, bot_token)
    assert result is not None
    assert result["telegram_id"] == 789
    assert result.get("user", {}).get("id") == 789


def test_validate_init_data_no_bot_token_returns_none():
    assert validate_init_data("auth_date=1&hash=ab", "") is None
