# -*- coding: utf-8 -*-
"""Automation engine — the action dispatcher (`run_action`) shared by schedules, workflows,
and the agent; scheduled-task execution; multi-step workflow runner; and A/B model testing.

`run_action` is the single place that turns an (action, params) pair into real work
(commands, video, harvest/retrain jobs, browse, screen record, notify, webhook, briefing,
speak, KB search/index). The daily-briefing generator lives in the insights layer, so it's
injected here via `set_briefing_hook()` to avoid a forward dependency. Depends on nova.core
(db/events/process) + nova.services (jobs/audit/notifications/browser/kb/ollama/screen) + config."""
import json
import time
import threading
import subprocess
from pathlib import Path
from config import TOOLKIT, TRAIN_DIR
from nova.core.db import db
from nova.core.events import push
from nova.core.process import ps_args, _q
from nova.services.audit import audit
from nova.services.notifications import add_notification, send_webhook
from nova.services.jobs import PM
from nova.services.browser import browse
from nova.services.kb import kb_search, kb_ingest_file
from nova.services.ollama import ollama_chat_once
from nova.services import screen as screen_svc

# Daily-briefing generator is injected by server (it lives in the insights layer).
_briefing_hook = None
def set_briefing_hook(fn):
    global _briefing_hook
    _briefing_hook = fn


def run_action(action, params, name="task"):
    """Execute one automation action; returns a short status string."""
    p = params or {}
    if action == "command":
        PM.start(f"⏰ {name}", ps_args(p.get("command", "")), kind="scheduled", source="schedule"); return "started command"
    if action == "video":
        prompt = p.get("prompt", "a cinematic shot")
        cmd = '& "{}" "{}"'.format(TOOLKIT / "genvideo.ps1", prompt.replace('"', '`"'))
        if p.get("ckpt"): cmd += ' -Ckpt "{}"'.format(p["ckpt"])
        if p.get("steps"): cmd += ' -Steps {}'.format(int(p["steps"]))
        PM.start(f"⏰ video: {prompt[:30]}", ps_args(cmd), kind="video", source="schedule"); return "started video"
    if action == "harvest":
        PM.start(f"⏰ {name}", ["python", str(TRAIN_DIR / "harvest_chats.py")], kind="scheduled", source="schedule"); return "harvest started"
    if action == "retrain":
        PM.start(f"⏰ {name}", ps_args(f'& "{TRAIN_DIR / "learn.ps1"}"'), kind="training", source="schedule"); return "retrain started"
    if action == "browse":
        try:
            r = browse(p.get("url", ""), fill=p.get("fill"), click=p.get("click"), wait=p.get("wait"))
            add_notification("success", "Browser", f"Opened {r.get('title') or p.get('url')}", link=r.get("screenshot"))
            return f"browsed: {r.get('title')}"
        except Exception as e:
            return f"browse error: {e}"
    if action == "screen_record":
        secs = max(1, min(int(p.get("seconds", 10)), 600))
        r = screen_svc.RECORDER.start(p.get("mode", "full"))
        if r.get("ok"):
            threading.Timer(secs, lambda: screen_svc.RECORDER.stop()).start()
            return f"recording screen for {secs}s"
        return r.get("error", "record failed")
    if action == "notify":
        add_notification("info", name, p.get("text", "")); return "notified"
    if action == "webhook":
        send_webhook(p.get("title", name), p.get("text", ""), "info"); return "webhook sent"
    if action == "briefing":
        text = _briefing_hook()["text"][:600] if _briefing_hook else "(briefing unavailable)"
        add_notification("info", "Daily Briefing", text); return "briefing generated"
    if action == "speak":
        subprocess.Popen(ps_args(f'& "{TOOLKIT / "speak.ps1"}" {_q(p.get("text",""))}'),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); return "spoke"
    if action == "kb_search":
        n = len(kb_search(p.get("query", ""), 4)); return f"kb search: {n} hits"
    if action == "kb_index":
        folder = Path(p.get("folder", ""))
        if not folder.exists(): return f"folder not found: {folder}"
        c = db(); have = {r[0] for r in c.execute("SELECT name FROM kb_docs").fetchall()}; c.close()
        exts = {".txt", ".md", ".pdf", ".docx", ".json", ".csv", ".log", ".py", ".js", ".ps1"}
        added = 0
        for f in folder.iterdir():
            if f.is_file() and f.suffix.lower() in exts and f.name not in have:
                if kb_ingest_file(f) > 0: added += 1
        add_notification("success", "KB indexed", f"{added} new files from {folder.name}")
        return f"indexed {added} new files from {folder}"
    if action == "screen_if":
        # Conditional screen trigger: if `match` text appears on screen, run `then_action`.
        # Use as a schedule (e.g., every 60s) for "if X on screen → do Y".
        want = (p.get("match") or "").strip().lower()
        if not want: return "screen_if: no 'match' text configured"
        try:
            r = screen_svc.read_screen(bool(p.get("vision")))
            text = (r.get("text") or "").lower()
        except Exception as e:
            return f"screen_if: read failed ({e})"
        if want in text:
            ta = p.get("then_action", "notify")
            tp = p.get("then_params") or {"text": f"Screen matched: {p.get('match')}"}
            st = run_action(ta, tp, name)
            return f"matched '{p.get('match')}' → {ta}: {st}"
        return f"no match for '{p.get('match')}'"
    return "unknown action"


def run_schedule(row):
    try:
        status = run_action(row["action"], json.loads(row["params"] or "{}"), row["name"])
    except Exception as e:
        status = f"error: {e}"
    c = db()
    nxt = (time.time() + row["interval_sec"]) if row["interval_sec"] and row["interval_sec"] > 0 else None
    c.execute("UPDATE schedules SET last_run=?, last_status=?, next_run=?, enabled=? WHERE id=?",
              (time.time(), status, nxt, 1 if nxt else 0, row["id"]))
    c.commit(); c.close()
    audit("automation", row["action"], f"{row['name']}: {status}", "fail" if str(status).startswith("error") else "ok")
    push({"type": "schedule_ran", "id": row["id"], "status": status})
    return status


def wf_start_job(action, p, name):
    """Start a job-type action and return its Job (for waiting); None for sync actions."""
    if action == "command": return PM.start(f"🔗 {name}", ps_args(p.get("command", "")), kind="workflow", source="workflow")
    if action == "harvest": return PM.start(f"🔗 {name}", ["python", str(TRAIN_DIR / "harvest_chats.py")], kind="workflow", source="workflow")
    if action == "retrain": return PM.start(f"🔗 {name}", ps_args(f'& "{TRAIN_DIR / "learn.ps1"}"'), kind="training", source="workflow")
    if action == "video":
        prompt = p.get("prompt", "a cinematic shot")
        cmd = '& "{}" "{}"'.format(TOOLKIT / "genvideo.ps1", prompt.replace('"', '`"'))
        if p.get("steps"): cmd += ' -Steps {}'.format(int(p["steps"]))
        return PM.start(f"🔗 video: {prompt[:24]}", ps_args(cmd), kind="video", source="workflow")
    return None


def run_workflow(wid):
    c = db(); row = c.execute("SELECT * FROM workflows WHERE id=?", (wid,)).fetchone(); c.close()
    if not row: return
    name = row["name"]; steps = json.loads(row["steps"] or "[]")
    push({"type": "workflow", "ev": "start", "id": wid, "name": name, "n": len(steps)})
    ok = True
    for i, step in enumerate(steps):
        a = step.get("action"); p = step.get("params", {})
        push({"type": "workflow", "ev": "step", "id": wid, "i": i, "action": a, "state": "running"})
        try:
            job = wf_start_job(a, p, name)
            if job:
                t0 = time.time()
                while job.status in ("starting", "running") and time.time() - t0 < 1200:
                    time.sleep(2)
                st = job.status + (f" (exit {job.exit_code})" if job.exit_code not in (0, None) else "")
                if job.status == "error": ok = False
            else:
                st = run_action(a, p, name)
        except Exception as e:
            st = f"error: {e}"; ok = False
        push({"type": "workflow", "ev": "step", "id": wid, "i": i, "action": a, "state": "done", "status": st})
        if not ok: break
    c = db(); c.execute("UPDATE workflows SET last_run=?, last_status=? WHERE id=?",
                        (time.time(), "completed" if ok else "failed", wid)); c.commit(); c.close()
    push({"type": "workflow", "ev": "done", "id": wid, "ok": ok})
    audit("workflow", "run", name, "ok" if ok else "fail")
    add_notification("success" if ok else "error", f"Workflow {name} {'completed' if ok else 'failed'}", "")


def abtest_run(a, bmodel, prompts, judge):
    push({"type": "abtest", "ev": "start", "a": a, "b": bmodel, "n": len(prompts), "judge": judge})
    wins = {a: 0, bmodel: 0, "tie": 0}
    for i, pr in enumerate(prompts):
        try: ra = ollama_chat_once(a, [{"role": "user", "content": pr}], 0.3)
        except Exception as e: ra = f"[error: {e}]"
        try: rb = ollama_chat_once(bmodel, [{"role": "user", "content": pr}], 0.3)
        except Exception as e: rb = f"[error: {e}]"
        verdict = None
        if judge:
            jp = (f"You are an impartial judge. Question:\n{pr}\n\nAnswer A:\n{ra}\n\nAnswer B:\n{rb}\n\n"
                  "Which answer is better? Reply with exactly one of: A, B, TIE — then a brief reason.")
            try: jt = ollama_chat_once(judge, [{"role": "user", "content": jp}], 0.0)
            except Exception as e: jt = f"TIE ({e})"
            v = jt.strip().upper()
            winner = a if v.startswith("A") else bmodel if v.startswith("B") else "tie"
            wins[winner] = wins.get(winner, 0) + 1
            verdict = {"winner": winner, "raw": jt[:200]}
        push({"type": "abtest", "ev": "result", "i": i, "prompt": pr, "a": ra, "b": rb, "verdict": verdict})
    push({"type": "abtest", "ev": "done", "wins": wins})
    add_notification("success", "A/B test complete", f"{a} vs {bmodel}")
