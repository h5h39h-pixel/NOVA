# -*- coding: utf-8 -*-
"""AI Screen Vision (Phase 7) — real-time screen perception.

Provides JPEG frame grabs (downscaled, throttled) for a live stream, live mouse position, and
focused-window context, plus on-demand VLM understanding. Builds on nova.services.screen (`_grab`,
`describe_screen`). Everything here is **privacy-gated**: nothing runs unless the matching opt-in
setting is on (`screen_vision_enabled`, `track_mouse`, `track_keyboard`). Nothing is persisted —
frames are streamed in memory only.

Depends on: nova.core.db (settings), nova.services.screen (capture + VLM), pillow (JPEG). Stdlib
ctypes is used for cursor/window info on Windows (no extra dependency)."""
import ctypes
import io
from nova.core.db import get_settings
from nova.services import screen as screen_svc


# ---- privacy gates ----------------------------------------------------------
def vision_state():
    s = get_settings()
    return {
        "enabled": bool(s.get("screen_vision_enabled")),
        "fps": _clamp(int(s.get("vision_fps", 4) or 4), 1, 15),
        "max_width": _clamp(int(s.get("vision_max_width", 1280) or 1280), 320, 3840),
        "quality": _clamp(int(s.get("vision_quality", 70) or 70), 30, 95),
        "track_mouse": bool(s.get("track_mouse")),
        "track_keyboard": bool(s.get("track_keyboard")),
    }


def vision_enabled():
    return bool(get_settings().get("screen_vision_enabled"))


def _clamp(v, lo, hi):
    try: return max(lo, min(int(v), hi))
    except Exception: return lo


# ---- frame grab (downscaled JPEG) ------------------------------------------
def grab_jpeg(max_width=1280, quality=70, region=None):
    """Grab the screen and return downscaled JPEG bytes. Caller must check the privacy gate first."""
    from PIL import Image
    arr = screen_svc._grab(region)                 # RGB numpy frame (whole virtual desktop)
    img = Image.fromarray(arr)
    if img.width > max_width:
        h = int(img.height * (max_width / img.width))
        img = img.resize((max_width, h), Image.BILINEAR)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=_clamp(quality, 30, 95))
    return buf.getvalue()


# ---- cursor + focused window (ctypes; Windows) -----------------------------
class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def mouse_pos():
    """Current global cursor position {x, y} (screen coords), or None if unavailable."""
    try:
        pt = _POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return {"x": int(pt.x), "y": int(pt.y)}
    except Exception:
        return None


def active_window():
    """Title of the currently focused window (light context; no keystroke capture), or None."""
    try:
        u = ctypes.windll.user32
        h = u.GetForegroundWindow()
        n = u.GetWindowTextLengthW(h)
        buf = ctypes.create_unicode_buffer(n + 1)
        u.GetWindowTextW(h, buf, n + 1)
        return {"title": buf.value}
    except Exception:
        return None


# ---- live MJPEG frame generator --------------------------------------------
async def mjpeg_frames():
    """Async generator of multipart MJPEG chunks while vision is enabled. Re-reads settings each
    tick so toggling the gate off (or changing FPS/quality) takes effect live and stops the stream."""
    import asyncio
    boundary = b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
    while vision_enabled():
        st = vision_state()
        try:
            jpg = await asyncio.to_thread(grab_jpeg, st["max_width"], st["quality"])
            yield boundary + jpg + b"\r\n"
        except Exception:
            break
        await asyncio.sleep(1.0 / st["fps"])


# ---- on-demand understanding ------------------------------------------------
def describe_now(question=None):
    """One-shot VLM understanding of the current screen (reuses Screen Studio's describe_screen)."""
    return screen_svc.describe_screen(question)
