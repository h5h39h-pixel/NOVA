# -*- coding: utf-8 -*-
"""Unit tests — nova/services (chat, settings, training, ollama, kb, backup, schedules)."""


def test_chat_store(tmpdb):
    from nova.services.chat import conv_ensure, chat_add, conv_messages, conv_clear
    cid = conv_ensure(project="T", title="hi")
    chat_add(cid, "user", "hello"); chat_add(cid, "assistant", "hi there")
    msgs = conv_messages(cid)
    assert len(msgs) == 2 and msgs[0]["role"] == "user" and msgs[1]["content"] == "hi there"
    conv_clear(cid)
    assert conv_messages(cid) == []


def test_settings_service(tmpdb):
    from nova.services.settings import _hash, _redact, exec_allowed, verify_login
    from nova.core.db import set_settings
    assert _hash("a") == _hash("a") and len(_hash("a")) == 64
    r = _redact({"auth_token": "x", "auth_token_hash": "y", "cloud_api_key": "k", "mode": "auto"})
    assert "auth_token" not in r and "auth_token_hash" not in r
    assert r["cloud_api_key"] == "***" and r["mode"] == "auto"
    # localhost → exec allowed
    assert exec_allowed() is True
    # exposed on LAN without opt-in → blocked; with opt-in → allowed
    set_settings({"auth_enabled": True, "lan_access": True, "allow_remote_exec": False})
    assert exec_allowed() is False
    set_settings({"allow_remote_exec": True})
    assert exec_allowed() is True
    # token login
    set_settings({"auth_enabled": True, "auth_token_hash": _hash("secret"), "auth_token": ""})
    assert verify_login("secret") and not verify_login("nope")


def test_secretbox_roundtrip(tmp_path, monkeypatch):
    import nova.core.secretbox as sb
    monkeypatch.setattr(sb, "_KEY_FILE", tmp_path / ".nova_key")
    monkeypatch.setattr(sb, "_fernet", None)
    enc = sb.encrypt_secret("sk-secret-123")
    assert enc.startswith("enc:") and "sk-secret-123" not in enc
    assert sb.decrypt_secret(enc) == "sk-secret-123"
    assert sb.encrypt_secret("") == ""                                   # empty passes through
    assert sb.decrypt_secret("plaintext-legacy") == "plaintext-legacy"  # legacy plaintext untouched


def test_settings_encrypts_cloud_key(tmp_path, monkeypatch, tmpdb):
    import nova.core.secretbox as sb
    from nova.services.settings import settings_save, get_cloud_api_key
    from nova.core.db import get_settings
    monkeypatch.setattr(sb, "_KEY_FILE", tmp_path / ".nova_key")
    monkeypatch.setattr(sb, "_fernet", None)
    settings_save({"cloud_api_key": "sk-live-xyz"})
    assert get_settings()["cloud_api_key"].startswith("enc:")   # stored encrypted at rest
    assert get_cloud_api_key() == "sk-live-xyz"                 # decrypts transparently for use


def test_training_datasets(tmp_path, monkeypatch, tmpdb):
    import nova.services.training as T
    monkeypatch.setattr(T, "DS_BASE", tmp_path / "b.jsonl")
    monkeypatch.setattr(T, "DS_LEARNED", tmp_path / "l.jsonl")
    monkeypatch.setattr(T, "DS_COMBINED", tmp_path / "c.jsonl")
    assert T.append_learned("hello there friend", "general kenobi") is True
    assert T.append_learned("hello there friend", "general kenobi") is False   # dedup
    assert T.append_learned("a", "b") is None                                  # too short
    assert T.rebuild_combined() == 1
    assert len(T.read_jsonl(tmp_path / "l.jsonl")) == 1


def test_ollama_tags(monkeypatch):
    import nova.services.ollama as O
    monkeypatch.setattr(O, "model_caps", lambda n: ([], ""))   # name-based tags only
    assert "coding" in O.model_tags("qwen2.5-coder:7b")
    assert "vision" in O.model_tags("qwen2.5vl:7b")
    assert O.model_tags("nomic-embed-text") == ["embedding"]


def test_kb_chunk_text():
    from nova.services.kb import chunk_text
    chunks = chunk_text("word " * 500)
    assert len(chunks) >= 1 and all(isinstance(x, str) and x for x in chunks)
    assert chunk_text("") == []


def test_kb_ingest_folder(tmp_path, monkeypatch, tmpdb):
    """IDEA-5: folder Q&A indexes supported files, skips unsupported + credential stores."""
    import nova.services.kb as KB
    monkeypatch.setattr(KB, "embed", lambda t: [0.1, 0.2, 0.3])   # no Ollama needed
    d = tmp_path / "docs"; d.mkdir()
    (d / "a.txt").write_text("alpha content about gpus", encoding="utf-8")
    (d / "b.md").write_text("beta notes on training", encoding="utf-8")
    (d / "ignore.bin").write_bytes(b"\x00\x01")                   # unsupported → skipped
    (d / ".env").write_text("SECRET=x", encoding="utf-8")         # credential → skipped

    res = KB.kb_ingest_folder(str(d))
    assert res["ok"] and res["indexed"] == 2 and res["chunks"] >= 2
    assert res["skipped"] >= 2
    # the indexed text is now searchable
    hits = KB.kb_search("gpus")
    assert any("alpha" in h["text"] for h in hits)

    bad = KB.kb_ingest_folder(str(tmp_path / "nope"))
    assert bad["ok"] is False


def test_kb_ingest_text(monkeypatch, tmpdb):
    import nova.services.kb as KB
    monkeypatch.setattr(KB, "embed", lambda t: [0.1, 0.2])
    n = KB.kb_ingest_text("note 1", "the quick brown fox jumps")
    assert n >= 1
    assert any("fox" in h["text"] for h in KB.kb_search("fox"))
    assert KB.kb_ingest_text("empty", "") == 0


def test_screen_memory_gate(monkeypatch, tmpdb):
    """IDEA-2: screen memory is strictly opt-in; when on it OCRs and indexes into the KB."""
    import nova.services.screen_vision as SV
    import nova.services.kb as KB
    from nova.core.db import set_settings
    monkeypatch.setattr(KB, "embed", lambda t: [0.3, 0.4])
    # OFF by default → refused
    r = SV.remember_screen()
    assert r["ok"] is False and "off" in r["error"].lower()
    # ON → OCR (mocked) text is indexed
    set_settings({"screen_memory_enabled": True})
    monkeypatch.setattr(SV.screen_svc, "read_screen",
                        lambda **k: {"ok": True, "text": "Visual Studio Code - main.py open", "mode": "ocr"})
    r = SV.remember_screen()
    assert r["ok"] and r["stored"] and r["chunks"] >= 1
    assert any("main.py" in h["text"] for h in KB.kb_search("which file was open"))


def test_control_macro_action(monkeypatch, tmpdb):
    """IDEA-1 (replay): a workflow `control` step dispatches to the control service (macro replay)."""
    import nova.services.schedules as SCH
    import nova.services.control as C
    import nova.services.settings as SET
    monkeypatch.setattr(SET, "exec_allowed", lambda: True)
    calls = []
    monkeypatch.setattr(C, "click", lambda x=None, y=None, button="left", double=False: calls.append(("click", x, y)) or "ok")
    monkeypatch.setattr(C, "set_element_text", lambda name, text: calls.append(("set_text", name, text)) or "ok")
    r1 = SCH.run_action("control", {"action": "click", "x": 100, "y": 200})
    r2 = SCH.run_action("control", {"action": "set_text", "name": "Search", "text": "hi"})
    assert "control click" in r1 and "control set_text" in r2
    assert ("click", 100, 200) in calls and ("set_text", "Search", "hi") in calls
    assert "unknown action" in SCH.run_action("control", {"action": "fly"})


def test_quality_record_and_summary(tmpdb):
    """IDEA-6: scored runs persist; summary reports latest + delta vs the previous run."""
    from nova.services import quality as Q
    Q.record("agent", 8, 10, "battery v1")          # 80%
    Q.record("agent", 9, 10, "battery v2")          # 90%
    Q.record("rag", 11, 12)                          # 91.7%
    hist = Q.history("agent")
    assert len(hist) == 2 and hist[0]["pct"] == 90.0   # newest first
    summ = {s["suite"]: s for s in Q.summary()}
    assert summ["agent"]["latest"] == 90.0 and summ["agent"]["delta"] == 10.0
    assert summ["rag"]["latest"] == 91.7 and summ["rag"]["delta"] is None  # only one run
    assert Q.record("x", 0, 0)["pct"] == 0.0          # no divide-by-zero


def test_screen_if_region_and_absent(monkeypatch, tmpdb):
    """IDEA-7: screen_if supports a pinned region + an inverted (absent) trigger."""
    import nova.services.schedules as SCH
    monkeypatch.setattr(SCH.screen_svc, "read_screen",
                        lambda vision=False, region=None: {"ok": True, "text": "Error: disk full on C:"})
    # present + normal → triggers
    r = SCH.run_action("screen_if", {"match": "disk full", "then_action": "notify"})
    assert "matched" in r and "notify" in r
    # present + absent flag → does NOT trigger
    r = SCH.run_action("screen_if", {"match": "disk full", "absent": True})
    assert "no trigger" in r
    # missing text + absent flag → triggers (the watched thing vanished)
    r = SCH.run_action("screen_if", {"match": "loading...", "absent": True, "then_action": "notify"})
    assert "vanished" in r
    # region is passed through + validated
    r = SCH.run_action("screen_if", {"match": "disk full", "region": [0, 0, 100, 50]})
    assert "in region" in r
    r = SCH.run_action("screen_if", {"match": "x", "region": "bad"})
    assert "must be [x,y,w,h]" in r


def test_screen_memory_retention(monkeypatch, tmpdb):
    """IDEA-2b: screen memory keeps only the newest N docs and purge removes all."""
    import nova.services.screen_vision as SV
    from nova.core.db import db, set_settings
    set_settings({"screen_memory_keep": 3})
    # seed 5 screen-memory docs with increasing created times
    c = db()
    for i in range(5):
        c.execute("INSERT INTO kb_docs(name,chunks,created) VALUES(?,?,?)",
                  (f"screen-memory 2026-06-30 10:0{i}:00", 1, 1000.0 + i))
    c.execute("INSERT INTO kb_docs(name,chunks,created) VALUES(?,?,?)", ("real-doc.txt", 1, 1.0))  # not screen-mem
    c.commit(); c.close()
    pruned = SV._prune_screen_memory()
    assert pruned == 2                                   # 5 → keep 3 → 2 removed
    c = db(); n = c.execute("SELECT COUNT(*) FROM kb_docs WHERE name LIKE 'screen-memory %'").fetchone()[0]; c.close()
    assert n == 3
    removed = SV.purge_screen_memory()
    assert removed == 3
    c = db()
    assert c.execute("SELECT COUNT(*) FROM kb_docs WHERE name LIKE 'screen-memory %'").fetchone()[0] == 0
    assert c.execute("SELECT COUNT(*) FROM kb_docs WHERE name='real-doc.txt'").fetchone()[0] == 1  # untouched
    c.close()


def test_backup_snapshot(tmp_path, monkeypatch, tmpdb):
    import os
    import nova.services.backup as B
    monkeypatch.setattr(B, "DB_PATH", tmpdb)
    monkeypatch.setattr(B, "BACKUP_DIR", tmp_path / "backups")
    p = B.snapshot_db(keep=5)
    assert os.path.exists(p)
    assert len(B.list_snapshots()) == 1


def test_make_backup_bundle(tmpdb):
    from nova.services.backup import make_backup
    b = make_backup()
    assert b["version"] == 1 and "conversations" in b and "kb_docs" in b
    assert "auth_token" not in b["settings"]   # secrets excluded from bundle


def test_screen_lang_allowlist():
    """SEC-6: OCR lang must be allowlisted (no shell injection via /api/screen/read)."""
    from nova.services.screen import _valid_lang
    assert _valid_lang("eng") and _valid_lang("ara") and _valid_lang("eng+ara")
    assert not _valid_lang("eng; Remove-Item C:\\x")
    assert not _valid_lang("eng -Command calc")
    assert not _valid_lang("") and not _valid_lang(None)


def test_run_action(tmpdb):
    from nova.services.schedules import run_action
    assert run_action("notify", {"text": "hi"}, "t") == "notified"
    assert run_action("bogus", {}) == "unknown action"


def test_screen_if_trigger(tmpdb, monkeypatch):
    import nova.services.schedules as S
    monkeypatch.setattr(S.screen_svc, "read_screen", lambda vision=False, region=None: {"text": "Build SUCCEEDED on main"})
    assert "no trigger" in S.run_action("screen_if", {"match": "FAILED"})
    out = S.run_action("screen_if", {"match": "succeeded", "then_action": "notify", "then_params": {"text": "ok"}})
    assert out.startswith("matched") and "notify" in out
    assert "no 'match'" in S.run_action("screen_if", {})


def test_training_progress_json():
    from nova.services.training import _parse_train_sub
    sub = _parse_train_sub('... [PROGRESS] {"step": 40, "total": 120, "loss": 1.5} ...')
    assert sub and sub["step"] == 40 and sub["total"] == 120 and sub["percent"] == 33


def test_memory_remember_recall_forget(tmpdb):
    """IDEA-8: durable facts persist, de-dupe, rank by keyword overlap, pin first, and delete."""
    from nova.services import memory as M
    a = M.remember("The operator prefers English explanations")
    M.remember("the operator prefers english explanations")     # case-insensitive dup → no growth
    M.remember("The GPU is an RTX 5090", tags="hardware")
    M.remember("Default chat model is qwen2.5:14b", pinned=True)
    assert len(M.all_facts()) == 3                                # dup collapsed

    hits = M.recall("which gpu do I have")
    assert hits and "RTX 5090" in hits[0]["text"]                 # keyword overlap surfaces the GPU fact

    pinned_first = M.recall("anything")
    assert pinned_first[0]["pinned"] == 1                         # pinned fact always ranks first

    block = M.context_block("english")
    assert "English explanations" in block

    assert M.forget(a["id"]) is True
    assert all(f["id"] != a["id"] for f in M.all_facts())
