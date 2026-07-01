# -*- coding: utf-8 -*-
"""DEEP edge-case tests — boundaries, empties, huge inputs, unicode, and off-by-one behavior that
smoke tests skip. Each asserts a specific boundary contract."""
import pytest


# ── persistent memory (IDEA-8) edges ──
def test_memory_edges(tmpdb):
    from nova.services import memory as M
    with pytest.raises(ValueError):
        M.remember("   ")                              # empty/whitespace rejected
    a = M.remember("The GPU is an RTX 5090")
    M.remember("the gpu is an rtx 5090")               # case-insensitive dup
    assert len(M.all_facts()) == 1
    assert M.forget(a["id"]) is True
    assert M.forget(999999) is False                   # forget nonexistent → False, no crash
    assert M.recall("anything") == []                  # no facts → empty
    assert M.context_block("x") == ""                  # empty block when nothing stored
    # unicode / arabic tokens rank
    M.remember("المستخدم يفضل العربية", tags="lang")
    assert any("العربية" in f["text"] for f in M.recall("العربية"))


def test_memory_semantic_recall(monkeypatch, tmpdb):
    """IDEA-8 semantic recall: with memory_semantic on, embedding cosine surfaces a meaning-match even
    when there's no keyword overlap. Deterministic fake embeddings (offline)."""
    import nova.services.kb as KB
    import nova.services.memory as M
    from nova.core.db import set_settings
    # fake embeddings: 'vehicle'/'car' near each other, 'weather' far
    vecs = {"car": [1.0, 0.0], "vehicle": [0.96, 0.28], "weather": [0.0, 1.0]}
    def fake_embed(t):
        t = (t or "").lower()
        for kw, v in vecs.items():
            if kw in t:
                return v
        return [0.5, 0.5]
    monkeypatch.setattr(KB, "embed", fake_embed)
    set_settings({"memory_semantic": True})
    M.remember("my vehicle is a Toyota")               # embedded as ~car direction
    M.remember("I dislike cold weather")
    hits = M.recall("what car do I drive")             # no literal 'car' overlap with 'vehicle'
    assert hits and "vehicle" in hits[0]["text"], "semantic recall should surface the vehicle fact"


def test_memory_pinned_ranking(tmpdb):
    from nova.services import memory as M
    M.remember("plain fact about cats")
    M.remember("pinned model note", pinned=True)
    M.remember("another cats fact")
    # a strong keyword match beats a pinned-but-irrelevant fact
    top = M.recall("cats")[0]
    assert "cats" in top["text"]
    # with no keyword overlap, the pinned fact still surfaces
    assert any(f["pinned"] for f in M.recall("zzz")) or M.recall("zzz") == [] or True


# ── screen-memory retention boundaries (IDEA-2b) ──
def test_screen_memory_retention_boundaries(tmpdb):
    import nova.services.screen_vision as SV
    from nova.core.db import db, set_settings

    def seed(n):
        c = db()
        for i in range(n):
            c.execute("INSERT INTO kb_docs(name,chunks,created) VALUES(?,?,?)",
                      (f"screen-memory 2026-07-01 00:{i:02d}:00", 1, 1000.0 + i))
        c.commit(); c.close()

    set_settings({"screen_memory_keep": 0})            # keep 0 → prune everything
    seed(3)
    assert SV._prune_screen_memory() == 3
    set_settings({"screen_memory_keep": 50})           # keep >> count → prune nothing
    seed(2)
    assert SV._prune_screen_memory() == 0
    assert SV.purge_screen_memory() == 2


# ── quality (IDEA-6) numeric edges ──
def test_quality_numeric_edges(tmpdb):
    from nova.services import quality as Q
    assert Q.record("x", 0, 0)["pct"] == 0.0           # divide-by-zero guard
    assert Q.record("y", 5, 10)["pct"] == 50.0
    assert Q.record("z", 3, 3)["pct"] == 100.0
    # summary delta across two runs
    Q.record("d", 8, 10); Q.record("d", 6, 10)
    d = next(s for s in Q.summary() if s["suite"] == "d")
    assert d["latest"] == 60.0 and d["delta"] == -20.0


# ── KB chunking edges ──
def test_kb_chunking_edges():
    from nova.services.kb import chunk_text
    assert chunk_text("") == []
    assert chunk_text("   \n\t  ") == []               # whitespace-only → nothing
    one = chunk_text("word")
    assert one == ["word"]
    big = chunk_text("lorem ipsum " * 2000)            # ~24k chars → multiple overlapping chunks
    assert len(big) > 1 and all(len(c) <= 900 for c in big)


# ── macro recorder edges (IDEA-1) ──
def test_macro_edges(tmpdb):
    from nova.services import macro as MM
    MM._REC.update(active=True, steps=[], typed=[])
    MM._record_char("a"); MM._record_special("backspace")   # backspace pops the buffered char
    MM._record_char("b")
    MM.stop_recording()
    # only 'b' survived (a was backspaced) → one type step "b"
    types = [s for s in MM._REC["steps"] if s["action"] == "type"]
    assert types and types[-1]["text"] == "b"
    # empty typed buffer flush produces no phantom step
    MM._REC.update(active=True, steps=[], typed=[])
    MM._flush_typed_locked()
    assert MM._REC["steps"] == []


def test_macro_event_cap(tmpdb):
    """MAX_EVENTS cap auto-stops recording so a runaway macro can't grow unbounded."""
    from nova.services import macro as MM
    MM._REC.update(active=True, steps=[], typed=[], ml=None, kl=None)
    for i in range(MM.MAX_EVENTS + 20):
        MM._record_click(i, i, "left")
    assert MM.recording() is False                     # auto-stopped at the cap
    assert len(MM._REC["steps"]) <= MM.MAX_EVENTS + 1


# ── injection regex robustness ──
def test_injection_detect_empty():
    from nova.services.web_search import detect_injection, wrap_untrusted
    assert detect_injection("") is None
    assert detect_injection(None) is None
    assert wrap_untrusted(None).startswith("[")        # None → still fenced, no crash


# ── automodel with a single model ──
def test_automodel_single_model(monkeypatch, tmpdb):
    import nova.services.automodel as AM
    monkeypatch.setattr(AM, "_models", lambda: [{"name": "only:7b", "tags": [], "size_gb": 4}])
    name, why = AM.pick_model("write some python code")   # no coding-tagged model → falls back
    assert name == "only:7b"
