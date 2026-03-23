"""
Tests for POST /auth/telegram (exchange initData for JWT).
"""
import sys
from unittest.mock import patch, MagicMock
from types import SimpleNamespace

import pytest


def _headers():
    return {"X-API-Key": "secret123"}


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
        "API_KEY": "secret123",
    }, clear=False):
        yield


def test_auth_telegram_401_without_init_data(client, env_auth):
    r = client.post("/auth/telegram", json={"init_data": ""}, headers=_headers())
    assert r.status_code == 401
    assert "required" in (r.json() or {}).get("detail", "").lower() or "init_data" in (r.json() or {}).get("detail", "").lower()


def test_auth_telegram_401_invalid_init_data(client, mock_validate_fail, env_auth):
    r = client.post("/auth/telegram", json={"init_data": "invalid-or-tampered"}, headers=_headers())
    assert r.status_code == 401
    assert "invalid" in (r.json() or {}).get("detail", "").lower() or "expired" in (r.json() or {}).get("detail", "").lower()


def test_auth_telegram_200_returns_token_and_player_id(client, mock_validate_ok, env_auth):
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
    with patch("api.routers.auth.get_supabase", return_value=mock_supabase):
        r = client.post("/auth/telegram", json={"init_data": "auth_date=1&user=%7B%22id%22%3A123%7D&hash=abc"}, headers=_headers())
    assert r.status_code == 200
    data = r.json()
    assert data.get("access_token")
    assert data.get("token_type") == "bearer"
    assert data.get("auth_type") == "telegram"
    assert data.get("telegram_id") == 123
    assert data.get("player_id") is None  # no player in DB from mock


def test_auth_web_401_without_access_token(client, env_auth):
    r = client.post("/auth/web", json={"access_token": ""}, headers=_headers())
    assert r.status_code == 401
    assert "required" in (r.json() or {}).get("detail", "").lower()


def test_auth_web_200_returns_token_and_player_id(client, env_auth):
    mock_supabase = MagicMock()
    mock_user = SimpleNamespace(
        id="11111111-1111-1111-1111-111111111111",
        email="player@example.com",
    )
    mock_supabase.auth.get_user.return_value = SimpleNamespace(user=mock_user)
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "22222222-2222-2222-2222-222222222222"}]
    )
    for key in list(sys.modules.keys()):
        if key == "api.main" or key == "api.routers" or key.startswith("api.routers."):
            del sys.modules[key]
    with patch("api.dependencies.get_supabase", lambda: mock_supabase):
        from fastapi.testclient import TestClient
        from api.main import app
        tc = TestClient(app)
        r = tc.post("/auth/web", json={"access_token": "supabase-access-token"}, headers=_headers())
    assert r.status_code == 200
    data = r.json()
    assert data.get("access_token")
    assert data.get("token_type") == "bearer"
    assert data.get("auth_type") == "web"
    assert data.get("auth_user_id") == "11111111-1111-1111-1111-111111111111"
    assert data.get("player_id") == "22222222-2222-2222-2222-222222222222"
