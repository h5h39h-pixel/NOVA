# -*- coding: utf-8 -*-
"""IDEA-1 — visual macro recorder routes: start/stop passive recording, save the captured macro as a
reusable Workflow. Logic in nova.services.macro. Local-only; user-initiated; exec_allowed-gated."""
from fastapi import APIRouter, Request
from nova.services import macro as M
from nova.services.audit import audit

router = APIRouter()


@router.get("/api/macro/state")
def api_macro_state():
    return M.state()


@router.post("/api/macro/start")
def api_macro_start():
    r = M.start_recording()
    if r.get("ok"):
        audit("macro", "record_start", "")
    return r


@router.post("/api/macro/stop")
def api_macro_stop():
    return M.stop_recording()


@router.post("/api/macro/save")
async def api_macro_save(req: Request):
    """Stop (if still recording) and save the captured macro as a Workflow. Accepts an optional
    explicit `steps` list (e.g. an edited macro); otherwise uses what was just recorded."""
    b = {}
    try: b = await req.json()
    except Exception: pass
    if M.recording():
        M.stop_recording()
    # an explicit `steps` (even empty) is authoritative; only fall back to the recorded buffer if the
    # caller didn't provide the key at all.
    steps = b["steps"] if isinstance(b.get("steps"), list) else M._REC["steps"]
    if not steps:
        return {"ok": False, "error": "no steps recorded"}
    wid = M.save_macro(b.get("name", "macro"), steps)
    audit("macro", "save", f"#{wid} ({len(steps)} steps)")
    return {"ok": True, "id": wid, "steps": len(steps)}
