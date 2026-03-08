"""
Tests that /players, /seasons, /divisions, /matches require valid X-API-Key when API_KEY is set.
Public routes (/, /health, /docs, /openapi-supabase.yaml, /docs-supabase) remain accessible without key.
"""
import os

import pytest

# client fixture and _get_mock_supabase from conftest (shared so dependency_overrides key matches)


# --- Public routes: must work without X-API-Key even when API_KEY is set ---

def test_root_without_key_when_api_key_set(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    r = client.get("/")
    assert r.status_code == 200
    assert "message" in r.json()


def test_health_without_key_when_api_key_set(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# --- Protected routes: require X-API-Key when API_KEY is set ---

@pytest.mark.parametrize("path", [
    "/players",
    "/players?telegram_id=1",
    "/players/rating",
    "/seasons/current",
    "/seasons/00000000-0000-0000-0000-000000000001/divisions",
    "/divisions/00000000-0000-0000-0000-000000000001",
    "/divisions/00000000-0000-0000-0000-000000000001/standings",
    "/matches/pending?player_id=00000000-0000-0000-0000-000000000001",
])
def test_protected_routes_401_without_key_when_api_key_set(client, monkeypatch, path):
    monkeypatch.setenv("API_KEY", "secret123")
    r = client.get(path)
    assert r.status_code == 401
    assert "Invalid or missing API key" in (r.json() or {}).get("detail", "")


@pytest.mark.parametrize("path", [
    "/players",
    "/players/rating",
    "/seasons/current",
])
def test_protected_routes_401_with_wrong_key_when_api_key_set(client, monkeypatch, path):
    monkeypatch.setenv("API_KEY", "secret123")
    r = client.get(path, headers={"X-API-Key": "wrong-key"})
    assert r.status_code == 401


@pytest.mark.parametrize("path", [
    "/players",
    "/players/rating",
    "/seasons/current",
])
def test_protected_routes_ok_with_valid_key_when_api_key_set(client, monkeypatch, path):
    monkeypatch.setenv("API_KEY", "secret123")
    r = client.get(path, headers={"X-API-Key": "secret123"})
    assert r.status_code != 401, f"Expected not 401 for {path} with valid key, got {r.status_code}"


# --- When API_KEY is not set, protected routes are accessible without key ---

def test_players_without_key_when_api_key_unset(client, monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    r = client.get("/players")
    assert r.status_code != 401
