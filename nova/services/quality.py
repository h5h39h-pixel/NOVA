# -*- coding: utf-8 -*-
"""IDEA-6 — quality dashboard. Record scored results of eval/health checks over time so regressions
after model/dep/prompt changes are visible as a trend (not just a one-off "it passed today").

Any eval can record a run via `record(suite, score, total, detail)`. A built-in lightweight
`health_snapshot()` records a composite local-health score (services up, runtime errors, KB indexed)
without calling heavy models — safe to schedule frequently. Heavier batteries (agent/RAG/gen) can POST
their scores here too. Local-only."""
import json
import time
from nova.core.db import db


def record(suite, score, total, detail=""):
    """Store one scored run. pct is score/total*100 (0 if total is 0)."""
    score = float(score); total = float(total)
    pct = round(score / total * 100, 1) if total else 0.0
    c = db()
    c.execute("INSERT INTO quality_runs(ts,suite,score,total,pct,detail) VALUES(?,?,?,?,?,?)",
              (time.time(), str(suite)[:60], score, total, pct, str(detail)[:500]))
    c.commit(); c.close()
    return {"suite": suite, "score": score, "total": total, "pct": pct}


def history(suite=None, limit=200):
    c = db()
    if suite:
        rows = c.execute("SELECT * FROM quality_runs WHERE suite=? ORDER BY id DESC LIMIT ?",
                         (suite, int(limit))).fetchall()
    else:
        rows = c.execute("SELECT * FROM quality_runs ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
    c.close()
    return [dict(r) for r in rows]


def summary():
    """Latest run + trend (delta vs the previous run) per suite."""
    c = db()
    suites = [r[0] for r in c.execute("SELECT DISTINCT suite FROM quality_runs").fetchall()]
    out = []
    for s in suites:
        rows = c.execute("SELECT pct, ts FROM quality_runs WHERE suite=? ORDER BY id DESC LIMIT 2", (s,)).fetchall()
        latest = rows[0]["pct"] if rows else 0.0
        prev = rows[1]["pct"] if len(rows) > 1 else None
        out.append({"suite": s, "latest": latest, "prev": prev,
                    "delta": (round(latest - prev, 1) if prev is not None else None),
                    "ts": rows[0]["ts"] if rows else None})
    c.close()
    out.sort(key=lambda x: x["suite"])
    return out


def health_snapshot():
    """A cheap composite local-health score (no heavy model calls): services reachable, low runtime
    errors, KB indexed. Records it under the 'health' suite and returns the breakdown."""
    from config import OLLAMA, COMFY_URL, OWUI_URL
    from nova.core.http import http_ok
    from nova.core.errors import snapshot as err_snapshot
    from nova.services.kb import kb_status
    checks = []
    checks.append(("ollama up", http_ok(f"{OLLAMA}/api/tags")))
    checks.append(("comfy up", http_ok(f"{COMFY_URL}/system_stats")))
    checks.append(("owui up", http_ok(f"{OWUI_URL}/")))
    try:
        errs = len(err_snapshot())
    except Exception:
        errs = 0
    checks.append(("no runtime errors", errs == 0))
    try:
        checks.append(("kb has docs", kb_status().get("docs", 0) > 0))
    except Exception:
        checks.append(("kb has docs", False))
    score = sum(1 for _, ok in checks if ok)
    total = len(checks)
    detail = json.dumps({k: bool(v) for k, v in checks})
    rec = record("health", score, total, detail)
    rec["checks"] = checks
    return rec
