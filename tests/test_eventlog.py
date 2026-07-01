# -*- coding: utf-8 -*-
"""Unified event log — store, filters, timeline, retention, and the bridges from audit / errors /
notifications so everything lands in one searchable place."""


def test_log_query_get_clear(tmpdb):
    from nova.core import eventlog as E
    E.clear()
    E.log("exec", "ran a command", level="info", source="terminal", detail="Get-Date", actor="user")
    E.log("error", "boom", level="error", source="loop", status="fail")
    res = E.query()
    assert res["total"] == 2 and res["items"][0]["message"] == "boom"     # newest first
    # filter by level + category
    assert E.query(level="error")["total"] == 1
    assert E.query(category="exec")["total"] == 1
    # full-text q matches message/detail/source
    assert E.query(q="Get-Date")["total"] == 1
    # get one
    eid = res["items"][0]["id"]
    assert E.get(eid)["message"] == "boom"
    E.clear()
    assert E.query()["total"] == 0


def test_invalid_level_category_defaulted(tmpdb):
    from nova.core import eventlog as E
    E.clear()
    E.log("nonsense-cat", "x", level="loud")
    row = E.query()["items"][0]
    assert row["category"] == "action" and row["level"] == "info"        # coerced to safe defaults


def test_record_exception_trace_and_throttle(tmpdb):
    from nova.core import eventlog as E
    E.clear(); E._last_error.clear()
    try:
        raise ValueError("kaboom-xyz")
    except ValueError as e:
        E.record_exception("mymodule.func", e, request_id=7)
    row = E.query(category="error")["items"][0]
    assert "kaboom-xyz" in row["message"] and "ValueError" in row["trace"]
    assert row["context"]["request_id"] == 7
    # throttled: an identical exception within the window is NOT logged again
    try:
        raise ValueError("kaboom-xyz")
    except ValueError as e:
        E.record_exception("mymodule.func", e)
    assert E.query(category="error")["total"] == 1


def test_stats_timeline(tmpdb):
    from nova.core import eventlog as E
    E.clear()
    for _ in range(3):
        E.log("system", "tick")
    E.log("error", "bad", level="error")
    s = E.stats(hours=1, buckets=10)
    assert s["by_category"].get("system") == 3 and s["by_level"].get("error") == 1
    assert len(s["timeline"]) == 10 and sum(b["total"] for b in s["timeline"]) == 4


def test_prune_retention(tmpdb, monkeypatch):
    from nova.core import eventlog as E
    E.clear()
    for i in range(20):
        E.log("system", f"e{i}")
    assert E.prune(keep=5) == 15 and E.query()["total"] == 5             # oldest removed, newest kept


# ---- bridges ----
def test_audit_bridges_to_eventlog(tmpdb):
    from nova.core import eventlog as E
    from nova.services.audit import audit
    E.clear()
    audit("security", "injection_detected", "ignore previous", "warn")
    audit("terminal", "run_command", "Get-Date")
    cats = {r["category"] for r in E.query()["items"]}
    assert "security" in cats and "exec" in cats
    sec = E.query(category="security")["items"][0]
    assert sec["level"] == "warn" and sec["actor"] == "security"


def test_error_record_bridges(tmpdb, monkeypatch, tmp_path):
    from nova.core import eventlog as E
    import nova.core.errors as ERR
    monkeypatch.setattr(ERR, "_FILE", tmp_path / "errors.json")   # don't pollute the real error log
    ERR._errors.clear()
    E.clear(); E._last_error.clear()
    try:
        raise RuntimeError("bridge-me-123")
    except RuntimeError as e:
        ERR.record("some.loop", e)
    hit = E.query(category="error", q="bridge-me-123")
    assert hit["total"] == 1 and "RuntimeError" in hit["items"][0]["trace"]


def test_request_logging(tmpdb):
    """Complete API access record: mutations + non-poll reads + errors are logged; high-frequency
    polls and static assets are skipped (so the log stays a record of real operations)."""
    from nova.core import eventlog as E
    E.clear()
    E.log_request("POST", "/api/agent", 200, 12.3)          # mutation → logged (info)
    E.log_request("GET", "/api/health", 200, 1.0)           # poll → skipped
    E.log_request("GET", "/api/metrics", 200, 1.0)          # poll → skipped
    E.log_request("GET", "/api/kb/docs", 200, 5.0)          # non-poll read → logged (debug)
    E.log_request("POST", "/api/exec", 500, 9.0)            # error → logged (error)
    E.log_request("GET", "/dashboard", 200, 1.0)            # static → skipped
    items = E.query(limit=50)["items"]
    paths = [i["source"] for i in items]
    assert "POST /api/agent" in paths and "GET /api/kb/docs" in paths and "POST /api/exec" in paths
    assert "GET /api/health" not in paths and "GET /api/metrics" not in paths and "GET /dashboard" not in paths
    err = next(i for i in items if i["source"] == "POST /api/exec")
    assert err["level"] == "error" and err["category"] == "exec" and err["context"]["status"] == 500
    agent = next(i for i in items if i["source"] == "POST /api/agent")
    assert agent["level"] == "info" and agent["category"] == "api"


def test_notification_bridges(tmpdb):
    from nova.core import eventlog as E
    from nova.services.notifications import add_notification
    E.clear()
    add_notification("info", "Backup done", "14 snapshots")
    row = E.query(category="alert")["items"][0]
    assert row["message"] == "Backup done" and row["source"] == "notification"
