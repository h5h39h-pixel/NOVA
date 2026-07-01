# -*- coding: utf-8 -*-
"""Tests for the confirmation layer (control_mode: auto | confirm | full)."""
import threading
import time


def test_control_mode_resolution(tmpdb):
    import nova.services.confirm as C
    from nova.core.db import set_settings
    set_settings({"control_mode": "confirm"})
    assert C.control_mode() == "confirm" and C.needs_confirm("run_command") is True
    assert C.needs_confirm("kb_search") is False        # read-only never needs confirm
    set_settings({"control_mode": "full"})
    assert C.is_full_access() is True and C.needs_confirm("control") is False
    set_settings({"control_mode": "auto"})
    assert C.needs_confirm("run_command") is False
    set_settings({"control_mode": "garbage"})
    assert C.control_mode() == "auto"                    # invalid → safe default


def test_confirm_timeout_denies(tmpdb):
    import nova.services.confirm as C
    from nova.core.db import set_settings
    set_settings({"control_mode": "confirm"})
    assert C.request_confirmation("control", "click 5,5", timeout=0.2) is False   # no UI answer → deny


def test_confirm_approve_and_deny(tmpdb):
    import nova.services.confirm as C
    from nova.core.db import set_settings
    set_settings({"control_mode": "confirm"})

    def _run(out):
        out["r"] = C.request_confirmation("run_command", "echo hi", timeout=5)

    for approved in (True, False):
        out = {}
        t = threading.Thread(target=_run, args=(out,)); t.start()
        cid = None
        for _ in range(100):                             # wait for the request to register
            p = C.pending()
            if p: cid = p[0]; break
            time.sleep(0.02)
        assert cid, "confirmation was never registered"
        assert C.resolve(cid, approved) is True
        t.join(3)
        assert out["r"] is approved


def test_gate_auto_never_blocks(tmpdb):
    import nova.services.confirm as C
    from nova.core.db import set_settings
    set_settings({"control_mode": "auto"})
    ok, msg = C.gate("run_command", "rm -rf x")
    assert ok is True and msg is None                    # auto → no prompt, proceeds


def test_agent_tool_respects_denied_confirm(monkeypatch, tmpdb):
    """agent_tool aborts a dangerous action when the confirmation gate denies it."""
    import nova.services.agent as A
    import nova.services.confirm as C
    monkeypatch.setattr(C, "gate", lambda action, detail="": (False, f"BLOCKED: denied '{action}'"))
    out = A.agent_tool("run_command", {"command": "echo hi"}, dry_run=False)
    assert "BLOCKED" in out and "denied" in out
