# -*- coding: utf-8 -*-
"""Perception & Control (Phase 8) — precise window awareness + mouse/keyboard control + UI element
detection.

- Window awareness: active window (title/process/pid/rect), all visible windows, screen resolution +
  DPI — via stdlib `ctypes` (Win32) + `psutil` (process names). No new dependency.
- Control: move/click/drag/scroll + key presses + accurate (clipboard) typing — via `pyautogui`
  (already a dep) and `screen.type_text` for Unicode/Arabic.
- Element detection: find UI elements by name/text (partial or exact) with their bounding rect + click
  center — via `uiautomation` (UI Automation).

These are powerful actions; routes/agent gate + audit them. Windows-only (degrades to errors elsewhere).
"""
import ctypes
import ctypes.wintypes as wt
import threading
import psutil
from nova.services import screen as screen_svc

# HON-1: global panic stop. When set, ALL mutating control (mouse/keyboard) is refused until resumed.
# This is the kill-switch for a runaway agent — defense in depth alongside the exec_allowed() gate.
CONTROL_PAUSED = threading.Event()


def control_paused():
    return CONTROL_PAUSED.is_set()


def pause_control():
    CONTROL_PAUSED.set()


def resume_control():
    CONTROL_PAUSED.clear()


def _blocked():
    return {"ok": False, "blocked": True, "reason": "control is paused (panic stop active — resume in the UI)"}

_user32 = ctypes.windll.user32
# Per-monitor DPI awareness so GetWindowRect / cursor coords are real pixels (accurate control).
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try: _user32.SetProcessDPIAware()
    except Exception: pass


class _RECT(ctypes.Structure):
    _fields_ = [("left", wt.LONG), ("top", wt.LONG), ("right", wt.LONG), ("bottom", wt.LONG)]


def _rect(hwnd):
    r = _RECT(); _user32.GetWindowRect(hwnd, ctypes.byref(r))
    return {"x": r.left, "y": r.top, "w": r.right - r.left, "h": r.bottom - r.top}


def _title(hwnd):
    n = _user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    _user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def _proc(hwnd):
    pid = wt.DWORD()
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    try:
        return psutil.Process(pid.value).name(), pid.value
    except Exception:
        return "", pid.value


# ---- awareness -------------------------------------------------------------
def active_window():
    h = _user32.GetForegroundWindow()
    name, pid = _proc(h)
    return {"hwnd": int(h), "title": _title(h), "process": name, "pid": pid, "rect": _rect(h)}


def list_windows(limit=60):
    out = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def _cb(hwnd, _l):
        try:
            if _user32.IsWindowVisible(hwnd):
                t = _title(hwnd)
                if t.strip():
                    name, pid = _proc(hwnd)
                    out.append({"hwnd": int(hwnd), "title": t, "process": name, "pid": pid, "rect": _rect(hwnd)})
        except Exception:
            pass
        return True

    _user32.EnumWindows(_cb, 0)
    return out[:limit]


def screen_info():
    dpi = 96
    try: dpi = _user32.GetDpiForSystem()
    except Exception: pass
    return {
        "primary": {"w": _user32.GetSystemMetrics(0), "h": _user32.GetSystemMetrics(1)},
        "virtual": {"w": _user32.GetSystemMetrics(78), "h": _user32.GetSystemMetrics(79)},
        "dpi": dpi, "scale": round(dpi / 96.0, 2),
    }


def awareness():
    """One call: active window + all windows + screen info — 'where am I / what's open'."""
    return {"active": active_window(), "windows": list_windows(), "screen": screen_info()}


# ---- mouse / keyboard control ---------------------------------------------
def _pag():
    import pyautogui
    pyautogui.FAILSAFE = True
    return pyautogui


def move_mouse(x, y, duration=0.1):
    if CONTROL_PAUSED.is_set(): return _blocked()
    _pag().moveTo(int(x), int(y), duration=duration)
    return {"ok": True, "x": int(x), "y": int(y)}


def click(x=None, y=None, button="left", double=False):
    if CONTROL_PAUSED.is_set(): return _blocked()
    p = _pag()
    if x is not None and y is not None:
        p.moveTo(int(x), int(y), duration=0.1)
    if double: p.doubleClick()
    elif button == "right": p.rightClick()
    else: p.click()
    return {"ok": True, "x": x, "y": y, "button": button, "double": double}


def drag(x1, y1, x2, y2, duration=0.3):
    if CONTROL_PAUSED.is_set(): return _blocked()
    p = _pag()
    p.moveTo(int(x1), int(y1), duration=0.1)
    p.dragTo(int(x2), int(y2), duration=duration, button="left")
    return {"ok": True, "from": [int(x1), int(y1)], "to": [int(x2), int(y2)]}


def scroll(amount):
    if CONTROL_PAUSED.is_set(): return _blocked()
    _pag().scroll(int(amount))
    return {"ok": True, "amount": int(amount)}


def _uia_set_focused(text):
    """Reliable text injection: set the value of the currently-focused UIA control directly
    (ValuePattern.SetValue) — focus-/foreground-robust, works where synthetic keystrokes don't.
    Returns True on success."""
    try:
        import uiautomation as auto
        c = auto.GetFocusedControl()
        if c is not None:
            c.GetValuePattern().SetValue(text)
            return True
    except Exception:
        pass
    return False


def type_text(text):
    if CONTROL_PAUSED.is_set(): return _blocked()
    if _uia_set_focused(text):                       # HON-2c: direct value-set (reliable)
        return {"ok": True, "typed": len(text), "via": "uia"}
    screen_svc.type_text(text)                       # fallback: clipboard paste / keystrokes
    return {"ok": True, "typed": len(text), "via": "clipboard"}


def set_element_text(name, text, partial=True):
    """Find a UIA element by name and set its text directly (no focus/typing needed) — the robust
    way to fill a named field in real apps (HON-2c)."""
    if CONTROL_PAUSED.is_set(): return _blocked()
    try:
        import uiautomation as auto
        want = (name or "").lower().strip()
        root = auto.GetForegroundControl() or auto.GetRootControl()
        for c, _ in auto.WalkControl(root, includeTop=True, maxDepth=14):
            try:
                nm = c.Name or ""
                if nm and ((want in nm.lower()) if partial else (nm.lower() == want)):
                    c.GetValuePattern().SetValue(text)
                    return {"ok": True, "set": nm}
            except Exception:
                continue
    except Exception as e:
        return {"ok": False, "error": str(e)[:160]}
    return {"ok": False, "error": f"no value-settable element matching '{name}'"}


def press_keys(keys):
    """keys: 'enter' | 'ctrl+s' | ['ctrl','s']."""
    if CONTROL_PAUSED.is_set(): return _blocked()
    p = _pag()
    if isinstance(keys, str):
        keys = [k.strip() for k in keys.replace("+", " ").split() if k.strip()]
    if not keys:
        return {"ok": False, "error": "no keys"}
    if len(keys) == 1: p.press(keys[0])
    else: p.hotkey(*keys)
    return {"ok": True, "keys": keys}


# ---- element detection (UI Automation) -------------------------------------
def find_element(name, partial=True, max_results=10):
    """Find UI elements whose Name matches `name` (substring if partial). Returns name, type,
    bounding rect, and click center for each match (ready to feed to click())."""
    try:
        import uiautomation as auto
    except Exception as e:
        return {"ok": False, "error": f"uiautomation unavailable: {e}", "matches": []}
    want = (name or "").lower().strip()
    if not want:
        return {"ok": False, "error": "no name", "matches": []}
    matches = []
    try:
        root = auto.GetForegroundControl() or auto.GetRootControl()
        for ctrl, _depth in auto.WalkControl(root, includeTop=True, maxDepth=14):
            try:
                nm = ctrl.Name or ""
            except Exception:
                continue
            if not nm:
                continue
            hit = (want in nm.lower()) if partial else (nm.lower() == want)
            if not hit:
                continue
            try:
                r = ctrl.BoundingRectangle
                if r.width() <= 0:
                    continue
                matches.append({"name": nm, "type": ctrl.ControlTypeName,
                                "rect": {"x": r.left, "y": r.top, "w": r.width(), "h": r.height()},
                                "center": {"x": r.xcenter(), "y": r.ycenter()}})
            except Exception:
                pass
            if len(matches) >= max_results:
                break
    except Exception as e:
        return {"ok": False, "error": str(e)[:200], "matches": matches}
    return {"ok": True, "count": len(matches), "matches": matches}


def click_element(name, partial=True, double=False):
    """Find an element by name and click its center."""
    if CONTROL_PAUSED.is_set(): return _blocked()
    r = find_element(name, partial, max_results=1)
    if not r.get("matches"):
        return {"ok": False, "error": f"no element matching '{name}'"}
    c = r["matches"][0]["center"]
    click(c["x"], c["y"], double=double)
    return {"ok": True, "clicked": r["matches"][0]["name"], "at": c}
