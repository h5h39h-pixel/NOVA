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


def test_keyboard_context_gate(client):
    from nova.core.db import set_settings
    set_settings({"screen_vision_enabled": True, "track_keyboard": False})
    assert client.get("/api/vision/context").status_code == 403
    set_settings({"track_keyboard": True})
    assert client.get("/api/vision/context").status_code == 200
