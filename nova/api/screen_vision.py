# -*- coding: utf-8 -*-
"""AI Screen Vision routes (Phase 7). Live MJPEG stream, single frame, cursor position, focused-window
context, and on-demand VLM understanding. Every capture path is gated on the opt-in privacy settings;
logic lives in nova.services.screen_vision."""
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, Response, JSONResponse
from nova.services import screen_vision as sv
from nova.services.audit import audit

router = APIRouter()


def _gate(need_track=None):
    """Return an error response if the relevant privacy gate is off, else None."""
    st = sv.vision_state()
    if not st["enabled"]:
        return JSONResponse({"error": "Screen Vision is off. Enable it in Settings (privacy: opt-in)."}, status_code=403)
    if need_track and not st[need_track]:
        return JSONResponse({"error": f"'{need_track}' is off. Enable it in Settings."}, status_code=403)
    return None


@router.get("/api/vision/state")
def api_vision_state():
    return sv.vision_state()


@router.get("/api/vision/stream")
def api_vision_stream():
    g = _gate()
    if g: return g
    audit("vision", "stream", "live screen stream opened")
    return StreamingResponse(sv.mjpeg_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


@router.get("/api/vision/frame")
def api_vision_frame():
    g = _gate()
    if g: return g
    return Response(content=sv.grab_jpeg(**{k: sv.vision_state()[k] for k in ("max_width", "quality")}),
                    media_type="image/jpeg")


@router.get("/api/vision/mouse")
def api_vision_mouse():
    g = _gate("track_mouse")
    if g: return g
    return {"mouse": sv.mouse_pos()}


@router.get("/api/vision/context")
def api_vision_context():
    g = _gate("track_keyboard")
    if g: return g
    return sv.keyboard_context()   # SV-4: focused window + opt-in recent-keystroke buffer


@router.post("/api/vision/remember-screen")
def api_vision_remember_screen():
    """IDEA-2: snapshot the screen → OCR → index into the KB (opt-in `screen_memory_enabled`)."""
    if not sv.screen_memory_enabled():
        return JSONResponse({"error": "Screen memory is off. Enable it in Settings (privacy: opt-in)."},
                            status_code=403)
    r = sv.remember_screen()
    if r.get("stored"):
        audit("vision", "screen_memory", r.get("doc", ""))
    return r


@router.delete("/api/vision/screen-memory")
def api_vision_purge_screen_memory():
    """IDEA-2b: one-click purge of ALL stored screen-memory docs (privacy)."""
    n = sv.purge_screen_memory()
    audit("vision", "screen_memory_purge", f"removed {n} docs")
    return {"ok": True, "removed": n}


@router.post("/api/vision/describe")
async def api_vision_describe(req: Request):
    g = _gate()
    if g: return g
    body = {}
    try: body = await req.json()
    except Exception: pass
    audit("vision", "describe", (body.get("question") or "what's on screen")[:80])
    return sv.describe_now(body.get("question"))
