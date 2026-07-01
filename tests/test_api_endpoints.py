# -*- coding: utf-8 -*-
"""Broad API surface tests — hit every no-param GET endpoint and the thin POST routers via the
hermetic TestClient. Asserts no 500s and JSON/known shapes. Covers the many small api/* routers that
were previously exercised only indirectly. Live-service calls degrade gracefully (http_ok=False)."""

# every safe, no-parameter GET (excludes: /api/vision/stream = infinite; /api/control/panic = side
# effect; /api/file/read + /api/backup = need a param / return a download — tested elsewhere)
GET_ENDPOINTS = [
    "/api/achievements", "/api/audit", "/api/auth/status", "/api/backup/snapshots", "/api/brain",
    "/api/briefing", "/api/bugs", "/api/chat-history", "/api/comfy/status", "/api/control/active",
    "/api/control/awareness", "/api/control/screen", "/api/control/windows", "/api/conversations",
    "/api/copilot", "/api/habits", "/api/history", "/api/insights", "/api/jobs/history",
    "/api/kb/docs", "/api/kb/status", "/api/learn/progress", "/api/learning/stats", "/api/logs",
    "/api/macro/state", "/api/media-models", "/api/memory", "/api/metrics", "/api/metrics/history",
    "/api/models", "/api/notifications", "/api/owui", "/api/processes", "/api/processes/system",
    "/api/quality", "/api/schedules", "/api/screen/record/status", "/api/screen/recordings",
    "/api/search", "/api/services", "/api/settings", "/api/training/history", "/api/training/log",
    "/api/training/status", "/api/workflows",
]

# vision reads are privacy-gated → 403 when disabled (the default), which is correct, not an error
VISION_GATED = ["/api/vision/state", "/api/vision/frame", "/api/vision/mouse", "/api/vision/context"]


def test_all_get_endpoints_no_500(client):
    failed = []
    for ep in GET_ENDPOINTS:
        try:
            r = client.get(ep)
            if r.status_code >= 500:
                failed.append(f"{ep} -> {r.status_code}")
        except Exception as e:
            failed.append(f"{ep} -> EXC {e}")
    assert not failed, f"endpoints 500'd: {failed}"


def test_vision_gated_endpoints(client):
    for ep in VISION_GATED:
        r = client.get(ep)
        assert r.status_code in (200, 403), f"{ep} -> {r.status_code}"   # 403 = privacy gate (fine)


def test_settings_roundtrip_api(client):
    r = client.post("/api/settings", json={"control_mode": "confirm"}).json()
    assert r["control_mode"] == "confirm"
    r = client.post("/api/settings", json={"control_mode": "auto"}).json()
    assert r["control_mode"] == "auto"


def test_schedules_crud(client):
    c = client.post("/api/schedules", json={"name": "t", "action": "notify",
                                            "params": {"text": "hi"}, "interval_sec": 0}).json()
    assert c.get("ok") or "id" in c
    rows = client.get("/api/schedules").json()
    assert isinstance(rows, list)
    for s in rows:
        client.request("DELETE", f"/api/schedules/{s['id']}")


def test_workflows_crud(client):
    client.post("/api/workflows", json={"name": "wf", "steps": [{"action": "notify", "params": {"text": "x"}}]})
    rows = client.get("/api/workflows").json()
    assert any(w["name"] == "wf" for w in rows)
    for w in rows:
        client.request("DELETE", f"/api/workflows/{w['id']}")


def test_agent_endpoint_starts(client, monkeypatch):
    """POST /api/agent returns quickly (agent runs on a thread); we stub the thread target."""
    import nova.api.agent as AA
    monkeypatch.setattr(AA.threading, "Thread", lambda *a, **k: type("T", (), {"start": lambda self: None, "daemon": True})())
    r = client.post("/api/agent", json={"goal": "test goal"}).json()
    assert r.get("ok") is True and "model" in r
    assert client.post("/api/agent", json={"goal": ""}).status_code == 400   # empty goal rejected


def test_bugs_and_notifications_crud(client):
    b = client.post("/api/bugs", json={"title": "t", "detail": "d", "severity": "low"}).json()
    assert b.get("ok")
    assert isinstance(client.get("/api/bugs").json().get("items"), list)
    client.post("/api/notifications/seen")   # mark all seen
    assert client.get("/api/notifications").json()["unread"] == 0
