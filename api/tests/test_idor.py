"""
IDOR / access control tests (SECURITY_OWASP_ANALYSIS §2).
Endpoints that act on player_id or match_id must verify X-Player-Id matches the resource owner/participant.
"""
import sys
from typing import Optional
from unittest.mock import MagicMock, patch

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
        h["X-Player-Id"] = player_id
    return h


# --- PATCH /players/{player_id} ---


def test_patch_players_without_x_player_id_returns_403(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    r = client.patch(
        f"/players/{PLAYER_A}",
        json={"name": "New Name"},
        headers=_auth_headers(),
    )
    assert r.status_code == 403
    assert "X-Player-Id" in (r.json() or {}).get("detail", "")


def test_patch_players_wrong_player_id_returns_403(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    r = client.patch(
        f"/players/{PLAYER_A}",
        json={"name": "New Name"},
        headers=_auth_headers(player_id=PLAYER_B),
    )
    assert r.status_code == 403
    assert "only update your own" in (r.json() or {}).get("detail", "").lower() or "access denied" in (r.json() or {}).get("detail", "").lower()


# --- GET /players?telegram_id=... ---


def test_get_players_by_telegram_id_without_x_player_id_returns_403(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    r = client.get("/players?telegram_id=123", headers=_auth_headers())
    assert r.status_code == 403
    assert "X-Player-Id" in (r.json() or {}).get("detail", "")


# --- GET /matches/pending ---


def test_get_matches_pending_without_x_player_id_returns_403(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    r = client.get(
        f"/matches/pending?player_id={PLAYER_A}",
        headers=_auth_headers(),
    )
    assert r.status_code == 403
    assert "X-Player-Id" in (r.json() or {}).get("detail", "")


def test_get_matches_pending_player_id_mismatch_returns_403(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    r = client.get(
        f"/matches/pending?player_id={PLAYER_A}",
        headers=_auth_headers(player_id=PLAYER_B),
    )
    assert r.status_code == 403
    assert "pending" in (r.json() or {}).get("detail", "").lower() or "access denied" in (r.json() or {}).get("detail", "").lower()


# --- POST /matches/submit-for-confirmation ---


def test_submit_for_confirmation_submitted_by_mismatch_returns_403(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    r = client.post(
        "/matches/submit-for-confirmation",
        json={
            "division_id": "00000000-0000-0000-0000-000000000003",
            "player1_id": PLAYER_A,
            "player2_id": PLAYER_B,
            "sets_player1": 2,
            "sets_player2": 1,
            "submitted_by": PLAYER_A,
        },
        headers=_auth_headers(player_id=PLAYER_B),
    )
    assert r.status_code == 403
    assert "submitted_by" in (r.json() or {}).get("detail", "").lower() or "access denied" in (r.json() or {}).get("detail", "").lower()


# --- POST /matches/{match_id}/notify-pending ---


def test_notify_pending_caller_not_participant_returns_403(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
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
            json={"confirmed_by_player_id": PLAYER_B},
            headers=_auth_headers(player_id=PLAYER_A),
        )
    assert r.status_code == 403
    assert "confirmed_by_player_id" in (r.json() or {}).get("detail", "").lower() or "access denied" in (r.json() or {}).get("detail", "").lower()


# --- POST /matches/{match_id}/reject ---


def test_reject_rejected_by_mismatch_returns_403(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
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
            json={"rejected_by_player_id": PLAYER_B},
            headers=_auth_headers(player_id=PLAYER_A),
        )
    assert r.status_code == 403
    assert "rejected_by_player_id" in (r.json() or {}).get("detail", "").lower() or "access denied" in (r.json() or {}).get("detail", "").lower()


# --- GET /matches/{match_id} with X-Player-Id: only participants ---


def test_get_match_by_id_non_participant_returns_403(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
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
