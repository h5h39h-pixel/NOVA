# -*- coding: utf-8 -*-
"""IDEA-1 — visual macro recorder (passive capture).

Records live mouse clicks + keystrokes via pynput global listeners into an ordered list of `control`
steps, then saves the sequence as a Workflow so it can be replayed by the workflow runner (which
dispatches each step through the control service — see the `control` action in schedules.py).

Privacy & safety: recording is **explicitly user-initiated** (start/stop), never always-on; only runs
while active; capped at 500 events; gated by `exec_allowed()` (localhost). It captures global input
*only between start and stop* — the UI shows a clear "recording" state.

Honest limitations (documented):
- Replay of *typed text* uses UIA SetValue (reliable); replay of *special keys* uses pyautogui, which is
  suppressed in this environment — so special-key steps may not replay. Recording is still accurate.
- Coordinates are captured in physical pixels (pynput); replay uses pyautogui. On a DPI-scaled display
  the two can differ — record/replay at the same scale.

The event handlers (`_record_click`/`_record_char`/`_record_special`) are pure and operate on the
module buffer so they can be unit-tested without a real input device.
"""
import json
import threading
import time
from nova.core.db import db

_LOCK = threading.Lock()        # guards the start/stop lifecycle
_BUF = threading.Lock()         # guards the event buffers (mutated from 2 listener threads)
_REC = {"active": False, "steps": [], "typed": [], "t0": 0.0, "ml": None, "kl": None}
MAX_EVENTS = 500


def recording():
    return _REC["active"]


def state():
    return {"recording": _REC["active"], "count": len(_REC["steps"]),
            "seconds": round(time.time() - _REC["t0"], 1) if _REC["active"] else 0}


def _flush_typed_locked():
    """Collapse buffered characters into a single 'type' step. Caller must hold _BUF."""
    if _REC["typed"]:
        text = "".join(_REC["typed"])
        _REC["typed"] = []
        if text:
            _REC["steps"].append({"action": "type", "text": text})


def _record_click(x, y, button="left"):
    if not _REC["active"]:
        return
    with _BUF:
        _flush_typed_locked()
        _REC["steps"].append({"action": "click", "x": int(x), "y": int(y), "button": str(button)})
        full = len(_REC["steps"]) >= MAX_EVENTS
    if full:
        stop_recording()


def _record_char(ch):
    if _REC["active"] and ch:
        with _BUF:
            _REC["typed"].append(ch)


def _record_special(name):
    """A non-character key (enter/tab/etc.) → flush typed text, then record a key step."""
    if not _REC["active"]:
        return
    with _BUF:
        _flush_typed_locked()
        _REC["steps"].append({"action": "keys", "keys": str(name)})
        full = len(_REC["steps"]) >= MAX_EVENTS
    if full:
        stop_recording()


def start_recording():
    from nova.services.settings import exec_allowed
    if not exec_allowed():
        return {"ok": False, "error": "macro recording is disabled while exposed on the LAN"}
    with _LOCK:
        if _REC["active"]:
            return {"ok": False, "error": "already recording"}
        try:
            from pynput import mouse, keyboard
        except Exception as e:
            return {"ok": False, "error": f"pynput unavailable: {e}"}
        _REC.update(active=True, steps=[], typed=[], t0=time.time())

        def on_click(x, y, button, pressed):
            if pressed:
                try: _record_click(x, y, getattr(button, "name", "left"))
                except Exception: pass

        def on_press(key):
            try:
                ch = getattr(key, "char", None)
                if ch is not None:
                    _record_char(ch)
                else:
                    _record_special(str(key).replace("Key.", ""))
            except Exception:
                pass

        ml = mouse.Listener(on_click=on_click)
        kl = keyboard.Listener(on_press=on_press)
        ml.start(); kl.start()
        _REC["ml"], _REC["kl"] = ml, kl
    return {"ok": True}


def stop_recording():
    with _LOCK:
        if _REC["active"]:
            _REC["active"] = False
            with _BUF:
                _flush_typed_locked()
            for lst in (_REC["ml"], _REC["kl"]):
                try:
                    if lst: lst.stop()
                except Exception:
                    pass
            _REC["ml"] = _REC["kl"] = None
        return {"ok": True, "steps": list(_REC["steps"]), "count": len(_REC["steps"])}


def to_workflow_steps(steps):
    """Wrap recorded control-param dicts into workflow steps ({action:'control', params:{...}})."""
    return [{"action": "control", "params": s} for s in steps]


def save_macro(name, steps):
    """Persist a recorded macro as a replayable Workflow. Returns the new workflow id."""
    wf_steps = to_workflow_steps(steps)
    c = db()
    wid = c.execute("INSERT INTO workflows(name,steps,created) VALUES(?,?,?)",
                    (("🎬 " + (name or "macro"))[:80], json.dumps(wf_steps), time.time())).lastrowid
    c.commit(); c.close()
    return wid
