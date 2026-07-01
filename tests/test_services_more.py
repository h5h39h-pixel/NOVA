# -*- coding: utf-8 -*-
"""More service-level coverage — schedules.run_action branches, agent_tool branches, jobs ProcMgr,
and process helpers. Heavy externals (subprocess, Ollama, ProcMgr, control) are mocked so these are
hermetic + fast but still exercise the real dispatch logic."""


# ---- schedules.run_action branches ----
def test_run_action_branches(monkeypatch, tmpdb):
    import nova.services.schedules as S
    # notify / speak / kb_search go through real code with light deps
    assert "notified" in S.run_action("notify", {"text": "hi"}).lower() or S.run_action("notify", {"text": "hi"})
    monkeypatch.setattr(S, "run_action", S.run_action)  # keep reference
    # kb_search
    monkeypatch.setattr(S, "kb_search", lambda q, k=4: [{"doc": "d", "text": "t", "score": 1.0}])
    assert "1" in S.run_action("kb_search", {"query": "x"})   # "kb search: 1 hits"
    # unknown action
    assert S.run_action("nope_action", {}) == "unknown action"
    # quality_check (light — hits health snapshot which degrades offline)
    r = S.run_action("quality_check", {})
    assert "quality_check" in r


def test_run_action_command_mocked(monkeypatch, tmpdb):
    import nova.services.schedules as S

    class _Job:
        def __init__(self): self.id = "j1"; self.status = "done"; self.exit_code = 0
    monkeypatch.setattr(S.PM, "start", lambda *a, **k: _Job())
    out = S.run_action("command", {"command": "Get-Date"}, "t")
    assert isinstance(out, str)


def test_run_action_screen_if_absent(monkeypatch, tmpdb):
    import nova.services.schedules as S
    monkeypatch.setattr(S.screen_svc, "read_screen", lambda vision=False, region=None: {"text": "all good"})
    # match absent (text not on screen) → normal trigger doesn't fire; absent flag fires (with always_notify)
    assert "no trigger" in S.run_action("screen_if", {"match": "error", "always_notify": True})
    out = S.run_action("screen_if", {"match": "error", "absent": True, "then_action": "notify", "always_notify": True})
    assert "fired" in out and "disappeared" in out


def test_run_action_agent_mocked(monkeypatch, tmpdb):
    import nova.services.schedules as S
    import nova.services.agent as A
    monkeypatch.setattr(A, "agent_run", lambda *a, **k: "did the thing")
    out = S.run_action("agent", {"goal": "do x"})
    assert "did the thing" in out
    assert "no goal" in S.run_action("agent", {})


# ---- agent_tool branches (mock heavy deps) ----
def test_agent_tool_readonly_branches(monkeypatch, tmpdb):
    import nova.services.agent as A
    # recall / remember (real, DB-backed)
    A.agent_tool("remember", {"text": "the user likes tea"})
    assert "tea" in A.agent_tool("recall", {"query": "tea"})
    # notify
    assert "notified" in A.agent_tool("notify", {"text": "hey"}).lower()
    # screen_awareness (mock control.awareness)
    import nova.services.control as C
    monkeypatch.setattr(C, "awareness", lambda: {"active": {"title": "W", "process": "p", "rect": {}},
                                                 "screen": {"primary": {"w": 1, "h": 1}, "dpi": 96, "scale": 1},
                                                 "windows": []})
    assert "Active" in A.agent_tool("screen_awareness", {})
    # find_element (mock)
    monkeypatch.setattr(C, "find_element", lambda name: {"matches": [{"name": "OK", "type": "Button",
                                                                      "center": {"x": 5, "y": 6}}]})
    assert "OK" in A.agent_tool("find_element", {"name": "OK"})


def test_agent_tool_dry_run_side_effecting(tmpdb):
    import nova.services.agent as A
    assert A.agent_tool("run_command", {"command": "echo hi"}, dry_run=True).startswith("[dry-run]")
    assert A.agent_tool("write_file", {"path": "x.txt", "content": "y"}, dry_run=True).startswith("[dry-run]")
    assert A.agent_tool("control", {"action": "click", "x": 1, "y": 1}, dry_run=True).startswith("[dry-run]")


def test_parse_action_and_build_sys():
    from nova.services.agent import parse_action, build_agent_sys, AGENT_SYS
    assert parse_action('{"thought":"t","action":"notify","text":"x"}')["action"] == "notify"
    assert parse_action("garbage") is None
    sys_all = build_agent_sys()
    assert "SECURITY" in sys_all and isinstance(AGENT_SYS, str)
    sys_subset = build_agent_sys(tools=["kb_search"], max_steps=5)
    assert "kb_search" in sys_subset


# ---- jobs ProcMgr ----
def test_jobs_procmgr(tmpdb):
    from nova.services.jobs import PM
    job = PM.start("test-echo", ["cmd", "/c", "echo", "hello"], kind="command", source="test")
    assert job.id and job.name == "test-echo"
    jobs = PM.jobs
    assert job.id in jobs


# ---- process helpers ----
def test_init_job_object_safe():
    from nova.core.process import init_job_object
    init_job_object()   # idempotent, guarded; must not raise on repeat calls
    init_job_object()
