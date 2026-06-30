# -*- coding: utf-8 -*-
"""Shared pytest fixtures. Tests run against a temporary SQLite DB (the real
control.db is never touched) and mock external services (Ollama/ComfyUI)."""
import sys
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class _BlockedNetwork(RuntimeError):
    """Raised when a test makes a real outbound HTTP call (Ollama/ComfyUI/etc.)."""


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """TST-2 — hermetic test mode. Block real outbound HTTP at the one chokepoint every
    helper uses (`urllib.request.urlopen`), so the suite never needs Ollama/ComfyUI running
    and can't silently depend on them. `http_ok` catches this → returns False; `http_json`
    propagates it → callers degrade. Tests that need a live-service reply mock the relevant
    service function (e.g. `O.http_json`) directly, which sits above this block."""
    import urllib.request

    def _blocked(*a, **k):
        raise _BlockedNetwork(
            "Outbound network is blocked in tests (TST-2 hermetic mode). "
            "Mock the service call instead of hitting a live endpoint."
        )

    monkeypatch.setattr(urllib.request, "urlopen", _blocked)


@pytest.fixture
def tmpdb(tmp_path, monkeypatch):
    """Point the DB layer at an isolated temp database and initialize the schema."""
    import nova.core.db as dbm
    monkeypatch.setattr(dbm, "DB_PATH", tmp_path / "test.db")
    dbm.init_db()
    return tmp_path / "test.db"


@pytest.fixture
def client(tmp_path, monkeypatch):
    """FastAPI TestClient backed by a temp DB. No lifespan → no background loops,
    no external side effects. Endpoints that call live services degrade gracefully."""
    import nova.core.db as dbm
    monkeypatch.setattr(dbm, "DB_PATH", tmp_path / "api.db")
    dbm.init_db()
    import server
    from fastapi.testclient import TestClient
    return TestClient(server.app)
