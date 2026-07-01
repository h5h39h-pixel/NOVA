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
        "narrate": bool(s.get("vision_narrate")),
        "narrate_interval": _clamp(int(s.get("vision_narrate_interval", 30) or 30), 10, 300),
    }


def vision_enabled():
    return bool(get_settings().get("screen_vision_enabled"))


def screen_memory_enabled():
    return bool(get_settings().get("screen_memory_enabled"))


def remember_screen(min_chars=12):
    """IDEA-2 local screen memory (opt-in): OCR the current screen and index the text into the KB as a
    timestamped 'screen memory' doc, so the user can later ask "what did I see earlier?". Returns a
    summary dict. STRICTLY opt-in (`screen_memory_enabled`) and 100% local — nothing leaves the PC."""
    if not screen_memory_enabled():
        return {"ok": False, "error": "Screen memory is off. Enable it in Settings (privacy: opt-in)."}
    import time
    from nova.services.kb import kb_ingest_text
    try:
        r = screen_svc.read_screen(vision=False)        # Windows OCR (local, no model cost)
    except Exception as e:
        return {"ok": False, "error": f"screen read failed: {e}"}
    text = (r.get("text") or "").strip()
    if len(text) < min_chars:
        return {"ok": True, "stored": False, "reason": "no meaningful text on screen", "chars": len(text)}
    name = "screen-memory " + time.strftime("%Y-%m-%d %H:%M:%S")
    chunks = kb_ingest_text(name, text)
    pruned = _prune_screen_memory()                  # IDEA-2b: enforce the retention cap
    return {"ok": True, "stored": chunks > 0, "doc": name, "chars": len(text), "chunks": chunks,
            "pruned": pruned}


def _prune_screen_memory():
    """IDEA-2b: keep only the newest `screen_memory_keep` screen-memory docs (default 50); delete the
    rest (and their chunks). Returns how many docs were pruned. Prevents unbounded KB growth."""
    keep = get_settings().get("screen_memory_keep", 50)   # 0 is valid ("keep none") — don't `or 50` it away
    try: keep = max(0, int(keep))
    except (TypeError, ValueError): keep = 50
    from nova.core.db import db
    c = db()
    rows = c.execute("SELECT id FROM kb_docs WHERE name LIKE 'screen-memory %' ORDER BY created DESC").fetchall()
    old = [r["id"] for r in rows[keep:]]
    for did in old:
        c.execute("DELETE FROM kb_chunks WHERE doc_id=?", (did,))
        c.execute("DELETE FROM kb_docs WHERE id=?", (did,))
    if old: c.commit()
    c.close()
    return len(old)


def purge_screen_memory():
    """Delete ALL stored screen-memory docs (one-click privacy purge). Returns count removed."""
    from nova.core.db import db
    c = db()
    rows = c.execute("SELECT id FROM kb_docs WHERE name LIKE 'screen-memory %'").fetchall()
    ids = [r["id"] for r in rows]
    for did in ids:
        c.execute("DELETE FROM kb_chunks WHERE doc_id=?", (did,))
        c.execute("DELETE FROM kb_docs WHERE id=?", (did,))
    if ids: c.commit()
    c.close()
    return len(ids)


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


# ---- SV-4: opt-in recent-keystroke context ---------------------------------
# A SMALL in-memory rolling buffer of recently typed text, captured by a pynput listener that runs
# ONLY while `track_keyboard` is on. Never persisted, capped, cleared the moment the gate is turned
# off. Privacy: this is a global capture while active — gated, off by default, with a clear warning.
import threading
from collections import deque
_KB = {"listener": None, "buf": None, "keys": 0}
_KB_LOCK = threading.Lock()   # _ensure_kb_listener runs from BOTH the threadpool and the event loop


def _on_kb_press(key):
    """pynput listener-thread callback — append to the buffer under the lock (the buffer may be swapped
    to None by a concurrent stop)."""
    try:
        with _KB_LOCK:
            if _KB["buf"] is None:
                return
            _KB["keys"] += 1
            ch = getattr(key, "char", None)
            if ch is not None:
                _KB["buf"].append(ch)
            else:
                name = str(key).replace("Key.", "")
                if name == "space": _KB["buf"].append(" ")
                elif name == "enter": _KB["buf"].append("\n")
                elif name == "tab": _KB["buf"].append("\t")
                elif name == "backspace" and _KB["buf"]:
                    _KB["buf"].pop()
    except Exception:
        pass


def _ensure_kb_listener(on):
    # Lock the check-then-(start|stop) so two threads (the threadpool context call + the event-loop
    # reconcile) can't both create a listener — that would orphan a global keyboard hook that never
    # stops (a privacy leak). stop() is called OUTSIDE the lock to avoid any join-under-lock stall.
    to_stop = None
    with _KB_LOCK:
        if on and _KB["listener"] is None:
            try:
                from pynput import keyboard
            except Exception:
                return
            _KB["buf"] = deque(maxlen=240); _KB["keys"] = 0
            lst = keyboard.Listener(on_press=_on_kb_press)
            lst.start(); _KB["listener"] = lst
        elif not on and _KB["listener"] is not None:
            to_stop = _KB["listener"]
            _KB["listener"] = None; _KB["buf"] = None; _KB["keys"] = 0
    if to_stop is not None:
        try: to_stop.stop()
        except Exception: pass


def _kb_capture_on():
    # SV-4 needs BOTH the feature toggle AND the master input-capture gate (keylogger-class).
    s = get_settings()
    return bool(s.get("track_keyboard")) and bool(s.get("allow_input_capture"))


def reconcile_kb_listener():
    """Make the keyboard listener match the gates. Called periodically by a background loop so that
    turning tracking (or the master gate) OFF reliably STOPS the listener even though the API endpoint
    403s when off (so it would never otherwise hit the stop path) — closes a privacy leak."""
    try:
        _ensure_kb_listener(_kb_capture_on())
    except Exception:
        pass


def keyboard_context():
    """SV-4: focused-window title + (opt-in) a short rolling buffer of recently typed text. Requires
    both `track_keyboard` and the master `allow_input_capture` gate; otherwise only the window."""
    on = _kb_capture_on()
    _ensure_kb_listener(on)
    win = active_window()
    if not on:
        return {"enabled": False, "window": win}
    with _KB_LOCK:                                  # snapshot atomically — the listener thread mutates buf
        recent = ("".join(_KB["buf"]) if _KB["buf"] else "")[-200:]
        keys = _KB["keys"]
    return {"enabled": True, "window": win, "recent_text": recent, "keys": keys}


# ---- SV-2: continuous VLM narration loop (opt-in, throttled) ----------------
def narrate_enabled():
    s = get_settings()
    return bool(s.get("screen_vision_enabled")) and bool(s.get("vision_narrate"))


async def narration_loop():
    """When `screen_vision_enabled` + `vision_narrate` are both on, periodically VLM-describe the screen
    and push a running narration over the WS bus (rendered live). Opt-in + throttled (VLM cost) — idles
    cheaply when off. Supervised in server.py (auto-restarts if it ever crashes)."""
    import asyncio, time
    from nova.core.events import push
    while True:
        if not narrate_enabled():
            await asyncio.sleep(5)            # cheap idle poll until enabled
            continue
        interval = _clamp(int(get_settings().get("vision_narrate_interval", 30) or 30), 10, 300)
        try:
            d = await asyncio.to_thread(describe_now,
                                        "In one concise sentence, describe what is happening on the screen right now.")
            desc = (d.get("description") or "").strip()
            if desc:
                push({"type": "vision_narration", "text": desc, "ts": time.time()})
        except Exception:
            pass
        # sleep in short slices so disabling / interval changes take effect within ~2s, not a full interval
        waited = 0
        while waited < interval and narrate_enabled():
            await asyncio.sleep(2)
            waited += 2


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
