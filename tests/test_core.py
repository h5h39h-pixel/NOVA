# -*- coding: utf-8 -*-
"""Unit tests — nova/core (db, process, events)."""


def test_settings_roundtrip(tmpdb):
    from nova.core.db import get_settings, set_settings
    assert get_settings()["mode"] == "auto"
    set_settings({"mode": "local"})
    assert get_settings()["mode"] == "local"


def test_history(tmpdb):
    from nova.core.db import add_history, db
    add_history("echo hi", 0, 0.1, "hi", "terminal")
    c = db(); n = c.execute("SELECT COUNT(*) FROM history").fetchone()[0]; c.close()
    assert n == 1


def test_db_wal_and_busy_timeout(tmpdb):
    """STB-5: the DB runs in WAL with a busy timeout so concurrent loops don't hit 'database is locked'."""
    from nova.core.db import db
    c = db()
    assert c.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    assert c.execute("PRAGMA busy_timeout").fetchone()[0] >= 5000
    c.close()


def test_schema_version(tmpdb):
    from nova.core.db import db, SCHEMA_VERSION
    c = db(); v = c.execute("SELECT version FROM schema_version").fetchone()[0]; c.close()
    assert v == SCHEMA_VERSION


def test_ps_args_and_quote():
    from nova.core.process import ps_args, _q
    a = ps_args("echo hi")
    assert a[0] == "powershell" and "-EncodedCommand" in a
    assert _q("plain") == '"plain"'
    assert _q("-Flag") == "-Flag"            # bare flags left alone
    assert '`"' in _q('say "hi"')            # inner quotes escaped


def test_errors_persist(tmp_path, monkeypatch):
    """HON-4: recorded errors persist to disk and reload after a 'restart'."""
    import nova.core.errors as E
    monkeypatch.setattr(E, "_FILE", tmp_path / "errors.json")
    E.clear()
    E.record("loopX", ValueError("boom-xyz"))
    assert (tmp_path / "errors.json").exists()
    E._errors.clear()          # simulate restart (in-memory gone)
    E._load()                  # restore from disk
    assert any("boom-xyz" in x["signature"] for x in E.snapshot())
    E.clear()


def test_events_push_without_loop():
    from nova.core import events
    events.push({"type": "test"})            # must not raise when no loop is set
    assert isinstance(events.clients, set)


def test_supervise_restarts_crashed_loop(tmpdb, monkeypatch):
    """IDEA-10: a background loop that crashes hard is auto-restarted by _supervise; a clean
    CancelledError (shutdown) stops it without a restart."""
    import asyncio, pytest, server
    calls = {"n": 0}

    async def flaky():
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("boom")            # hard crash → supervisor must restart it
        raise asyncio.CancelledError()            # second run → stop the supervisor

    async def no_sleep(*a, **k):                   # don't actually wait out the backoff
        return
    monkeypatch.setattr(asyncio, "sleep", no_sleep)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(server._supervise(flaky))
    assert calls["n"] == 2                         # restarted exactly once after the crash
