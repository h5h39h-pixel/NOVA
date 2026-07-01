# -*- coding: utf-8 -*-
"""DEEP failure-injection tests — what happens when things GO WRONG: services down, bad input,
malformed data, oversized input, degraded dependencies. Assert graceful degradation, never a crash
or a 500 the user can't understand."""


# ── dependency down: embeddings / Ollama unreachable ──
def test_embed_failure_degrades(monkeypatch, tmpdb):
    import nova.services.kb as KB

    def boom(*a, **k):
        raise ConnectionError("ollama down")
    monkeypatch.setattr(KB, "http_json", boom)
    assert KB.embed("hello") == []                     # no crash → empty embedding
    assert KB.kb_search("anything") == []              # search degrades to no results
    assert KB.kb_ingest_text("doc", "some text") == 0  # ingest with no embeddings → 0 chunks


def test_http_ok_unreachable_is_false():
    from nova.core.http import http_ok
    assert http_ok("http://127.0.0.1:1/") is False     # connection refused → False, fast, no raise


# ── malformed agent action JSON ──
def test_agent_parse_action_malformed():
    from nova.services.agent import parse_action
    assert parse_action("no json here") is None
    assert parse_action('{"thought": "x", "action": ') is None   # truncated JSON
    assert parse_action('prefix {"action":"notify","text":"hi"} suffix')["action"] == "notify"


# ── bad/empty request bodies → clean errors, not 500s ──
def test_bad_bodies_are_clean(client):
    # quality: non-numeric score
    r = client.post("/api/quality", json={"suite": "x", "score": "abc", "total": 1}).json()
    assert r["ok"] is False and "number" in r["error"].lower()
    # memory: empty text
    r = client.post("/api/memory", json={"text": ""}).json()
    assert r["ok"] is False
    # macro save: no steps
    r = client.post("/api/macro/save", json={"name": "x", "steps": []}).json()
    assert r["ok"] is False
    # kb ingest-folder: missing folder
    r = client.post("/api/kb/ingest-folder", json={}).json()
    assert r["ok"] is False


def test_agent_save_workflow_empty_goal(client):
    r = client.post("/api/agent/save-workflow", json={"goal": "   "})
    assert r.status_code == 400


# ── oversized input handling ──
def test_history_output_truncated(tmpdb):
    from nova.core.db import add_history, db
    add_history("cmd", 0, 0.1, "X" * 50000, "terminal")   # 50k output
    c = db(); row = c.execute("SELECT output FROM history ORDER BY id DESC LIMIT 1").fetchone(); c.close()
    assert len(row["output"]) <= 4000                     # capped, not unbounded


def test_memory_recall_caps(tmpdb):
    from nova.services import memory as M
    for i in range(40):
        M.remember(f"fact number {i} about topic")
    hits = M.recall("topic")
    assert len(hits) <= M.MAX_INJECT                      # recall never floods the prompt


# ── guard degrades safely if settings read fails ──
def test_protected_foreground_survives_settings_error(monkeypatch, tmpdb):
    import nova.services.control as C
    import nova.core.db as dbm
    monkeypatch.setattr(C, "_foreground_title", lambda: "notepad")
    def boom(): raise RuntimeError("db gone")
    monkeypatch.setattr(dbm, "get_settings", boom)
    # must not raise — falls back to the default protected list against a safe title → None
    assert C.protected_foreground() is None


# ── destructive check on empty input ──
def test_danger_reason_empty():
    from nova.core.safety import danger_reason, is_dangerous
    assert danger_reason("") is None
    assert danger_reason(None) is None
    assert is_dangerous("") is False


# ── understand blocks credential paths (agent tool) ──
def test_agent_understand_blocks_credentials(tmpdb):
    from nova.services.agent import agent_tool
    out = agent_tool("understand", {"path": r"C:\Users\me\.ssh\id_rsa"}, dry_run=True)
    assert "BLOCKED" in out
