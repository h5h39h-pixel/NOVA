# -*- coding: utf-8 -*-
"""Ops Center routes — the unified diagnostics/audit/bugs hub API: auto-discovered issues, filing an
issue as a bug, a full exportable diagnostics report, and event-log export (JSON/CSV)."""
import csv
import io
import json
import time
from fastapi import APIRouter, Request
from fastapi.responses import Response
from nova.core import eventlog
from nova.services import issues as issues_svc

router = APIRouter()


@router.get("/api/issues")
def api_issues():
    """Auto-discovered actionable issues (recurring errors, failing ops, services down)."""
    return issues_svc.discover_issues()


@router.post("/api/issues/file")
async def api_issue_file(req: Request):
    """Turn a discovered issue into a bug report (diagnostics → tasks)."""
    issue = await req.json()
    bid = issues_svc.file_issue_as_bug(issue or {})
    return {"ok": True, "bug_id": bid}


@router.get("/api/ops/report")
def api_ops_report():
    """A single JSON diagnostics report: health snapshot, discovered issues, event stats, top errors.
    The exportable 'state of the system' for debugging/auditing."""
    from nova.core.errors import snapshot as err_snapshot, total as err_total
    rep = {"generated": time.time()}
    try: rep["issues"] = issues_svc.discover_issues()
    except Exception: rep["issues"] = {"issues": [], "count": 0}
    try: rep["event_stats"] = eventlog.stats(hours=24)
    except Exception: rep["event_stats"] = {}
    try: rep["top_errors"] = err_snapshot(20); rep["error_total"] = err_total()
    except Exception: rep["top_errors"] = []
    return rep


@router.get("/api/events/export")
def api_events_export(format: str = "json", level: str = "", category: str = "",
                      q: str = "", since: float = None, limit: int = 5000):
    """Download the (filtered) event log as JSON or CSV for external audit/analysis."""
    data = eventlog.query(level=level, category=category, q=q, since=since,
                          limit=min(int(limit), 20000))
    items = data["items"]
    stamp = time.strftime("%Y%m%d-%H%M%S")
    if format == "csv":
        buf = io.StringIO()
        cols = ["ts", "level", "category", "source", "message", "detail", "actor", "status"]
        w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for e in items:
            w.writerow({k: e.get(k) for k in cols})
        return Response(buf.getvalue(), media_type="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="events-{stamp}.csv"'})
    return Response(json.dumps(items, indent=2, default=str), media_type="application/json",
                    headers={"Content-Disposition": f'attachment; filename="events-{stamp}.json"'})
