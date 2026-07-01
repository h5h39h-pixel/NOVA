# -*- coding: utf-8 -*-
"""Tests for the five reliability features: session replay (#1), anomaly alerts (#2),
dry-run diff/preview (#3), resource budget per agent run (#4). (#5 backup-restore drill lives in
tests/test_backup_restore.py.) Each test runs against the autouse temp DB from conftest."""
import time
import json

from nova.core import eventlog
from nova.services import replay, preview, anomaly


# ── #3 dry-run diff / preview ────────────────────────────────────────────────
def test_preview_create_new_file(tmp_path):
    p = tmp_path / "brand_new.txt"
    r = preview.preview_action("write_file", {"path": str(p), "content": "hello\nworld\n"})
    assert r["kind"] == "create"
    assert "CREATE" in r["will"]


def test_preview_overwrite_shows_diff(tmp_path):
    p = tmp_path / "exists.txt"
    p.write_text("line1\nline2\nline3\n", encoding="utf-8")
    r = preview.preview_action("write_file", {"path": str(p), "content": "line1\nCHANGED\nline3\n"})
    assert r["kind"] == "overwrite"
    assert r["added"] >= 1 and r["removed"] >= 1
    assert "CHANGED" in r["diff"]


def test_preview_flags_destructive_command():
    r = preview.preview_action("run_command", {"command": "Remove-Item -Recurse -Force C:\\data"})
    assert r["kind"] == "command"
    assert r["destructive"] is True


def test_preview_benign_command_not_flagged():
    r = preview.preview_action("run_command", {"command": "Get-Date"})
    assert r["destructive"] is False


def test_preview_delete_reports_target(tmp_path):
    p = tmp_path / "gone.txt"; p.write_text("x", encoding="utf-8")
    r = preview.preview_action("delete_file", {"path": str(p)})
    assert "DELETE" in r["will"]
    r2 = preview.preview_action("delete_file", {"path": str(tmp_path / "missing.txt")})
    assert "not found" in r2["will"]


# ── #1 session replay ────────────────────────────────────────────────────────
def _seed_run(run_id, goal="test goal", final="done"):
    eventlog.log("agent", goal, source="agent.goal", actor="agent",
                 context={"run_id": run_id, "step": 0, "kind": "goal"})
    eventlog.log("agent", "thinking", source="agent.thought", actor="agent",
                 context={"run_id": run_id, "step": 1, "kind": "thought"})
    eventlog.log("agent", "run_command {}", source="agent.action", actor="agent",
                 context={"run_id": run_id, "step": 1, "kind": "action"})
    eventlog.log("agent", final, source="agent.final", actor="agent",
                 context={"run_id": run_id, "step": 999, "kind": "final"})


def test_replay_lists_and_reconstructs_run():
    _seed_run("abc123def456", goal="do the thing", final="finished ok")
    runs = replay.list_runs(limit=10)
    ids = [r["run_id"] for r in runs]
    assert "abc123def456" in ids
    row = next(r for r in runs if r["run_id"] == "abc123def456")
    assert row["goal"] == "do the thing"
    assert row["final"] == "finished ok"
    assert row["steps"] >= 4

    detail = replay.get_run("abc123def456")
    assert detail["goal"] == "do the thing"
    assert detail["final"] == "finished ok"
    kinds = [s["kind"] for s in detail["steps"]]
    assert kinds[0] == "goal" and kinds[-1] == "final"   # chronological order


def test_replay_isolates_runs():
    _seed_run("run_one_aaaa", goal="one")
    _seed_run("run_two_bbbb", goal="two")
    d1 = replay.get_run("run_one_aaaa")
    assert d1["goal"] == "one"
    assert all("run_two" not in json.dumps(s) for s in d1["steps"])


# ── #2 anomaly alerts ────────────────────────────────────────────────────────
def test_anomaly_detects_error_spike():
    anomaly._last_alert.clear()
    for i in range(anomaly._ERROR_SPIKE + 2):
        eventlog.log("error", f"boom {i}", level="error", source="test")
    found = anomaly.check_anomalies()
    kinds = [f["kind"] for f in found]
    assert "error_spike" in kinds


def test_anomaly_error_spike_is_throttled():
    anomaly._last_alert.clear()
    for i in range(anomaly._ERROR_SPIKE + 2):
        eventlog.log("error", f"boom {i}", level="error", source="test")
    first = anomaly.check_anomalies()
    assert any(f["kind"] == "error_spike" for f in first)
    # immediate re-check must be silent (cooldown)
    second = anomaly.check_anomalies()
    assert not any(f["kind"] == "error_spike" for f in second)


def test_anomaly_quiet_when_healthy():
    anomaly._last_alert.clear()
    # a couple of errors, well under the spike threshold
    eventlog.log("error", "one-off", level="error", source="test")
    found = anomaly.check_anomalies()
    assert not any(f["kind"] == "error_spike" for f in found)


# ── #4 resource budget per agent run ─────────────────────────────────────────
def test_agent_token_budget_stops_run(monkeypatch):
    from nova.core.db import set_settings
    from nova.services import agent
    set_settings({"agent_max_tokens": 1, "agent_max_seconds": 0})

    # model keeps proposing a (disallowed→no-op) action, never finishing; token budget must cut it off.
    def fake_chat(model, msgs, temperature):
        return json.dumps({"thought": "keep going", "action": "run_command",
                           "args": {"command": "echo hi"}})
    monkeypatch.setattr(agent, "ollama_chat_once", fake_chat)

    final = agent.agent_run("loop forever", "fake-model", max_steps=10, tools=["recall"])
    assert isinstance(final, str)
    assert "token budget" in final.lower()


def test_agent_time_budget_stops_run(monkeypatch):
    from nova.core.db import set_settings
    from nova.services import agent
    set_settings({"agent_max_seconds": 1, "agent_max_tokens": 0})

    def slow_chat(model, msgs, temperature):
        time.sleep(1.2)
        return json.dumps({"thought": "slow", "action": "run_command", "args": {"command": "echo hi"}})
    monkeypatch.setattr(agent, "ollama_chat_once", slow_chat)

    final = agent.agent_run("slow loop", "fake-model", max_steps=10, tools=["recall"])
    assert "time budget" in final.lower()
