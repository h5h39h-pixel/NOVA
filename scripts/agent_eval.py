# -*- coding: utf-8 -*-
"""OUT-1 — agent goal battery. Run a fixed set of SAFE, verifiable goals through the real
agent loop (real model, real tools) and measure the true multi-step success rate, then write
a dated baseline to docs/agent-baseline.md.

This is OUTCOME verification, not a unit test: it answers "does the agent actually accomplish
goals end-to-end?" — which the mocked-model tests (TST-3) deliberately cannot. Results are
model- and run-dependent; the point is an honest, repeatable baseline.

Usage:  python scripts/agent_eval.py [--model qwen2.5:14b] [--steps 6] [--write-doc]
Requires Ollama running locally with the chosen model.
"""
import argparse
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import nova.services.agent as A  # noqa: E402

USER = os.environ.get("USERNAME", "")


def _combined(events, final):
    obs = " ".join(str(e.get("text", "")) for e in events if e.get("ev") == "observation")
    return (str(final or "") + " " + obs)


# ---- battery: each goal has safe tools + a verifiable success check ----
def _check_write(ev, final):
    p = A.SAFE_WRITE_ROOT / "eval1.txt"
    return p.exists() and "NOVA-OK-7731" in p.read_text(encoding="utf-8", errors="replace")


def _check_read(ev, final):
    return "TOKEN-4F9A2" in _combined(ev, final)


def _check_multi(ev, final):
    p = A.SAFE_WRITE_ROOT / "eval5.txt"
    return p.exists() and "42" in p.read_text(encoding="utf-8", errors="replace") and "42" in (final or "")


BATTERY = [
    {"id": "write_file", "tools": ["write_file"], "steps": 4,
     "goal": "Create a text file named eval1.txt in your output folder containing exactly the text "
             "NOVA-OK-7731 and nothing else. Then finish.",
     "check": _check_write},
    {"id": "arithmetic", "tools": ["run_command"], "steps": 4,
     "goal": "Use a single PowerShell command to compute 17 * 23, then tell me the numeric result.",
     "check": lambda ev, final: "391" in _combined(ev, final)},
    {"id": "username", "tools": ["run_command"], "steps": 4,
     "goal": "Find the current Windows user name by running a PowerShell command, then report it.",
     "check": lambda ev, final: bool(USER) and USER in _combined(ev, final)},
    {"id": "read_file", "tools": ["read_file"], "steps": 4,
     "goal": "Read the file eval_secret.txt in your output folder and tell me the token it contains.",
     "check": _check_read},
    {"id": "multi_step", "tools": ["write_file", "read_file"], "steps": 6,
     "goal": "First write the number 42 into a file called eval5.txt in your output folder. "
             "Then read that file back and tell me what number it contains.",
     "check": _check_multi},
]


def _prep():
    A.SAFE_WRITE_ROOT.mkdir(parents=True, exist_ok=True)
    for f in ("eval1.txt", "eval5.txt"):
        (A.SAFE_WRITE_ROOT / f).unlink(missing_ok=True)
    (A.SAFE_WRITE_ROOT / "eval_secret.txt").write_text("TOKEN-4F9A2", encoding="utf-8")


def run_goal(task, model, max_steps):
    events = []
    orig_push, orig_notify = A.push, A.add_notification
    A.push = lambda e: events.append(e)
    A.add_notification = lambda *a, **k: None
    t = time.time()
    err = None
    try:
        A.agent_run(task["goal"], model, dry_run=False, unrestricted=False,
                    max_steps=min(max_steps, task["steps"]), tools=task["tools"])
    except Exception as e:
        err = str(e)
    finally:
        A.push, A.add_notification = orig_push, orig_notify
    dt = time.time() - t
    finals = [e.get("text", "") for e in events if e.get("ev") == "final"]
    final = str(finals[-1]) if finals else ""              # model may return final as a number
    steps = len([e for e in events if e.get("ev") == "action"])
    obs = " | ".join(str(e.get("text", ""))[:120] for e in events if e.get("ev") == "observation")
    try:
        ok = bool(task["check"](events, final)) and not err
    except Exception as e:
        ok, err = False, f"checker error: {e}"
    return {"id": task["id"], "ok": ok, "steps": steps, "secs": round(dt, 1),
            "final": final[:200], "obs": obs[:300], "err": err}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen2.5:14b")
    ap.add_argument("--steps", type=int, default=6)
    ap.add_argument("--write-doc", action="store_true")
    args = ap.parse_args()

    _prep()
    print(f"Agent goal battery - model={args.model}  goals={len(BATTERY)}\n")
    results = []
    for task in BATTERY:
        r = run_goal(task, args.model, args.steps)
        results.append(r)
        print(f"[{'PASS' if r['ok'] else 'FAIL'}] {r['id']:<12} steps={r['steps']} {r['secs']}s"
              + (f"  ERR={r['err']}" if r['err'] else ""))
        print(f"        final: {r['final']}")
        if not r['ok']:
            print(f"        obs:   {r['obs']}")

    passed = sum(1 for r in results if r["ok"])
    rate = round(100 * passed / len(results)) if results else 0
    print(f"\n=== BASELINE: {passed}/{len(results)} ({rate}%) goals achieved with {args.model} ===")

    if args.write_doc:
        ts = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
        lines = [
            "# Agent success baseline (OUT-1)", "",
            f"_Generated by `scripts/agent_eval.py` on {ts} — model **{args.model}**._", "",
            "Real end-to-end runs of the agent loop against fixed, verifiable goals (safe tools only). "
            "This is outcome verification, not a unit test — numbers are model- and run-dependent.", "",
            f"**Result: {passed}/{len(results)} ({rate}%) goals achieved.**", "",
            "| Goal | Result | Steps | Time | Final (truncated) |",
            "|---|---|---|---|---|",
        ]
        for r in results:
            fin = r["final"].replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {r['id']} | {'✅' if r['ok'] else '❌'} | {r['steps']} | {r['secs']}s | {fin} |")
        lines += [
            "",
            "> First baseline (2026-06-30) scored **2/5** and exposed a real bug: relative `write_file` "
            "paths prefixed with `agent-output/` nested a doubled directory, and `read_file` resolved "
            "relative paths against the process CWD instead of the output folder — so the agent could not "
            "read back files it wrote. Fixed in M54 (`_strip_output_prefix` + `resolve_read_path`); the "
            "battery then scored 5/5.",
            "",
            "Re-run: `python scripts/agent_eval.py --model <name> --write-doc`.", ""]
        (ROOT / "docs" / "agent-baseline.md").write_text("\n".join(lines), encoding="utf-8")
        print("wrote docs/agent-baseline.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
