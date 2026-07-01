# -*- coding: utf-8 -*-
"""Agent session replay — reconstruct any past agent run step-by-step from the unified event log.

`agent_run` tags every step (goal → thought → action → observation → final) with a `run_id` in the
event's context (see `_rlog` in nova/services/agent.py). This module reads those back so a whole run
can be reviewed after the fact — invaluable for debugging what the agent actually did. Read-only."""
import json
from nova.core.db import db


def _agent_rows(where="", args=(), limit=3000):
    c = db()
    rows = c.execute(
        "SELECT id,ts,source,message,context FROM event_log WHERE category='agent'" + where +
        " ORDER BY id DESC LIMIT ?", (*args, limit)).fetchall()
    c.close()
    return rows


def _ctx(r):
    try:
        return json.loads(r["context"] or "{}")
    except Exception:
        return {}


def list_runs(limit=30):
    """Recent agent runs (newest first): run_id, goal, start/end, step count, final answer."""
    runs = {}
    for r in _agent_rows():
        ctx = _ctx(r)
        rid = ctx.get("run_id")
        if not rid:
            continue
        d = runs.get(rid)
        if not d:
            d = runs[rid] = {"run_id": rid, "started": r["ts"], "ended": r["ts"],
                             "goal": "", "final": "", "steps": 0}
        d["started"] = min(d["started"], r["ts"])
        d["ended"] = max(d["ended"], r["ts"])
        d["steps"] += 1
        if ctx.get("kind") == "goal":
            d["goal"] = r["message"]
        elif ctx.get("kind") == "final":
            d["final"] = r["message"]
    out = sorted(runs.values(), key=lambda x: x["ended"], reverse=True)[:limit]
    for d in out:
        d["duration_s"] = round(d["ended"] - d["started"], 1)
    return out


def get_run(run_id):
    """Full step-by-step timeline for one run, in chronological order."""
    rows = _agent_rows(" AND context LIKE ?", (f'%"run_id": "{run_id}"%',), limit=1000)
    steps = []
    for r in reversed(rows):                     # chronological
        ctx = _ctx(r)
        steps.append({"ts": r["ts"], "kind": ctx.get("kind"), "step": ctx.get("step"),
                      "text": r["message"], "source": r["source"]})
    goal = next((s["text"] for s in steps if s["kind"] == "goal"), "")
    final = next((s["text"] for s in steps if s["kind"] == "final"), "")
    return {"run_id": run_id, "goal": goal, "final": final, "steps": steps}
