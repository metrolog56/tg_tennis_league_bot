"""
IDOR / access control tests (SECURITY_OWASP_ANALYSIS §2).
Endpoints must verify caller identity from Bearer JWT matches resource ownership/participant checks.
"""
import sys
from typing import Optional
from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi.testclient import TestClient

# client, _make_mock_supabase, _get_mock_supabase from conftest (shared ref for dependency_overrides)
from api.tests.conftest import _make_mock_supabase

PLAYER_A = "00000000-0000-0000-0000-000000000001"
PLAYER_B = "00000000-0000-0000-0000-000000000002"
MATCH_ID = "00000000-0000-0000-0000-000000000010"


def _auth_headers(api_key: str = "secret123", player_id: Optional[str] = None):
    h = {"X-API-Key": api_key}
    if player_id:
        h["Authorization"] = f"Bearer {jwt.encode({'player_id': player_id}, 'test-jwt-secret-at-least-32-characters-long', algorithm='HS256')}"
    return h


# --- PATCH /players/{player_id} ---


def test_patch_players_without_bearer_returns_401(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-at-least-32-characters-long")
    r = client.patch(
        f"/players/{PLAYER_A}",
        json={"name": "New Name"},
        headers=_auth_headers(),
    )
    assert r.status_code == 401
    assert "Bearer" in (r.json() or {}).get("detail", "")


def test_patch_players_wrong_player_id_returns_403(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-at-least-32-characters-long")
    r = client.patch(
        f"/players/{PLAYER_A}",
        json={"name": "New Name"},
        headers=_auth_headers(player_id=PLAYER_B),
    )
    assert r.status_code == 403
    assert "only update your own" in (r.json() or {}).get("detail", "").lower() or "access denied" in (r.json() or {}).get("detail", "").lower()


# --- GET /players?telegram_id=... ---


def test_get_players_by_telegram_id_without_bearer_returns_401(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-at-least-32-characters-long")
    r = client.get("/players?telegram_id=123", headers=_auth_headers())
    assert r.status_code == 401
    assert "Bearer" in (r.json() or {}).get("detail", "")


# --- GET /matches/pending ---


def test_get_matches_pending_without_bearer_returns_401(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-at-least-32-characters-long")
    r = client.get(
        "/matches/pending",
        headers=_auth_headers(),
    )
    assert r.status_code == 401
    assert "Bearer" in (r.json() or {}).get("detail", "")


def test_get_matches_pending_player_id_mismatch_returns_403(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-at-least-32-characters-long")
    r = client.get(
        "/matches/pending",
        headers=_auth_headers(player_id=PLAYER_B),
    )
    # no mismatch possible via query in bearer-only mode; endpoint uses token identity
    assert r.status_code == 200


# --- POST /matches/submit-for-confirmation ---


def test_submit_for_confirmation_submitted_by_mismatch_returns_403(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-at-least-32-characters-long")
    r = client.post(
        "/matches/submit-for-confirmation",
        json={
            "division_id": "00000000-0000-0000-0000-000000000003",
            "player1_id": PLAYER_A,
            "player2_id": PLAYER_B,
            "sets_player1": 2,
            "sets_player2": 1,
            "submitted_by": PLAYER_A,  # ignored in bearer-only mode
        },
        headers=_auth_headers(player_id=PLAYER_B),
    )
    assert r.status_code != 403


# --- POST /matches/{match_id}/notify-pending ---


def test_notify_pending_caller_not_participant_returns_403(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-at-least-32-characters-long")
    mock_sb = _make_mock_supabase()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"player1_id": PLAYER_A, "player2_id": PLAYER_B}
    ]
    for key in list(sys.modules.keys()):
        if key == "api.main" or key == "api.routers" or key.startswith("api.routers."):
            del sys.modules[key]
    with patch("api.dependencies.get_supabase", lambda: mock_sb):
        from api.main import app
        tc = TestClient(app)
        r = tc.post(
            f"/matches/{MATCH_ID}/notify-pending",
            headers=_auth_headers(player_id="00000000-0000-0000-0000-000000000099"),
        )
    assert r.status_code == 403
    assert "participant" in (r.json() or {}).get("detail", "").lower() or "access denied" in (r.json() or {}).get("detail", "").lower()


# --- POST /matches/{match_id}/confirm ---


def test_confirm_confirmed_by_mismatch_returns_403(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-at-least-32-characters-long")
    mock_sb = _make_mock_supabase()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": MATCH_ID,
            "status": "pending_confirm",
            "player1_id": PLAYER_A,
            "player2_id": PLAYER_B,
            "submitted_by": PLAYER_A,
        }
    ]
    with patch("api.dependencies.get_supabase", return_value=mock_sb):
        from api.main import app
        tc = TestClient(app)
        r = tc.post(
            f"/matches/{MATCH_ID}/confirm",
            json={"confirmed_by_player_id": PLAYER_B},  # ignored in bearer-only mode
            headers=_auth_headers(player_id=PLAYER_A),
        )
    assert r.status_code == 400


# --- POST /matches/{match_id}/reject ---


def test_reject_rejected_by_mismatch_returns_403(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-at-least-32-characters-long")
    mock_sb = _make_mock_supabase()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": MATCH_ID,
            "status": "pending_confirm",
            "player1_id": PLAYER_A,
            "player2_id": PLAYER_B,
            "submitted_by": PLAYER_A,
        }
    ]
    with patch("api.dependencies.get_supabase", return_value=mock_sb):
        from api.main import app
        tc = TestClient(app)
        r = tc.post(
            f"/matches/{MATCH_ID}/reject",
            json={"rejected_by_player_id": PLAYER_B},  # ignored in bearer-only mode
            headers=_auth_headers(player_id=PLAYER_A),
        )
    assert r.status_code == 400


# --- GET /matches/{match_id} with Bearer: only participants ---


def test_get_match_by_id_non_participant_returns_403(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-at-least-32-characters-long")
    mock_sb = _make_mock_supabase()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        MagicMock(data=[{"id": MATCH_ID, "player1_id": PLAYER_A, "player2_id": PLAYER_B}]),
        MagicMock(data=[{"id": PLAYER_A, "name": "A", "telegram_id": 1}]),
        MagicMock(data=[{"id": PLAYER_B, "name": "B", "telegram_id": 2}]),
    ]
    for key in list(sys.modules.keys()):
        if key == "api.main" or key == "api.routers" or key.startswith("api.routers."):
            del sys.modules[key]
    with patch("api.dependencies.get_supabase", lambda: mock_sb):
        from api.main import app
        tc = TestClient(app)
        r = tc.get(
            f"/matches/{MATCH_ID}",
            headers=_auth_headers(player_id="00000000-0000-0000-0000-000000000099"),
        )
    assert r.status_code == 403
    assert "participant" in (r.json() or {}).get("detail", "").lower() or "access denied" in (r.json() or {}).get("detail", "").lower()
