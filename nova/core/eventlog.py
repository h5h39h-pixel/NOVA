# -*- coding: utf-8 -*-
"""Unified event log — the project's single, structured record for debugging & auditing.

Captures three streams in ONE searchable table (`event_log`):
  • internal errors  — exceptions/crashes, with the full stack trace + context
  • external ops     — command exec, file I/O, network/browser, media/model calls
  • system events    — server start/stop, config changes, user/agent actions

Design notes:
  - one row per event; category + level make it filterable; `context` holds arbitrary JSON.
  - retention-capped (RETAIN rows) so the log can never fill the disk (lesson learned).
  - error events are throttled per-signature so a broken loop can't flood the log.
  - this is the STORE only (bottom layer, depends just on nova.core.db); the audit trail and the
    in-memory error aggregator bridge INTO here, and the API/UI read FROM here.
"""
import json
import time
import traceback
from nova.core.db import db

LEVELS = ("debug", "info", "warn", "error", "critical")
CATEGORIES = ("error", "exec", "file", "network", "system", "action",
              "agent", "security", "automation", "media", "alert", "api")

RETAIN = 50000                 # hard cap on stored rows (oldest pruned)
_THROTTLE_SECS = 30            # collapse identical error events within this window
_last_error = {}               # signature -> last-logged ts (flood control)
_since_prune = 0               # insert counter → prune every N inserts


def _prune_if_needed(c):
    """Keep the table bounded. Runs occasionally (not every insert) to stay cheap."""
    global _since_prune
    _since_prune += 1
    if _since_prune < 500:
        return
    _since_prune = 0
    n = c.execute("SELECT COUNT(*) FROM event_log").fetchone()[0]
    if n > RETAIN:
        cut = c.execute("SELECT id FROM event_log ORDER BY id DESC LIMIT 1 OFFSET ?",
                        (RETAIN,)).fetchone()
        if cut:
            c.execute("DELETE FROM event_log WHERE id <= ?", (cut[0],))


def log(category, message, *, level="info", source="", detail="",
        actor="system", status="ok", context=None, trace=None):
    """Record one event. Never raises (logging must not break the caller)."""
    try:
        if category not in CATEGORIES:
            category = "action"
        if level not in LEVELS:
            level = "info"
        ctx = json.dumps(context)[:4000] if context else None
        c = db()
        c.execute(
            "INSERT INTO event_log(ts,level,category,source,message,detail,trace,actor,status,context)"
            " VALUES(?,?,?,?,?,?,?,?,?,?)",
            (time.time(), level, category, str(source)[:160], str(message)[:500],
             str(detail)[:4000] if detail else None, trace, str(actor)[:40], str(status)[:20], ctx))
        _prune_if_needed(c)
        c.commit()
        c.close()
    except Exception:
        pass


# High-frequency polling endpoints — excluded from request logging so the log records real operations,
# not thousands of health/metrics polls. Mutations + non-poll reads + all errors are still logged.
_SKIP_GET = ("/api/metrics", "/api/health", "/api/processes", "/api/services", "/api/notifications",
             "/api/events", "/api/errors", "/api/quality", "/api/vision/stream", "/api/vision/frame",
             "/api/vision/mouse", "/api/vision/context", "/api/macro/state", "/api/auth/status")


def _req_category(path):
    if "/api/file" in path or "/upload" in path or "/ingest" in path:
        return "file"
    if "/api/exec" in path or "/terminal" in path:
        return "exec"
    if "/api/browse" in path or "/api/open-url" in path or "/api/search" in path:
        return "network"
    return "api"


def log_request(method, path, status, ms, actor="user"):
    """Access-log one HTTP request into the unified log. Skips static + high-frequency GET polls.
    Successful GETs are 'debug' (dimmable), mutations 'info', 4xx 'warn', 5xx 'error'."""
    if not path.startswith("/api"):
        return
    if method == "GET" and any(path.startswith(p) for p in _SKIP_GET):
        return
    level = "error" if status >= 500 else "warn" if status >= 400 else ("info" if method != "GET" else "debug")
    log(_req_category(path), f"{method} {path}", level=level, source=f"{method} {path}",
        actor=actor, status=("fail" if status >= 400 else "ok"),
        context={"status": status, "ms": round(ms, 1)})


def record_exception(source, exc, *, actor="system", **context):
    """Record an exception with its stack trace + context. Throttled per (type+message) so a loop
    erroring every tick logs once per window, not thousands of times."""
    try:
        sig = f"{type(exc).__name__}: {str(exc)[:140]}"
        now = time.time()
        last = _last_error.get(sig, 0)
        if now - last < _THROTTLE_SECS:
            return
        _last_error[sig] = now
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[-6000:]
        log("error", sig, level="error", source=source, trace=tb,
            actor=actor, status="fail", context=context or None)
    except Exception:
        pass


def _where(field, val, ops, args, like=False):
    if val:
        ops.append(f"{field} LIKE ?" if like else f"{field}=?")
        args.append(f"%{val}%" if like else val)


def query(level="", category="", source="", actor="", status="", q="",
          since=None, until=None, limit=200, offset=0):
    """Filtered, paginated search — newest first. `q` matches message/detail/source."""
    ops, args = [], []
    _where("level", level, ops, args)
    _where("category", category, ops, args)
    _where("actor", actor, ops, args)
    _where("status", status, ops, args)
    _where("source", source, ops, args, like=True)
    if q:
        ops.append("(message LIKE ? OR detail LIKE ? OR source LIKE ?)")
        args += [f"%{q}%", f"%{q}%", f"%{q}%"]
    if since is not None:
        ops.append("ts >= ?"); args.append(float(since))
    if until is not None:
        ops.append("ts <= ?"); args.append(float(until))
    where = (" WHERE " + " AND ".join(ops)) if ops else ""
    c = db()
    total = c.execute("SELECT COUNT(*) FROM event_log" + where, args).fetchone()[0]
    rows = c.execute(
        "SELECT id,ts,level,category,source,message,detail,trace,actor,status,context"
        " FROM event_log" + where + " ORDER BY id DESC LIMIT ? OFFSET ?",
        args + [int(limit), int(offset)]).fetchall()
    c.close()
    return {"total": total, "items": [_row(r) for r in rows]}


def get(event_id):
    c = db()
    r = c.execute(
        "SELECT id,ts,level,category,source,message,detail,trace,actor,status,context"
        " FROM event_log WHERE id=?", (int(event_id),)).fetchone()
    c.close()
    return _row(r) if r else None


def _row(r):
    d = dict(r)
    if d.get("context"):
        try: d["context"] = json.loads(d["context"])
        except Exception: pass
    return d


def stats(hours=24, buckets=48):
    """Counts by category + level, plus a time-bucketed timeline for the last `hours`."""
    now = time.time()
    since = now - hours * 3600
    span = max(1.0, (now - since) / buckets)
    c = db()
    by_cat = {r[0]: r[1] for r in c.execute(
        "SELECT category, COUNT(*) FROM event_log WHERE ts>=? GROUP BY category", (since,)).fetchall()}
    by_level = {r[0]: r[1] for r in c.execute(
        "SELECT level, COUNT(*) FROM event_log WHERE ts>=? GROUP BY level", (since,)).fetchall()}
    timeline = [{"t": 0, "total": 0, "error": 0} for _ in range(buckets)]
    for ts, lvl in c.execute("SELECT ts, level FROM event_log WHERE ts>=?", (since,)).fetchall():
        i = min(buckets - 1, int((ts - since) / span))
        timeline[i]["t"] = since + i * span
        timeline[i]["total"] += 1
        if lvl in ("error", "critical"):
            timeline[i]["error"] += 1
    c.close()
    return {"by_category": by_cat, "by_level": by_level, "timeline": timeline,
            "span_secs": span, "since": since}


def clear():
    c = db(); c.execute("DELETE FROM event_log"); c.commit(); c.close()
    _last_error.clear()


def prune(keep=RETAIN):
    """Force a prune to `keep` newest rows. Returns rows removed."""
    c = db()
    cut = c.execute("SELECT id FROM event_log ORDER BY id DESC LIMIT 1 OFFSET ?", (keep,)).fetchone()
    removed = 0
    if cut:
        removed = c.execute("DELETE FROM event_log WHERE id <= ?", (cut[0],)).rowcount
        c.commit()
    c.close()
    return removed
