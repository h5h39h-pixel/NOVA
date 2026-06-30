# -*- coding: utf-8 -*-
"""TST-1 — deeper per-service unit tests (real assertions). External services (Ollama/HTTP) are
mocked; the DB is the isolated temp DB from conftest. No live server / network required."""


def test_audit_writes(tmpdb):
    from nova.services.audit import audit
    from nova.core.db import db
    audit("tester", "did_thing", "some detail", "ok")
    c = db(); n = c.execute("SELECT COUNT(*) FROM audit WHERE actor='tester'").fetchone()[0]; c.close()
    assert n == 1


def test_add_notification_and_category(tmpdb):
    from nova.core.db import set_settings, db
    from nova.services.notifications import add_notification, _notif_category
    set_settings({"desktop_notifications": False})        # don't spawn a desktop toast in tests
    add_notification("info", "Training complete", "done")
    c = db(); r = c.execute("SELECT level,title,category FROM notifications ORDER BY id DESC LIMIT 1").fetchone(); c.close()
    assert r["title"] == "Training complete" and r["category"] == "training"
    assert _notif_category("Agent finished")[0] == "agent"
    assert _notif_category("Daily Briefing")[0] == "automation"
    assert _notif_category("something else")[0] == "system"


def test_metrics_history_roundtrip(tmpdb):
    from nova.services.metrics import set_last_metrics, get_last_metrics, record_history, history, collect_metrics
    m = collect_metrics()
    assert "cpu" in m and "ram_pct" in m and m["type"] == "metrics"
    set_last_metrics({"sentinel": 1})
    assert get_last_metrics() == {"sentinel": 1}
    record_history({"ts": 1.0, "cpu": 10, "ram_pct": 20, "gpu": {"util": 5, "vram_used": 1, "vram_total": 2, "temp": 40}})
    record_history({"ts": 2.0, "cpu": 11, "ram_pct": 21, "gpu": None})
    h = history()
    assert len(h) >= 2 and "gpu_util" in h[0] and h[-1]["cpu"] == 11


def test_conv_touch_and_count(tmpdb):
    from nova.services.chat import conv_ensure, chat_add, conv_touch, chat_count
    from nova.core.db import db
    cid = conv_ensure(title="New chat")
    conv_touch(cid, add_tokens=5, first_user="my first question goes here")
    c = db(); r = c.execute("SELECT tokens,title FROM conversations WHERE cid=?", (cid,)).fetchone(); c.close()
    assert r["tokens"] == 5 and r["title"] == "my first question goes here"[:48]
    chat_add(cid, "user", "hi")
    assert chat_count() >= 1


def test_run_schedule_updates_db(tmpdb):
    import json
    from nova.core.db import db, set_settings
    from nova.services.schedules import run_schedule
    set_settings({"desktop_notifications": False})
    c = db()
    c.execute("INSERT INTO schedules(name,action,params,interval_sec,next_run,enabled,created) VALUES(?,?,?,?,?,1,?)",
              ("t", "notify", json.dumps({"text": "hi"}), 0, 0, 0))
    c.commit()
    row = dict(c.execute("SELECT * FROM schedules ORDER BY id DESC LIMIT 1").fetchone()); c.close()
    assert run_schedule(row) == "notified"
    c = db(); r = c.execute("SELECT last_status FROM schedules WHERE id=?", (row["id"],)).fetchone(); c.close()
    assert r["last_status"] == "notified"


def test_run_action_webhook_and_kb(tmpdb, monkeypatch):
    import nova.services.schedules as S
    monkeypatch.setattr(S, "send_webhook", lambda *a, **k: None)
    assert S.run_action("webhook", {"title": "t", "text": "x"}, "n") == "webhook sent"
    monkeypatch.setattr(S, "kb_search", lambda q, k=4: [{"doc": "a", "text": "x", "score": 1.0}])
    assert S.run_action("kb_search", {"query": "hi"}, "n") == "kb search: 1 hits"


def test_backup_restore_roundtrip(tmp_path, monkeypatch, tmpdb):
    import nova.services.backup as B
    from nova.services.chat import conv_ensure
    from nova.core.db import db
    monkeypatch.setattr(B, "DS_BASE", tmp_path / "no_base.jsonl")       # isolate from real datasets
    monkeypatch.setattr(B, "DS_LEARNED", tmp_path / "no_learned.jsonl")
    monkeypatch.setattr(B, "rebuild_combined", lambda: 0)
    cid = conv_ensure(project="BK", title="hello")
    bundle = B.make_backup()
    assert bundle["version"] == 1 and any(cv["cid"] == cid for cv in bundle["conversations"])
    c = db(); c.execute("DELETE FROM conversations WHERE cid=?", (cid,)); c.commit(); c.close()
    added = B.restore_backup(bundle)
    assert added and added.get("conversations", 0) >= 1
    c = db(); n = c.execute("SELECT COUNT(*) FROM conversations WHERE cid=?", (cid,)).fetchone()[0]; c.close()
    assert n == 1
    assert B.restore_backup({"version": 99}) is None                   # unrecognized bundle


def test_ollama_models_mocked(monkeypatch):
    import nova.services.ollama as O
    def fake(url, **k):
        if url.endswith("/api/tags"): return {"models": [{"name": "qwen2.5:14b", "size": 9_000_000_000}]}
        if url.endswith("/api/ps"): return {"models": []}
        return {"capabilities": [], "details": {}}
    monkeypatch.setattr(O, "http_json", fake)
    O._caps_cache.clear()
    ms = O.ollama_models()
    assert len(ms) == 1 and ms[0]["name"] == "qwen2.5:14b"
    assert ms[0]["loaded"] is False and "size_gb" in ms[0] and isinstance(ms[0]["tags"], list)


def test_learning_stats_mocked(tmpdb, monkeypatch):
    import nova.services.training as T
    monkeypatch.setattr(T, "nova_installed", lambda: False)
    monkeypatch.setattr(T, "read_jsonl", lambda p: [])
    s = T.learning_stats()
    for key in ("base", "learned", "combined", "nova", "runs", "recommendations"):
        assert key in s
    assert s["nova"] is False and isinstance(s["recommendations"], list)
    assert T.training_history() == []


def test_extract_text(tmp_path):
    from nova.services.files import extract_text
    p = tmp_path / "x.txt"; p.write_text("hello world", encoding="utf-8")
    assert "hello world" in extract_text(p)
    q = tmp_path / "x.xyz"; q.write_text("z", encoding="utf-8")
    assert "unsupported" in extract_text(q).lower()
