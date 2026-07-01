# -*- coding: utf-8 -*-
"""Confirmation layer — the optional per-action safety gate for the autonomous agent.

Three modes (setting `control_mode`, stored in the DB):
  - **auto**  (default) — dangerous actions execute without a prompt (still panic/protected-window gated).
  - **confirm**         — before every dangerous action (run_command / control / act_on_screen /
                          write_file) the agent BLOCKS and asks the UI; the user Approves or Denies.
  - **full**            — execute everything without a prompt AND treat the run as unrestricted.

How the confirm handshake works (agent runs on a worker thread, UI is over the WS bus):
  1. the agent thread calls `request_confirmation(action, detail)` → registers a pending request,
     pushes a `{"type":"confirm", id, action, detail}` event over the bus, and BLOCKS on an Event.
  2. the browser shows a popup; the user clicks Approve/Deny → `POST /api/agent/confirm {id, approved}`
     → `resolve(id, approved)` sets the Event.
  3. `request_confirmation` returns the decision. A timeout (no UI / no answer) → **deny** (fail-safe).
"""
import threading
import uuid
from nova.core.db import get_settings
from nova.core.events import push

# actions that require confirmation in 'confirm' mode
DANGEROUS = frozenset(("run_command", "control", "act_on_screen", "write_file", "delete_file"))

_PENDING = {}          # id -> {"event": Event, "approved": bool}
_LOCK = threading.Lock()


def control_mode():
    # Degrade to 'auto' if settings can't be read (e.g. DB unavailable) — the confirmation layer must
    # never break tool execution just because it couldn't read its own setting.
    try:
        m = str(get_settings().get("control_mode") or "auto").lower()
    except Exception:
        return "auto"
    return m if m in ("auto", "confirm", "full") else "auto"


def is_full_access():
    return control_mode() == "full"


def needs_confirm(action):
    """True if this action must be confirmed given the current mode."""
    return control_mode() == "confirm" and action in DANGEROUS


def request_confirmation(action, detail="", timeout=120):
    """Block the calling (agent) thread until the user approves/denies via the UI, or `timeout`
    seconds pass (→ deny, fail-safe). Returns True if approved."""
    cid = uuid.uuid4().hex[:12]
    ev = threading.Event()
    with _LOCK:
        _PENDING[cid] = {"event": ev, "approved": False}
    push({"type": "confirm", "id": cid, "action": action, "detail": str(detail)[:300]})
    approved_in_time = ev.wait(timeout)
    with _LOCK:
        rec = _PENDING.pop(cid, None)
    approved = bool(approved_in_time and rec and rec["approved"])
    push({"type": "confirm_result", "id": cid, "approved": approved,
          "reason": "" if approved_in_time else "timeout"})
    return approved


def resolve(cid, approved):
    """Called by the API when the user answers. Returns True if a pending request was resolved."""
    with _LOCK:
        rec = _PENDING.get(cid)
        if not rec:
            return False
        rec["approved"] = bool(approved)
        rec["event"].set()
    return True


def pending():
    with _LOCK:
        return list(_PENDING.keys())


def gate(action, detail=""):
    """Convenience for the agent tool dispatch: if this action needs confirmation, ask and return
    (ok, message). ok=False means the user denied (or timed out) → the caller should abort the action."""
    if needs_confirm(action):
        if not request_confirmation(action, detail):
            return False, f"BLOCKED: you denied the '{action}' action (Confirm mode)."
    return True, None
