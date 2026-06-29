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


def test_events_push_without_loop():
    from nova.core import events
    events.push({"type": "test"})            # must not raise when no loop is set
    assert isinstance(events.clients, set)
