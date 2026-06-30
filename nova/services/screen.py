# -*- coding: utf-8 -*-
"""
Screen service — capture, record, and read the screen (fully native, no PowerShell).

Capture uses `mss` (fast, no AV/AMSI issues); recording grabs frames with mss and
writes an MP4 via imageio's bundled ffmpeg in a background thread. Reading uses the
toolkit's Windows OCR, and understanding uses the local qwen2.5-VL vision model.

Depends only on config (+ toolkit ocr.ps1 + Ollama). Routes/agent live in server.py
and call into here, per ARCHITECTURE.md.
"""
import time, uuid, subprocess, threading, base64, json, urllib.request, re

# SEC-6: OCR language codes are passed into a PowerShell -Command; allowlist them strictly
# (e.g. "eng", "ara", "eng+ara") so a malicious `lang` can't inject shell content.
_LANG_RE = re.compile(r"[A-Za-z]{2,8}(\+[A-Za-z]{2,8})*")
def _valid_lang(lang):
    return bool(lang) and bool(_LANG_RE.fullmatch(str(lang)))
import numpy as np
import mss
from config import WORKSPACE, TOOLKIT, OLLAMA

UPLOAD_DIR = WORKSPACE / "data" / "uploads"
VISION_MODEL = "qwen2.5vl:7b"   # strong screen-understanding VLM, runs locally on the 5090

# optional hook so the server can assign spawned processes to its Job Object (no orphans)
ASSIGN_HOOK = None
def set_assign_hook(fn):
    global ASSIGN_HOOK
    ASSIGN_HOOK = fn

def _grab(region=None):
    """Return an RGB numpy frame of the whole virtual screen (or a region bbox)."""
    with mss.mss() as sct:
        if region:
            x, y, w, h = [int(v) for v in region]
            mon = {"left": x, "top": y, "width": w, "height": h}
        else:
            mon = sct.monitors[0]   # the full virtual desktop (all monitors)
        raw = sct.grab(mon)
        arr = np.frombuffer(raw.rgb, dtype=np.uint8).reshape(raw.height, raw.width, 3)
        return arr

def capture_screenshot(region=None):
    """Capture full screen or a region → PNG in uploads/. Returns (filename, path)."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    fn = f"screen_{uuid.uuid4().hex[:8]}.png"; out = UPLOAD_DIR / fn
    import imageio.v2 as imageio
    imageio.imwrite(str(out), _grab(region))
    return fn, out

def read_screen(vision=False, region=None, lang=None):
    """Capture the screen and extract text via Windows OCR (or qwen2.5-VL vision)."""
    if vision:
        d = describe_screen("Extract ALL text visible on this screen exactly as written. Output only the text.", region)
        return {"ok": d.get("ok", True), "text": d.get("description", ""), "file": d.get("file"), "mode": "vision"}
    fn, path = capture_screenshot(region)
    cmd = '& "{}" "{}"'.format(TOOLKIT / "ocr.ps1", path)
    if _valid_lang(lang): cmd += f' -Lang {lang}'   # SEC-6: only allowlisted lang codes
    full = "& {" + cmd + "} 2>&1 | Out-String"
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", full],
                       capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace")
    return {"ok": True, "text": (r.stdout or "").strip(), "file": f"/files/{fn}", "mode": "ocr"}

def vlm_image(image_path, prompt=None, num_predict=600):
    """Run the local vision model (qwen2.5-VL) on ANY image file and return its text answer.
    Shared by describe_screen and the unified 'understand' service. Raises on failure."""
    from pathlib import Path as _P
    b64 = base64.b64encode(_P(image_path).read_bytes()).decode("ascii")
    prompt = prompt or ("Describe exactly what is on this image: the application/window, the visible "
                        "text, the buttons, menus and input fields, and what the user appears to be doing. "
                        "Be specific and concise.")
    body = json.dumps({"model": VISION_MODEL, "stream": False, "options": {"num_predict": num_predict},
                       "messages": [{"role": "user", "content": prompt, "images": [b64]}]}).encode()
    rq = urllib.request.Request(OLLAMA + "/api/chat", data=body,
                                headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(rq, timeout=180) as r:
        return (json.loads(r.read().decode()).get("message") or {}).get("content", "").strip()


def describe_screen(question=None, region=None):
    """Use the local vision model to understand the screen in natural language."""
    fn, path = capture_screenshot(region)
    try:
        desc = vlm_image(path, question)
        return {"ok": True, "description": desc, "file": f"/files/{fn}", "model": VISION_MODEL}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200], "file": f"/files/{fn}"}

# ----------------------------------------------------------------------------- act on screen (see → click → type)
def _pag():
    import pyautogui
    pyautogui.FAILSAFE = True
    return pyautogui

def click_at(x, y, double=False, right=False):
    p = _pag(); p.moveTo(int(x), int(y), duration=0.12)
    if right: p.rightClick()
    elif double: p.doubleClick()
    else: p.click()
    return {"ok": True, "x": int(x), "y": int(y)}

def type_text(text):
    """Type via clipboard paste (reliable for any language incl. Arabic), fallback to keystrokes."""
    try:
        import pyperclip
        pyperclip.copy(text); _pag().hotkey("ctrl", "v")
    except Exception:
        _pag().write(text, interval=0.01)
    return {"ok": True, "typed": len(text)}

def press_keys(combo):
    keys = [k.strip().lower() for k in combo.replace("+", " ").split() if k.strip()]
    if keys: _pag().hotkey(*keys)
    return {"ok": True, "keys": keys}

def locate_element(description, region=None):
    """Ask the vision model for the pixel coordinates to click for a described UI element."""
    fn, path = capture_screenshot(region)
    try:
        import imageio.v2 as imageio
        img = imageio.imread(str(path)); H, W = int(img.shape[0]), int(img.shape[1])
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        prompt = (f'The screenshot is {W}x{H} pixels (origin top-left). Output ONLY a compact JSON object '
                  f'{{"x": <int>, "y": <int>}} giving the pixel coordinates of the CENTER of this UI element: '
                  f'"{description}". If not visible, output {{"x": -1, "y": -1}}. No other text.')
        body = json.dumps({"model": VISION_MODEL, "stream": False, "options": {"num_predict": 80, "temperature": 0},
                           "messages": [{"role": "user", "content": prompt, "images": [b64]}]}).encode()
        rq = urllib.request.Request(OLLAMA + "/api/chat", data=body,
                                    headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(rq, timeout=120) as r:
            txt = (json.loads(r.read().decode()).get("message") or {}).get("content", "")
        import re
        m = re.search(r'"x"\s*:\s*(-?\d+)\s*,\s*"y"\s*:\s*(-?\d+)', txt)
        if not m:
            return {"ok": False, "error": "element not located", "raw": txt[:120], "file": f"/files/{fn}"}
        x, y = int(m.group(1)), int(m.group(2))
        if x < 0 or y < 0:
            return {"ok": False, "error": "element not visible", "file": f"/files/{fn}"}
        # clamp into bounds
        x = max(0, min(x, W - 1)); y = max(0, min(y, H - 1))
        return {"ok": True, "x": x, "y": y, "w": W, "h": H, "file": f"/files/{fn}"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:160], "file": f"/files/{fn}"}

_ACT_STOP = re.compile(r"\b(the|a|an|button|icon|menu|link|field|box|tab|on|screen|please|click|press|select|to)\b", re.I)
def _core_term(instr):
    """Reduce a natural instruction ('click the Save button') to its core target ('Save') so the
    UI-Automation name match can find it."""
    return " ".join(_ACT_STOP.sub(" ", instr or "").split())

def act_on_screen(instruction, text=None, key=None, double=False):
    """High-level: locate the target described by `instruction`, click it, then optionally type/press
    a key. **Tries precise UI-Automation element detection first** (exact pixel center, fast, reliable);
    falls back to vision-model grounding when the element has no UIA name (FEA-1)."""
    try:   # HON-1: honor the global panic stop
        from nova.services.control import control_paused
        if control_paused():
            return {"ok": False, "blocked": True, "error": "control is paused (panic stop active)"}
    except Exception:
        pass
    loc, via = None, "uia"
    try:
        from nova.services.control import find_element
        term = _core_term(instruction) or instruction
        r = find_element(term, partial=True, max_results=1)
        if r.get("matches"):
            c = r["matches"][0]["center"]; loc = {"ok": True, "x": c["x"], "y": c["y"]}
    except Exception:
        loc = None
    if not loc:
        via = "vision"
        loc = locate_element(instruction)
    if not loc.get("ok"):
        return loc
    click_at(loc["x"], loc["y"], double=double)
    time.sleep(0.5)
    out = {"ok": True, "clicked": [loc["x"], loc["y"]], "via": via}
    if text:
        type_text(text); out["typed"] = text
    if key:
        press_keys(key); out["key"] = key
    return out

class ScreenRecorder:
    """On-demand screen recording: mss frame grab → MP4 via imageio (background thread)."""
    def __init__(self):
        self._thread = None; self._stop = threading.Event()
        self.file = None; self.started = 0.0; self.mode = None; self.fps = 15; self._region = None

    def is_recording(self):
        return bool(self._thread and self._thread.is_alive())

    def _loop(self, out, fps, region):
        import imageio.v2 as imageio
        writer = imageio.get_writer(str(out), fps=fps, codec="libx264", quality=7,
                                    macro_block_size=None, ffmpeg_log_level="error")
        period = 1.0 / fps
        try:
            while not self._stop.is_set():
                t0 = time.time()
                try: writer.append_data(_grab(region))
                except Exception: pass
                dt = time.time() - t0
                if dt < period: self._stop.wait(period - dt)
        finally:
            try: writer.close()
            except Exception: pass

    def start(self, mode="full", region=None, window=None, audio=False, fps=15):
        if self.is_recording():
            return {"ok": False, "error": "already recording"}
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        fn = f"rec_{uuid.uuid4().hex[:8]}.mp4"; out = UPLOAD_DIR / fn
        self._region = region if (mode == "region" and region) else None
        self.fps = max(5, min(int(fps), 30)); self.mode = mode
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, args=(out, self.fps, self._region), daemon=True)
        self._thread.start()
        self.file = fn; self.started = time.time()
        return {"ok": True, "file": f"/files/{fn}", "mode": mode}

    def stop(self):
        if not self.is_recording():
            return {"ok": False, "error": "not recording"}
        f = self.file; dur = time.time() - self.started
        self._stop.set(); self._thread.join(timeout=15)
        self._thread = None; self.file = None
        return {"ok": True, "file": f"/files/{f}", "seconds": round(dur, 1)}

    def status(self):
        rec = self.is_recording()
        return {"recording": rec, "file": (f"/files/{self.file}" if rec else None),
                "seconds": round(time.time() - self.started, 1) if rec else 0, "mode": self.mode}

RECORDER = ScreenRecorder()

def list_recordings(limit=20):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(UPLOAD_DIR.glob("rec_*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    return [{"file": f"/files/{p.name}", "name": p.name, "size_kb": int(p.stat().st_size / 1024),
             "ts": p.stat().st_mtime} for p in files]
