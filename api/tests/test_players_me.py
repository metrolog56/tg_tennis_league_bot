import sys
from typing import Optional
from unittest.mock import MagicMock, patch

import jwt


PLAYER_A = "00000000-0000-0000-0000-000000000001"


def _auth_headers(api_key: str = "secret123", player_id: Optional[str] = None):
    h = {"X-API-Key": api_key}
    if player_id:
        h["Authorization"] = f"Bearer {jwt.encode({'player_id': player_id}, 'test-jwt-secret-at-least-32-characters-long', algorithm='HS256')}"
    return h


def test_players_me_requires_identity(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-at-least-32-characters-long")
    r = client.get("/players/me", headers=_auth_headers())
    assert r.status_code == 401


def test_players_me_returns_current_player(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-at-least-32-characters-long")
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": PLAYER_A, "name": "Player A", "telegram_id": None}]
    )
    for key in list(sys.modules.keys()):
        if key == "api.main" or key == "api.routers" or key.startswith("api.routers."):
            del sys.modules[key]
    with patch("api.dependencies.get_supabase", lambda: mock_supabase):
        from fastapi.testclient import TestClient
        from api.main import app
        tc = TestClient(app)
        r = tc.get("/players/me", headers=_auth_headers(player_id=PLAYER_A))
    assert r.status_code == 200
    assert (r.json() or {}).get("id") == PLAYER_A
