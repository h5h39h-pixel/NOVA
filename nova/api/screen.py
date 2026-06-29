# -*- coding: utf-8 -*-
"""Screen Studio routes — capture / OCR+vision read / describe / record (start/stop/status/
list) / click-to-act (act/click/type). All capture & automation logic lives in
nova.services.screen; this layer adds request handling, auditing, and KB ingest on read."""
import asyncio
import uuid
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from config import UPLOAD_DIR
from nova.core.process import assign_to_job
from nova.services.audit import audit
from nova.services.notifications import add_notification
from nova.services.kb import kb_ingest_file
from nova.services import screen as screen_svc

screen_svc.set_assign_hook(assign_to_job)   # recordings inherit the Job Object (no orphans)

router = APIRouter()

@router.post("/api/screen/shot")
async def api_screen_shot(req: Request):
    b = await req.json() if await req.body() else {}
    fn, path = await asyncio.to_thread(screen_svc.capture_screenshot, b.get("region"))
    audit("screen", "shot", fn)
    return {"ok": True, "file": f"/files/{fn}"}

@router.post("/api/screen/read")
async def api_screen_read(req: Request):
    b = await req.json() if await req.body() else {}
    r = await asyncio.to_thread(screen_svc.read_screen, bool(b.get("vision")), b.get("region"), b.get("lang"))
    audit("screen", "read", ("vision" if b.get("vision") else "ocr") + f": {len(r.get('text',''))} chars")
    if b.get("to_kb") and r.get("text"):
        try:
            p = UPLOAD_DIR / f"screenread_{uuid.uuid4().hex[:6]}.txt"; p.write_text(r["text"], encoding="utf-8")
            kb_ingest_file(p); r["indexed"] = True
        except Exception: r["indexed"] = False
    return r

@router.post("/api/screen/describe")
async def api_screen_describe(req: Request):
    b = await req.json() if await req.body() else {}
    r = await asyncio.to_thread(screen_svc.describe_screen, b.get("question"), b.get("region"))
    audit("screen", "describe", (r.get("description") or r.get("error") or "")[:80])
    return r

@router.post("/api/screen/record/start")
async def api_screen_rec_start(req: Request):
    b = await req.json() if await req.body() else {}
    r = screen_svc.RECORDER.start(b.get("mode", "full"), b.get("region"), b.get("window"),
                                  bool(b.get("audio")), int(b.get("fps", 15)))
    if r.get("ok"):
        audit("screen", "record_start", r.get("mode", "full"))
        add_notification("info", "Screen recording started", r.get("mode", "full"))
    return r

@router.post("/api/screen/record/stop")
async def api_screen_rec_stop():
    r = screen_svc.RECORDER.stop()
    if r.get("ok"):
        audit("screen", "record_stop", f"{r.get('seconds')}s")
        add_notification("success", "Screen recording saved", f"{r.get('seconds')}s", link=r.get("file"))
    return r

@router.get("/api/screen/record/status")
def api_screen_rec_status():
    return screen_svc.RECORDER.status()

@router.get("/api/screen/recordings")
def api_screen_recordings():
    return {"items": screen_svc.list_recordings()}

@router.post("/api/screen/act")
async def api_screen_act(req: Request):
    b = await req.json(); instr = (b.get("instruction") or "").strip()
    if not instr: return JSONResponse({"error": "instruction required"}, status_code=400)
    r = await asyncio.to_thread(screen_svc.act_on_screen, instr, b.get("text"), b.get("key"), bool(b.get("double")))
    audit("screen", "act", f"{instr[:50]} -> {r.get('clicked')}", "ok" if r.get("ok") else "fail")
    return r

@router.post("/api/screen/click")
async def api_screen_click(req: Request):
    b = await req.json()
    r = await asyncio.to_thread(screen_svc.click_at, b.get("x", 0), b.get("y", 0), bool(b.get("double")), bool(b.get("right")))
    audit("screen", "click", f"{r.get('x')},{r.get('y')}")
    return r

@router.post("/api/screen/type")
async def api_screen_type(req: Request):
    b = await req.json()
    r = await asyncio.to_thread(screen_svc.type_text, b.get("text", "")) if b.get("text") else screen_svc.press_keys(b.get("key", ""))
    audit("screen", "type", str(b.get("text", b.get("key", "")))[:40])
    return r
