# -*- coding: utf-8 -*-
"""Metrics / services / processes routes — the live metrics snapshot, service up/down
status + start/restart, the tracked-job list + control, and top OS processes. Backed by
nova.services.metrics, nova.services.jobs (PM), nova.core.process + http, and config."""
import time
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import psutil
from config import COMFY, COMFY_URL, OLLAMA, OWUI_URL, OWUI_CTR
from nova.core.http import http_ok
from nova.core.process import ps_args
from nova.services.metrics import collect_metrics, get_last_metrics
from nova.services.jobs import PM

router = APIRouter()

# ---- metrics snapshot
@router.get("/api/metrics")
def api_metrics(): return get_last_metrics() or collect_metrics()

# ---- services
@router.get("/api/services")
def api_services():
    return {"ollama": http_ok(f"{OLLAMA}/api/tags"),
            "comfy":  http_ok(f"{COMFY_URL}/system_stats"),
            "owui":   http_ok(f"{OWUI_URL}/")}

@router.post("/api/services/{svc}/{action}")
def api_service_action(svc: str, action: str):
    if svc == "comfy" and action in ("start", "restart"):
        if action == "restart":
            PM.start("kill ComfyUI", ps_args("Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like '*ComfyUI*'} | Stop-Process -Force"))
        py = COMFY / "venv" / "Scripts" / "python.exe"
        PM.start("ComfyUI server", [str(py), str(COMFY / "main.py"), "--port", "8188"],
                 cwd=str(COMFY), kind="service")
        return {"ok": True}
    if svc == "owui" and action == "restart":
        PM.start("restart open-webui", ["docker", "restart", OWUI_CTR], kind="service")
        return {"ok": True}
    return JSONResponse({"ok": False, "error": "unsupported"}, status_code=400)

# ---- tracked background jobs
@router.get("/api/processes")
def api_processes(): return [j.info() for j in PM.jobs.values()][-50:]

@router.post("/api/processes/{jid}/{action}")
def api_proc_action(jid: str, action: str):
    if action == "stop":    return {"ok": PM.stop(jid)}
    if action == "restart":
        j = PM.restart(jid); return {"ok": bool(j), "job": j.info() if j else None}
    return JSONResponse({"error": "bad action"}, status_code=400)

# ---- live OS processes (psutil)
@router.get("/api/processes/system")
def api_proc_system(limit: int = 8):
    """Live OS processes via psutil (real CPU%/RAM), top by memory."""
    procs = []
    for p in psutil.process_iter(["pid", "name"]):
        try: p.cpu_percent(None); procs.append(p)
        except Exception: pass
    time.sleep(0.3)  # let cpu_percent measure an interval
    cores = psutil.cpu_count() or 1
    rows = []
    for p in procs:
        try:
            rows.append({"pid": p.pid, "name": p.info["name"] or "?",
                         "cpu": round(p.cpu_percent(None) / cores, 1),
                         "mem_mb": round(p.memory_info().rss / 1e6, 1)})
        except Exception: pass
    rows.sort(key=lambda x: x["mem_mb"], reverse=True)
    return {"count": len(rows), "top": rows[:limit]}
