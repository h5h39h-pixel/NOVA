# -*- coding: utf-8 -*-
"""Automatic issue discovery — the "brain" of the Ops Center. Scans the unified event log + live
services and surfaces actionable ISSUES (recurring errors, failing operations, services down), each
with a severity, a suggested next step, and a deep-link query into the Event Log. Issues can be filed
as bug reports (the in-app tracker) in one click, wiring diagnostics → tasks.

Read-only + cheap; never raises. Depends on nova.core.db + nova.core.http + config."""
import time
from nova.core.db import db


def _sev(n):
    return "critical" if n >= 20 else "high" if n >= 8 else "medium" if n >= 3 else "low"


def _issue(kind, severity, title, detail, category, count, suggestion, query):
    return {"id": f"{kind}:{abs(hash(title)) % 10**8}", "kind": kind, "severity": severity,
            "title": title, "detail": detail, "category": category, "count": count,
            "suggestion": suggestion, "query": query}


def discover_issues():
    """Return the current actionable issues, most severe first."""
    issues = []
    now = time.time()
    day = now - 86400
    try:
        c = db()
        # 1) recurring errors in the last 24h (grouped by message + trace signature)
        for r in c.execute(
                "SELECT message, COUNT(*) n, MAX(source) src FROM event_log "
                "WHERE category='error' AND ts>=? GROUP BY message HAVING n>=2 "
                "ORDER BY n DESC LIMIT 10", (day,)).fetchall():
            issues.append(_issue(
                "recurring-error", _sev(r["n"]),
                f"Recurring error ×{r['n']}: {(r['message'] or '')[:80]}",
                f"{r['n']} occurrences in the last 24h (source: {r['src']}).", "error", r["n"],
                "Open the Event Log filtered to this error and fix the root cause.",
                {"category": "error", "q": (r["message"] or "")[:40]}))
        # 2) operations failing repeatedly (non-error categories with fail/warn status)
        for r in c.execute(
                "SELECT source, COUNT(*) n FROM event_log "
                "WHERE status IN ('fail','error') AND category!='error' AND ts>=? "
                "GROUP BY source HAVING n>=3 ORDER BY n DESC LIMIT 8", (day,)).fetchall():
            issues.append(_issue(
                "failing-op", _sev(r["n"]),
                f"Failing operation ×{r['n']}: {r['source']}",
                f"{r['n']} failed operations from '{r['source']}' in 24h.", "action", r["n"],
                "Check the Event Log for these failures; the dependency or input may be broken.",
                {"source": r["source"], "status": "fail"}))
        c.close()
    except Exception:
        pass
    # 3) local services unreachable
    try:
        from nova.core.http import http_ok
        from config import OLLAMA, COMFY_URL, OWUI_URL
        for name, url in (("Ollama", f"{OLLAMA}/api/tags"), ("ComfyUI", f"{COMFY_URL}/system_stats"),
                          ("Open WebUI", f"{OWUI_URL}/")):
            if not http_ok(url):
                issues.append(_issue("service-down", "medium", f"{name} unreachable",
                                     f"{name} is not responding ({url}).", "system", 0,
                                     f"Start {name} (it's optional for core chat but needed for its features).",
                                     {"category": "system"}))
    except Exception:
        pass
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    issues.sort(key=lambda i: order.get(i["severity"], 9))
    return {"issues": issues, "count": len(issues), "generated": now}


def file_issue_as_bug(issue):
    """Create a bug report from a discovered issue (diagnostics → the in-app task tracker)."""
    from nova.services.notifications import add_notification
    title = str(issue.get("title", "Discovered issue"))[:120]
    detail = (str(issue.get("detail", "")) + "\n\nSuggested: " + str(issue.get("suggestion", "")))[:2000]
    sev = issue.get("severity", "medium")
    c = db()
    bid = c.execute(
        "INSERT INTO bug_reports(ts,title,detail,severity,status,page,logs) VALUES(?,?,?,?,?,?,?)",
        (time.time(), title, detail, sev, "open", "ops-center", "")).lastrowid
    c.commit(); c.close()
    add_notification("info", "Issue filed as bug", title[:60], category="system")
    return bid
