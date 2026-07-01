# -*- coding: utf-8 -*-
"""Anomaly alerts — watch the runtime for trouble and raise a notification when something looks wrong.

Signals (all derived from data we already collect — no new instrumentation):
  • error_spike  — a burst of error/critical events in the recent window (something started failing)
  • loop_stall   — the metrics loop stopped writing samples (a background loop died/blocked)
  • rss_climb    — this process's memory is trending up over many samples (a leak)

Runs on a supervised background loop (see server.py). Each finding is throttled so a persistent
condition alerts once per cooldown, not every tick. Read-only + notify-only: never changes state."""
import time
from nova.core import eventlog
from nova.core.db import db

# thresholds
_ERROR_SPIKE = 15            # error/critical events within the window → spike
_WINDOW_MIN = 10            # error-spike look-back (minutes)
_STALL_SECS = 180          # metrics loop silent this long → stalled
_RSS_SLOPE_MB_H = 40.0      # sustained RSS growth over this → suspected leak
_COOLDOWN = 900             # per-kind alert cooldown (seconds)

_last_alert = {}            # kind -> ts
_rss_samples = []           # [(ts, rss_mb)] rolling window for slope


def _cooling(kind, now):
    return (now - _last_alert.get(kind, 0)) < _COOLDOWN


def _alert(kind, message, detail=""):
    """Emit a notification + an 'alert' event. Best-effort; never raises."""
    _last_alert[kind] = time.time()
    try:
        eventlog.log("alert", message, level="warn", source=f"anomaly.{kind}",
                     detail=detail, actor="system", status="warn", context={"kind": kind})
    except Exception:
        pass
    try:
        from nova.services.notifications import add_notification
        add_notification("warn", "Anomaly detected", message, category="anomaly")
    except Exception:
        pass


def _check_error_spike(now, findings):
    if _cooling("error_spike", now):
        return
    since = now - _WINDOW_MIN * 60
    try:
        errs = eventlog.query(level="error", since=since, limit=_ERROR_SPIKE + 5)["total"]
        crit = eventlog.query(level="critical", since=since, limit=5)["total"]
    except Exception:
        return
    n = errs + crit
    if n >= _ERROR_SPIKE:
        findings.append({"kind": "error_spike", "count": n})
        _alert("error_spike", f"{n} errors in the last {_WINDOW_MIN} min",
               "A burst of errors suggests something started failing — check the Event Log.")


def _check_loop_stall(now, findings):
    if _cooling("loop_stall", now):
        return
    try:
        c = db()
        row = c.execute("SELECT MAX(ts) FROM metrics_history").fetchone()
        c.close()
    except Exception:
        return
    last = row[0] if row else None
    if last and (now - last) > _STALL_SECS:
        age = int(now - last)
        findings.append({"kind": "loop_stall", "age_s": age})
        _alert("loop_stall", f"Metrics loop silent for {age}s",
               "The system-metrics loop stopped writing samples — a background loop may have died.")


def _check_rss_climb(now, findings):
    try:
        import psutil
        rss_mb = psutil.Process().memory_info().rss / (1024 * 1024)
    except Exception:
        return
    _rss_samples.append((now, rss_mb))
    # keep ~2h of samples
    cutoff = now - 2 * 3600
    while _rss_samples and _rss_samples[0][0] < cutoff:
        _rss_samples.pop(0)
    if _cooling("rss_climb", now) or len(_rss_samples) < 6:
        return
    t0, r0 = _rss_samples[0]
    span_h = (now - t0) / 3600.0
    if span_h < 0.33:                      # need ≥20 min of history before trusting a slope
        return
    slope = (rss_mb - r0) / span_h
    if slope > _RSS_SLOPE_MB_H:
        findings.append({"kind": "rss_climb", "slope_mb_h": round(slope, 1)})
        _alert("rss_climb", f"Memory climbing ~{slope:.0f} MB/h",
               f"RSS rose from {r0:.0f}→{rss_mb:.0f} MB over {span_h:.1f}h — possible leak.")


def check_anomalies():
    """Run all checks once. Returns the list of findings this tick (also fired as alerts)."""
    now = time.time()
    findings = []
    _check_error_spike(now, findings)
    _check_loop_stall(now, findings)
    _check_rss_climb(now, findings)
    return findings
