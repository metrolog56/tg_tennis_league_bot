"""
Tests for POST /auth/telegram (exchange initData for JWT).
"""
from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture
def mock_validate_ok():
    with patch("api.routers.auth.validate_init_data") as m:
        m.return_value = {"telegram_id": 123, "user": {"id": 123}}
        yield m


@pytest.fixture
def mock_validate_fail():
    with patch("api.routers.auth.validate_init_data") as m:
        m.return_value = None
        yield m


@pytest.fixture
def env_auth():
    with patch.dict("os.environ", {
        "TELEGRAM_BOT_TOKEN": "test-bot-token",
        "JWT_SECRET": "test-jwt-secret-at-least-32-characters-long",
    }, clear=False):
        yield


def test_auth_telegram_401_without_init_data(client):
    r = client.post("/auth/telegram", json={"init_data": ""})
    assert r.status_code == 401
    assert "required" in (r.json() or {}).get("detail", "").lower() or "init_data" in (r.json() or {}).get("detail", "").lower()


def test_auth_telegram_401_invalid_init_data(client, mock_validate_fail, env_auth):
    r = client.post("/auth/telegram", json={"init_data": "invalid-or-tampered"})
    assert r.status_code == 401
    assert "invalid" in (r.json() or {}).get("detail", "").lower() or "expired" in (r.json() or {}).get("detail", "").lower()


def test_auth_telegram_200_returns_token_and_player_id(client, mock_validate_ok, env_auth):
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
    with patch("api.routers.auth.get_supabase", return_value=mock_supabase):
        r = client.post("/auth/telegram", json={"init_data": "auth_date=1&user=%7B%22id%22%3A123%7D&hash=abc"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("access_token")
    assert data.get("token_type") == "bearer"
    assert data.get("telegram_id") == 123
    assert data.get("player_id") is None  # no player in DB from mock
