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
    monkeypatch.setattr(S.screen_svc, "read_screen", lambda vision=False: {"text": "Build SUCCEEDED on main"})
    assert "no match" in S.run_action("screen_if", {"match": "FAILED"})
    out = S.run_action("screen_if", {"match": "succeeded", "then_action": "notify", "then_params": {"text": "ok"}})
    assert out.startswith("matched") and "notify" in out
    assert "no 'match'" in S.run_action("screen_if", {})


def test_training_progress_json():
    from nova.services.training import _parse_train_sub
    sub = _parse_train_sub('... [PROGRESS] {"step": 40, "total": 120, "loss": 1.5} ...')
    assert sub and sub["step"] == 40 and sub["total"] == 120 and sub["percent"] == 33
