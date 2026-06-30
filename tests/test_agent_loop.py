# -*- coding: utf-8 -*-
"""TST-3 — agent ReAct loop integration tests with a MOCKED model.

We script `ollama_chat_once` to return canned JSON steps and capture the events the loop
emits + the observations it feeds back, verifying: JSON parsing, tool dispatch, final/stop/
step-budget termination, reformat recovery, tool gating, the `ask` path, and the
destructive-command / confined-write guards. No model, no network, no real side effects."""
import pytest


@pytest.fixture
def agent_env(monkeypatch):
    """Isolate the loop: capture push() events + the user-message fed back each turn,
    silence notifications/audit, and provide a .script([...]) helper to drive the model."""
    import nova.services.agent as A
    events, seen = [], []
    monkeypatch.setattr(A, "push", lambda e: events.append(e))
    monkeypatch.setattr(A, "add_notification", lambda *a, **k: None)
    monkeypatch.setattr(A, "audit", lambda *a, **k: None)
    A.AGENT_STOP.clear()

    def script(steps):
        it = iter(steps)
        def fake(model, msgs, temperature=0.2):
            seen.append(msgs[-1]["content"])
            try:
                return next(it)
            except StopIteration:
                return '{"thought":"end","final":"done"}'
        monkeypatch.setattr(A, "ollama_chat_once", fake)

    ns = type("Env", (), {})()
    ns.A, ns.events, ns.seen, ns.script = A, events, seen, script
    return ns


def _evs(events, ev):
    return [e for e in events if e.get("ev") == ev]


def test_parse_action():
    from nova.services.agent import parse_action
    assert parse_action('{"a":1}')["a"] == 1
    assert parse_action('thinking... {"action":"x","args":{"n":1}} trailing')["action"] == "x"
    assert parse_action('x {"a":{"b":2}} y')["a"]["b"] == 2          # nested braces
    assert parse_action("no json here") is None
    assert parse_action("{bad json}") is None                        # first {...} doesn't parse


def test_loop_tool_then_final(agent_env):
    agent_env.script(['{"thought":"notify","action":"notify","args":{"text":"hi"}}',
                      '{"thought":"done","final":"all set"}'])
    agent_env.A.agent_run("do it", "m", max_steps=5)
    ev = agent_env.events
    assert _evs(ev, "start") and _evs(ev, "action") and _evs(ev, "observation")
    assert _evs(ev, "action")[0]["action"] == "notify"
    assert _evs(ev, "observation")[0]["text"] == "user notified"
    assert _evs(ev, "final")[0]["text"] == "all set"
    assert ev[-1]["ev"] == "done"


def test_loop_reformats_bad_json(agent_env):
    agent_env.script(["this is not json", '{"thought":"x","final":"ok"}'])
    agent_env.A.agent_run("g", "m", max_steps=5)
    thoughts = [e["text"] for e in _evs(agent_env.events, "thought")]
    assert any("reformat" in t for t in thoughts)
    assert _evs(agent_env.events, "final")[0]["text"] == "ok"


def test_loop_step_budget(agent_env, monkeypatch):
    def always(model, msgs, temperature=0.2):
        agent_env.seen.append(msgs[-1]["content"])
        return '{"thought":"loop","action":"notify","args":{"text":"x"}}'
    monkeypatch.setattr(agent_env.A, "ollama_chat_once", always)
    agent_env.A.agent_run("g", "m", max_steps=2)
    assert len(_evs(agent_env.events, "action")) == 2                # never more than the budget
    assert "step limit" in _evs(agent_env.events, "final")[0]["text"].lower()


def test_loop_stop_mid_run(agent_env, monkeypatch):
    def model(m, ms, t=0.2):
        agent_env.seen.append(ms[-1]["content"])
        agent_env.A.AGENT_STOP.set()                                 # user hits Stop during the turn
        return '{"thought":"x","action":"notify","args":{"text":"y"}}'
    monkeypatch.setattr(agent_env.A, "ollama_chat_once", model)
    agent_env.A.agent_run("g", "m", max_steps=5)
    assert _evs(agent_env.events, "stopped")
    assert not _evs(agent_env.events, "observation")                 # stopped before dispatch
    agent_env.A.AGENT_STOP.clear()


def test_loop_tool_gating(agent_env):
    agent_env.script(['{"thought":"x","action":"run_command","args":{"command":"echo hi"}}',
                      '{"thought":"d","final":"done"}'])
    agent_env.A.agent_run("g", "m", max_steps=4, tools=["notify"])   # run_command not allowed
    fed_back = " ".join(agent_env.seen)
    assert "disabled for this run" in fed_back
    assert not _evs(agent_env.events, "action")                      # gated tool never dispatched


def test_loop_ask(agent_env):
    agent_env.script(['{"thought":"need info","action":"ask","args":{"text":"which file?"}}'])
    agent_env.A.agent_run("g", "m", max_steps=5)
    ask = _evs(agent_env.events, "ask")
    assert ask and ask[0]["text"] == "which file?"


def test_agent_tool_blocks_destructive(tmpdb):
    from nova.services.agent import agent_tool
    out = agent_tool("run_command", {"command": "Remove-Item -Recurse -Force C:\\data"})
    assert out.startswith("BLOCKED") and "destructive" in out
    dry = agent_tool("run_command", {"command": "Get-Date"}, dry_run=True)
    assert dry.startswith("[dry-run]")                               # safe cmd simulated, not run


def test_agent_tool_write_confined():
    from nova.services.agent import agent_tool
    out = agent_tool("write_file", {"path": "C:\\Windows\\x.txt", "content": "x"})
    assert out.startswith("BLOCKED")                                 # outside the safe output root


def test_agent_write_read_roundtrip(monkeypatch, tmp_path):
    """OUT-1 regression: a relative path (even one the model prefixes with 'agent-output/')
    must write to AND read back from the same place — no doubled directory, no CWD mismatch."""
    import nova.services.agent as A
    monkeypatch.setattr(A, "SAFE_WRITE_ROOT", tmp_path)
    w = A.agent_tool("write_file", {"path": "agent-output/note.txt", "content": "hello-42"})
    assert "wrote" in w
    assert (tmp_path / "note.txt").exists() and not (tmp_path / "agent-output").exists()
    assert "hello-42" in A.agent_tool("read_file", {"path": "note.txt"})
    assert "hello-42" in A.agent_tool("read_file", {"path": "agent-output/note.txt"})
