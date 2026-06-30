# -*- coding: utf-8 -*-
"""Integration tests — FastAPI routers via TestClient (temp DB, no live server)."""
import re


def test_settings_endpoint(client):
    r = client.get("/api/settings")
    assert r.status_code == 200
    j = r.json()
    assert "mode" in j and "auth_token" not in j and "auth_token_hash" not in j


def test_history_and_notifications(client):
    assert client.get("/api/history").status_code == 200
    n = client.get("/api/notifications").json()
    assert "items" in n and "unread" in n


def test_audit_endpoint(client):
    j = client.get("/api/audit").json()
    assert "events" in j and isinstance(j["events"], list)


def test_bug_crud(client):
    assert client.post("/api/bugs", json={"title": "Test bug", "detail": "x"}).json()["ok"]
    items = client.get("/api/bugs").json()["items"]
    assert any(b["title"] == "Test bug" for b in items)
    bid = items[0]["id"]
    assert client.post(f"/api/bugs/{bid}/status", json={"status": "closed"}).json()["ok"]
    assert client.delete(f"/api/bugs/{bid}").json()["ok"]


def test_conversation_crud(client):
    cid = client.post("/api/conversations", json={"project": "T"}).json()["cid"]
    assert cid
    assert any(c["cid"] == cid for c in client.get("/api/conversations").json())
    assert client.delete(f"/api/conversations/{cid}").json()["ok"]


def test_settings_save_redacts(client):
    r = client.post("/api/settings", json={"mode": "local"}).json()
    assert r["mode"] == "local" and "auth_token" not in r


def test_selftest_endpoint(client):
    r = client.get("/api/selftest")
    assert r.status_code == 200 and "passed" in r.json() and "total" in r.json()


def test_agent_save_workflow(client):
    """IDEA-3: saving an agent run persists a one-step 'agent' workflow that replays the goal."""
    r = client.post("/api/agent/save-workflow",
                    json={"goal": "summarize my notes folder", "model": "auto", "deepthink": True}).json()
    assert r["ok"] and r["id"]
    wfs = client.get("/api/workflows").json()
    wf = next(w for w in wfs if w["id"] == r["id"])
    assert wf["steps"][0]["action"] == "agent"
    assert wf["steps"][0]["params"]["goal"] == "summarize my notes folder"
    assert wf["steps"][0]["params"]["deepthink"] is True


def test_macro_api_save(client):
    """IDEA-1: macro state + saving an explicit step list as a workflow (no real listeners started)."""
    st = client.get("/api/macro/state").json()
    assert st["recording"] is False
    steps = [{"action": "click", "x": 10, "y": 20, "button": "left"},
             {"action": "type", "text": "hello"}]
    r = client.post("/api/macro/save", json={"name": "demo", "steps": steps}).json()
    assert r["ok"] and r["steps"] == 2
    wfs = client.get("/api/workflows").json()
    wf = next(w for w in wfs if w["id"] == r["id"])
    assert wf["steps"][0]["action"] == "control" and wf["steps"][0]["params"]["action"] == "click"
    # empty save is rejected
    assert client.post("/api/macro/save", json={"name": "x", "steps": []}).json()["ok"] is False


def test_quality_api(client):
    """IDEA-6: record via API + read summary; snapshot endpoint runs the cheap health check."""
    rec = client.post("/api/quality", json={"suite": "unit", "score": 7, "total": 8}).json()
    assert rec["ok"] and rec["run"]["pct"] == 87.5
    q = client.get("/api/quality").json()
    assert any(s["suite"] == "unit" for s in q["summary"])
    snap = client.post("/api/quality/snapshot").json()
    assert snap["ok"] and "pct" in snap["run"]


def test_memory_api_crud(client):
    """IDEA-8: add → list → recall → delete a durable memory via the API."""
    add = client.post("/api/memory", json={"text": "I prefer concise answers", "pinned": True}).json()
    assert add["ok"] and add["item"]["id"]
    mid = add["item"]["id"]
    items = client.get("/api/memory").json()["items"]
    assert any(f["id"] == mid and f["pinned"] == 1 for f in items)
    hit = client.get("/api/memory", params={"q": "concise"}).json()["items"]
    assert any("concise" in f["text"] for f in hit)
    assert client.request("DELETE", f"/api/memory/{mid}").json()["ok"] is True
    assert all(f["id"] != mid for f in client.get("/api/memory").json()["items"])


def test_index_auto_cache_bust(client):
    html = client.get("/").text
    assert re.search(r"app\.css\?v=\d+", html)   # server-stamped asset version


def test_security_headers(client):
    """SEC-3: strict CSP + clickjacking/permissions headers present."""
    h = client.get("/").headers
    csp = h.get("content-security-policy", "")
    assert "default-src 'self'" in csp and "frame-ancestors 'self'" in csp and "object-src 'none'" in csp
    assert h.get("x-content-type-options") == "nosniff"
    assert "microphone=(self)" in h.get("permissions-policy", "")


def test_exec_destructive_confirm_guard(client, monkeypatch):
    """SEC-1: destructive commands require confirm; nothing executes without it."""
    import server
    calls = []
    class _Job: id = "job-test"
    monkeypatch.setattr(server.PM, "start", lambda *a, **k: (calls.append(a), _Job())[1])
    # safe command runs
    r = client.post("/api/exec", json={"command": "echo hello"})
    assert r.status_code == 200 and r.json().get("ok")
    base = len(calls)
    # destructive without confirm -> 409, NOT executed
    r = client.post("/api/exec", json={"command": "format C:"})
    assert r.status_code == 409 and r.json().get("needs_confirm")
    assert len(calls) == base
    # destructive WITH confirm -> executes
    r = client.post("/api/exec", json={"command": "format C:", "confirm": True})
    assert r.status_code == 200 and r.json().get("ok")
    assert len(calls) == base + 1
