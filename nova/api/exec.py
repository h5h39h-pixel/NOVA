# -*- coding: utf-8 -*-
"""Terminal exec route — run a PowerShell command (LAN-gated + destructive-confirm guard), tracked by
the ProcMgr. Extracted from server.py (HON-11). The exec surface is the highest-risk endpoint; the
guards (exec_allowed + danger_reason confirm) live here."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from nova.core.process import ps_args
from nova.core.safety import danger_reason
from nova.services.settings import exec_allowed
from nova.services.jobs import PM
from nova.services.audit import audit

router = APIRouter()


@router.post("/api/exec")
async def api_exec(req: Request):
    if not exec_allowed():
        audit("terminal", "run_command", "blocked (remote exec disabled)", "blocked")
        return JSONResponse({"error": "Command execution is disabled while exposed on the LAN. "
                                      "Enable 'allow_remote_exec' in Settings to permit it."}, status_code=403)
    b = await req.json(); cmd = (b.get("command") or "").strip()
    if not cmd:
        return JSONResponse({"error": "empty"}, status_code=400)
    # SEC-1/SEC-2: clearly-destructive commands require an explicit confirm (the Terminal asks first).
    why = danger_reason(cmd)
    if why and not b.get("confirm"):
        audit("terminal", "run_command", cmd, "needs_confirm")
        return JSONResponse({"needs_confirm": True,
                             "reason": f"This looks destructive — {why}. Run it anyway?"}, status_code=409)
    job = PM.start(cmd, ps_args(cmd), kind="command", source="terminal")
    audit("terminal", "run_command", cmd, "forced" if why else "ok")
    return {"ok": True, "job": job.id}
