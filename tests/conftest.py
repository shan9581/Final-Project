"""Shared pytest fixtures for contract and integration tests."""
import os
import tempfile
import pytest
from server.app import create_app


@pytest.fixture
def app(tmp_path):
    """Flask app wired to a temporary SQLite file (fresh per test)."""
    flask_app = create_app({"DATABASE": str(tmp_path / "test.db"), "TESTING": True})
    yield flask_app


@pytest.fixture
def client(app):
    """HTTP test client."""
    return app.test_client()


@pytest.fixture
def db_path(tmp_path):
    """Real temporary SQLite file; auto-deleted after the test."""
    path = str(tmp_path / "test_workout.db")
    yield path
    if os.path.exists(path):
        os.remove(path)
