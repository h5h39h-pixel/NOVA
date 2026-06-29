# -*- coding: utf-8 -*-
"""Training Studio + continuous-learning routes — dataset status/log, save/upload examples,
harvest, one-click retrain, pause/resume/stop, live progress, learning stats, run history.
All logic lives in nova.services.training; this layer is request validation + status codes."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from nova.services.notifications import add_notification
from nova.services import training as T

router = APIRouter()

@router.get("/api/training/status")
def api_training_status(): return T.training_status()

@router.get("/api/training/log")
def api_training_log(lines: int = 120): return T.training_log(lines)

@router.post("/api/training/save")
async def api_training_save(req: Request):
    b = await req.json()
    r = T.append_learned(b.get("user", ""), b.get("assistant", ""))
    if r is None: return JSONResponse({"ok": False, "error": "messages too short"}, status_code=400)
    add_notification("success" if r else "info",
                     "Saved to training" if r else "Already in training set",
                     (b.get("user", "")[:50]))
    return {"ok": True, "added": bool(r),
            "learned": len(T.read_jsonl(T.DS_LEARNED)), "combined": len(T.read_jsonl(T.DS_COMBINED))}

@router.post("/api/learn/harvest")
def api_learn_harvest():
    r = T.harvest()
    return r if r.get("ok") else JSONResponse(r, status_code=500)

@router.post("/api/learn/retrain")
def api_learn_retrain():
    """One-click: harvest new chats then retrain nova-local (runs learn.ps1 as a tracked job)."""
    if T.active_training_job():
        return JSONResponse({"ok": False, "error": "training already running"}, status_code=409)
    job = T.start_retrain()
    return {"ok": True, "job": job.id}

@router.post("/api/learn/stop")
def api_learn_stop():
    if not (T.active_training_job() or T.has_training_procs()):
        return JSONResponse({"ok": False, "error": "no training running"}, status_code=409)
    ok = T.training_stop()
    T.audit("training", "stop", "user stopped training")
    add_notification("info", "Training stopped", "stopped by user")
    return {"ok": ok}

@router.post("/api/learn/pause")
def api_learn_pause():
    ok = T.training_pause()
    if ok: T.audit("training", "pause", "user paused training"); add_notification("info", "Training paused", "resume any time")
    return {"ok": ok}

@router.post("/api/learn/resume")
def api_learn_resume():
    ok = T.training_resume()
    if ok: T.audit("training", "resume", "user resumed training")
    return {"ok": ok}

@router.get("/api/learn/progress")
def api_learn_progress(): return T.progress()

@router.get("/api/learning/stats")
def api_learning_stats(): return T.learning_stats()

@router.get("/api/training/history")
def api_training_history(limit: int = 20): return T.training_history(limit)

@router.post("/api/training/upload-dataset")
async def api_training_upload_dataset(req: Request):
    form = await req.form(); f = form.get("file")
    if not f: return JSONResponse({"error": "no file"}, status_code=400)
    raw = (await f.read()).decode("utf-8", errors="replace")
    return T.upload_dataset(raw)
