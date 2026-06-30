# -*- coding: utf-8 -*-
"""Perception & Control routes (Phase 8). Read-only awareness (active window, all windows, screen,
find element) + mutating control (mouse/keyboard). Mutating actions are gated by `exec_allowed()`
(localhost allowed by design; LAN needs opt-in) and audited. Logic in nova.services.control."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from nova.services import control as C
from nova.services.settings import exec_allowed
from nova.services.audit import audit

router = APIRouter()


def _gate():
    if not exec_allowed():
        return JSONResponse({"error": "control is disabled while exposed on the LAN "
                             "(enable 'allow_remote_exec' in Settings)."}, status_code=403)
    return None


# ---- awareness (read-only) ----
@router.get("/api/control/awareness")
def api_awareness(): return C.awareness()


@router.get("/api/control/active")
def api_active(): return C.active_window()


@router.get("/api/control/windows")
def api_windows(): return {"windows": C.list_windows()}


@router.get("/api/control/screen")
def api_screen(): return C.screen_info()


@router.post("/api/control/find")
async def api_find(req: Request):
    b = await req.json()
    return C.find_element(b.get("name", ""), partial=b.get("partial", True))


# ---- control (gated + audited) ----
@router.post("/api/control/mouse")
async def api_mouse(req: Request):
    g = _gate()
    if g: return g
    b = await req.json(); act = b.get("action", "move")
    audit("control", f"mouse:{act}", f"{b.get('x')},{b.get('y')}")
    if act == "move": return C.move_mouse(b.get("x", 0), b.get("y", 0))
    if act == "click": return C.click(b.get("x"), b.get("y"), b.get("button", "left"), bool(b.get("double")))
    if act == "drag": return C.drag(b.get("x1", 0), b.get("y1", 0), b.get("x2", 0), b.get("y2", 0))
    if act == "scroll": return C.scroll(b.get("amount", 0))
    return JSONResponse({"error": "unknown mouse action"}, status_code=400)


@router.post("/api/control/key")
async def api_key(req: Request):
    g = _gate()
    if g: return g
    b = await req.json()
    if b.get("text") is not None:
        audit("control", "type", str(b.get("text"))[:40]); return C.type_text(b.get("text", ""))
    audit("control", "keys", str(b.get("keys"))[:40]); return C.press_keys(b.get("keys", ""))


@router.post("/api/control/click-element")
async def api_click_element(req: Request):
    g = _gate()
    if g: return g
    b = await req.json()
    audit("control", "click-element", str(b.get("name"))[:40])
    return C.click_element(b.get("name", ""), partial=b.get("partial", True), double=bool(b.get("double")))
