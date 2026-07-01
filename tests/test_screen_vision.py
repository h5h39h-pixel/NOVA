# -*- coding: utf-8 -*-
"""SV-7 — AI Screen Vision tests. Verify the JPEG grab, and that every capture route is gated on the
opt-in privacy settings (off by default). The infinite MJPEG stream is only tested in its disabled
(403) state to avoid blocking; the single-frame route covers the enabled path."""
import numpy as np


def test_vision_state_default_off(client):
    r = client.get("/api/vision/state")
    assert r.status_code == 200
    j = r.json()
    assert j["enabled"] is False and j["track_mouse"] is False and j["track_keyboard"] is False
    assert 1 <= j["fps"] <= 15 and "max_width" in j and "quality" in j


def test_stream_and_frame_gated_off(client):
    assert client.get("/api/vision/stream").status_code == 403
    assert client.get("/api/vision/frame").status_code == 403
    assert client.post("/api/vision/describe", json={}).status_code == 403


def test_grab_jpeg(monkeypatch):
    import nova.services.screen as S
    import nova.services.screen_vision as V
    monkeypatch.setattr(S, "_grab", lambda region=None: np.zeros((40, 60, 3), dtype=np.uint8))
    b = V.grab_jpeg(max_width=32, quality=60)
    assert b[:2] == b"\xff\xd8"          # JPEG SOI marker
    assert len(b) > 100


def test_frame_when_enabled(client, monkeypatch):
    import nova.services.screen as S
    from nova.core.db import set_settings
    monkeypatch.setattr(S, "_grab", lambda region=None: np.zeros((40, 60, 3), dtype=np.uint8))
    set_settings({"screen_vision_enabled": True})
    r = client.get("/api/vision/frame")
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"
    assert r.content[:2] == b"\xff\xd8"


def test_mouse_gate(client):
    from nova.core.db import set_settings
    set_settings({"screen_vision_enabled": True, "track_mouse": False})
    assert client.get("/api/vision/mouse").status_code == 403      # tracking off → blocked even when enabled
    set_settings({"track_mouse": True})
    r = client.get("/api/vision/mouse")
    assert r.status_code == 200 and "mouse" in r.json()


def test_keyboard_context_gate(client, monkeypatch):
    import nova.services.screen_vision as SV
    monkeypatch.setattr(SV, "_ensure_kb_listener", lambda on: None)   # never start a real global keylogger in tests
    from nova.core.db import set_settings
    set_settings({"screen_vision_enabled": True, "track_keyboard": False, "allow_input_capture": True})
    assert client.get("/api/vision/context").status_code == 403       # feature toggle off → API blocked
    set_settings({"track_keyboard": True})
    r = client.get("/api/vision/context")
    assert r.status_code == 200 and r.json().get("enabled") is True    # both gates on → capture enabled


def test_keyboard_context_requires_master_gate(client, monkeypatch):
    """SV-4 defense: track_keyboard alone does NOT capture keystrokes — the master allow_input_capture
    gate is also required (keylogger-class feature, off by default)."""
    import nova.services.screen_vision as SV
    monkeypatch.setattr(SV, "_ensure_kb_listener", lambda on: None)
    from nova.core.db import set_settings
    set_settings({"screen_vision_enabled": True, "track_keyboard": True, "allow_input_capture": False})
    r = client.get("/api/vision/context")
    # API gate is on track_keyboard so it returns 200, but no keystrokes are captured without the master gate
    assert r.status_code == 200 and r.json().get("enabled") is False and "recent_text" not in r.json()


def test_narrate_gate(tmpdb):
    """SV-2: continuous narration only runs when BOTH screen vision and narrate are on."""
    import nova.services.screen_vision as SV
    from nova.core.db import set_settings
    set_settings({"screen_vision_enabled": False, "vision_narrate": True})
    assert SV.narrate_enabled() is False
    set_settings({"screen_vision_enabled": True, "vision_narrate": False})
    assert SV.narrate_enabled() is False
    set_settings({"screen_vision_enabled": True, "vision_narrate": True})
    assert SV.narrate_enabled() is True
    st = SV.vision_state()
    assert "narrate" in st and "narrate_interval" in st


def test_keyboard_context_off_no_listener(tmpdb):
    """SV-4: with track_keyboard off, context returns enabled:False and starts no listener."""
    import nova.services.screen_vision as SV
    from nova.core.db import set_settings
    set_settings({"track_keyboard": False})
    ctx = SV.keyboard_context()
    assert ctx["enabled"] is False and SV._KB["listener"] is None


def test_kb_listener_reconcile_stops_on_optout(tmpdb):
    """SV-4 privacy: reconcile_kb_listener() STOPS a running listener once track_keyboard is off
    (closes the leak where the API 403s on opt-out and never hits the stop path)."""
    import nova.services.screen_vision as SV
    from nova.core.db import set_settings

    class _Fake:
        def __init__(self): self.stopped = False
        def stop(self): self.stopped = True
    fake = _Fake()
    SV._KB["listener"] = fake          # simulate a listener left running from when tracking was on
    set_settings({"track_keyboard": False})
    SV.reconcile_kb_listener()
    assert fake.stopped is True and SV._KB["listener"] is None
