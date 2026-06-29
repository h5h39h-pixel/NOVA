# -*- coding: utf-8 -*-
"""Automation routes — schedules (CRUD + toggle + run-now), workflows (CRUD + run), and
A/B model testing. Logic lives in nova.services.schedules; this is request handling."""
import json
import time
import threading
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from nova.core.db import db
from nova.services.schedules import run_schedule, run_workflow, abtest_run

router = APIRouter()

# ---- schedules ----
@router.get("/api/schedules")
def api_schedules():
    c = db(); rows = [dict(r) for r in c.execute("SELECT * FROM schedules ORDER BY id DESC").fetchall()]; c.close()
    return rows

@router.post("/api/schedules")
async def api_sched_create(req: Request):
    b = await req.json()
    first = float(b.get("first_delay_sec", 60))
    c = db()
    c.execute("INSERT INTO schedules(name,action,params,interval_sec,next_run,enabled,created) VALUES(?,?,?,?,?,1,?)",
              (b.get("name", "Task")[:80], b.get("action", "notify"), json.dumps(b.get("params", {})),
               int(b.get("interval_sec", 0)), time.time() + first, time.time()))
    c.commit(); c.close()
    return {"ok": True}

@router.post("/api/schedules/{sid}/toggle")
def api_sched_toggle(sid: int):
    c = db(); cur = c.execute("SELECT enabled FROM schedules WHERE id=?", (sid,)).fetchone()
    if cur: c.execute("UPDATE schedules SET enabled=? WHERE id=?", (0 if cur["enabled"] else 1, sid)); c.commit()
    c.close(); return {"ok": True}

@router.post("/api/schedules/{sid}/run")
def api_sched_run(sid: int):
    c = db(); row = c.execute("SELECT * FROM schedules WHERE id=?", (sid,)).fetchone(); c.close()
    if not row: return JSONResponse({"error": "not found"}, status_code=404)
    return {"ok": True, "status": run_schedule(dict(row))}

@router.delete("/api/schedules/{sid}")
def api_sched_del(sid: int):
    c = db(); c.execute("DELETE FROM schedules WHERE id=?", (sid,)); c.commit(); c.close(); return {"ok": True}

# ---- workflows ----
@router.get("/api/workflows")
def api_workflows():
    c = db(); rows = [dict(r) for r in c.execute("SELECT * FROM workflows ORDER BY id DESC").fetchall()]; c.close()
    for r in rows:
        try: r["steps"] = json.loads(r["steps"] or "[]")
        except Exception: r["steps"] = []
    return rows

@router.post("/api/workflows")
async def api_wf_create(req: Request):
    b = await req.json()
    c = db(); c.execute("INSERT INTO workflows(name,steps,created) VALUES(?,?,?)",
                        (b.get("name", "Workflow")[:80], json.dumps(b.get("steps", [])), time.time())); c.commit(); c.close()
    return {"ok": True}

@router.post("/api/workflows/{wid}/run")
def api_wf_run(wid: int):
    threading.Thread(target=run_workflow, args=(wid,), daemon=True).start()
    return {"ok": True}

@router.delete("/api/workflows/{wid}")
def api_wf_del(wid: int):
    c = db(); c.execute("DELETE FROM workflows WHERE id=?", (wid,)); c.commit(); c.close(); return {"ok": True}

# ---- A/B model testing (scorecards) ----
@router.post("/api/abtest")
async def api_abtest(req: Request):
    b = await req.json()
    a, bmodel = b.get("model_a"), b.get("model_b")
    prompts = [p.strip() for p in (b.get("prompts") or []) if p.strip()][:10]
    if not (a and bmodel and prompts): return JSONResponse({"error": "need model_a, model_b, prompts"}, status_code=400)
    threading.Thread(target=abtest_run, args=(a, bmodel, prompts, b.get("judge")), daemon=True).start()
    return {"ok": True}
