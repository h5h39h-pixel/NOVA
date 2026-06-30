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
