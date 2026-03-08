"""
Shared fixtures and mock helpers for API tests.
Single _get_mock_supabase reference so dependency_overrides in tests use the same key as the app.
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _make_mock_supabase():
    mock = MagicMock()
    mock_execute = MagicMock()
    mock_execute.data = []
    mock.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_execute
    mock.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value = mock_execute
    mock.table.return_value.select.return_value.execute.return_value = mock_execute
    mock.table.return_value.update.return_value.eq.return_value.select.return_value.execute.return_value = mock_execute
    mock.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_execute
    mock.table.return_value.insert.return_value.select.return_value.execute.return_value = mock_execute
    mock.table.return_value.select.return_value.or_.return_value.execute.return_value = mock_execute
    return mock


def _get_mock_supabase():
    """Callable with no params so FastAPI OpenAPI schema does not get *args/**kwargs."""
    return _make_mock_supabase()


@pytest.fixture
def client():
    with patch("api.dependencies.get_supabase", _get_mock_supabase):
        from api.main import app
        yield TestClient(app)
