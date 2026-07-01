# -*- coding: utf-8 -*-
"""Network-failure simulation — disconnect external services (Ollama/ComfyUI/web) and verify the
system DEGRADES gracefully (no crash, clean empties/False), then reconnect and verify RECOVERY."""


def test_http_ok_down_then_up(monkeypatch):
    import nova.core.http as H
    # simulate every probe failing
    monkeypatch.setattr(H.urllib.request, "urlopen", lambda *a, **k: (_ for _ in ()).throw(OSError("down")))
    assert H.http_ok("http://127.0.0.1:11434/api/tags") is False       # degrades to False, no raise


def test_embeddings_down_degrades_and_recovers(monkeypatch, tmpdb):
    import nova.services.kb as KB
    # DISCONNECT: embeddings endpoint unreachable
    def boom(*a, **k):
        raise ConnectionError("ollama unreachable")
    monkeypatch.setattr(KB, "http_json", boom)
    assert KB.embed("hello") == []                     # no crash
    assert KB.kb_search("anything") == []              # search degrades to empty
    assert KB.kb_ingest_text("doc", "text") == 0       # ingest with no embeddings → 0 chunks
    # RECONNECT: embeddings back
    monkeypatch.setattr(KB, "http_json", lambda *a, **k: {"embedding": [0.1, 0.2, 0.3]})
    assert KB.embed("hello") == [0.1, 0.2, 0.3]        # recovers
    assert KB.kb_ingest_text("doc2", "the gpu has vram") >= 1


def test_web_search_offline(monkeypatch):
    import ddgs

    class Dead:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def text(self, *a, **k): raise OSError("no network")
    monkeypatch.setattr(ddgs, "DDGS", Dead)
    from nova.services.web_search import web_search, web_context
    assert web_search("anything") == []                # offline → empty, no crash
    block, src = web_context("anything")
    assert block == "" and src == []


def test_status_snapshot_all_services_down(monkeypatch, tmpdb):
    import server
    import nova.core.http
    monkeypatch.setattr(server, "http_ok", lambda url, **k: False)      # every service down
    monkeypatch.setattr(nova.core.http, "http_ok", lambda url, **k: False)
    st = server._status_snapshot()                     # the status loop's work must not raise
    assert st["ollama"] is False and st["comfy"] is False and st["owui"] is False


def test_agent_llm_unreachable_degrades(monkeypatch, tmpdb):
    """If the model is unreachable mid-run, the agent returns an error string — it does not crash."""
    import nova.services.agent as A
    monkeypatch.setattr(A, "ollama_chat_once", lambda *a, **k: (_ for _ in ()).throw(OSError("model down")))
    out = A.agent_run("do something", "qwen2.5:14b", dry_run=True, max_steps=2)
    assert isinstance(out, str)                         # returns cleanly, no exception
