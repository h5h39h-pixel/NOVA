# -*- coding: utf-8 -*-
"""Training & continuous learning — owns both the dataset corpus (base/learned/combined
JSONL, deduped on (user, assistant) pairs) and the fine-tune job lifecycle: start a
harvest/retrain run as a tracked ProcMgr job, pause/resume/stop it (works even for an
orphaned run after a server restart), parse live progress from the training log, compute
learning stats, and record each completed run. `record_training_run` self-registers as the
ProcMgr training hook at import. Depends on nova.core (db/http/process/events) +
nova.services (jobs/audit/notifications/metrics) + config."""
import re
import json
import time
import subprocess
import psutil
from config import DS_BASE, DS_LEARNED, DS_COMBINED, TRAIN_DIR, TRAIN_LOG, TRAIN_REPORT, OLLAMA
from nova.core.db import db
from nova.core.http import http_json
from nova.core.process import ps_args
from nova.core.events import push
from nova.services.audit import audit
from nova.services.notifications import add_notification
from nova.services.jobs import PM, set_training_hook
from nova.services.metrics import get_last_metrics

# Nova's persona — the system message stamped onto every learned training example.
NOVA_SYSTEM = ("You are Nova, a helpful bilingual (Arabic/English) AI assistant running locally on the "
               "user's Windows 11 PC with an RTX 5090. You are an expert in their AI Control Center, "
               "Ollama, ComfyUI/LTX-Video, PowerShell, and local toolkit. Be concise and practical.")


def read_jsonl(p):
    out = []
    if p.exists():
        for ln in p.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln:
                try: out.append(json.loads(ln))
                except Exception: pass
    return out


def ex_key(ex):
    msgs = ex.get("messages", [])
    u = next((m["content"] for m in msgs if m["role"] == "user"), "")
    a = next((m["content"] for m in msgs if m["role"] == "assistant"), "")
    return " ".join(u.split()).lower() + "||" + " ".join(a.split()).lower()


def rebuild_combined():
    seen, combined = set(), []
    for ex in read_jsonl(DS_BASE) + read_jsonl(DS_LEARNED):
        k = ex_key(ex)
        if k in seen: continue
        seen.add(k); combined.append(ex)
    DS_COMBINED.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in combined) + "\n", encoding="utf-8")
    return len(combined)


def append_learned(user, assistant):
    user, assistant = (user or "").strip(), (assistant or "").strip()
    if len(user) < 2 or len(assistant) < 2: return None
    ex = {"messages": [{"role": "system", "content": NOVA_SYSTEM},
                       {"role": "user", "content": user},
                       {"role": "assistant", "content": assistant}]}
    existing = {ex_key(e) for e in read_jsonl(DS_LEARNED) + read_jsonl(DS_BASE)}
    if ex_key(ex) in existing: return False
    with open(DS_LEARNED, "a", encoding="utf-8") as f:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    rebuild_combined()
    return True


# ============================ training job lifecycle ============================
TRAIN_STEPS = 7


def nova_installed():
    try: return any(m["name"].startswith("nova-local") for m in http_json(f"{OLLAMA}/api/tags").get("models", []))
    except Exception: return False


def training_status():
    report = TRAIN_REPORT.read_text(encoding="utf-8", errors="replace") if TRAIN_REPORT.exists() else ""
    return {
        "base": len(read_jsonl(DS_BASE)),
        "learned": len(read_jsonl(DS_LEARNED)),
        "combined": len(read_jsonl(DS_COMBINED)),
        "nova_installed": nova_installed(),
        "report": report,
        "merged_exists": (TRAIN_DIR / "merged" / "config.json").exists(),
    }


def training_log(lines=120):
    if not TRAIN_LOG.exists(): return {"log": ""}
    tail = TRAIN_LOG.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:]
    return {"log": "\n".join(tail)}


def harvest():
    try:
        out = subprocess.run(["python", str(TRAIN_DIR / "harvest_chats.py")],
                             capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace")
        line = next((l for l in out.stdout.splitlines() if l.startswith("RESULT")), out.stdout[-200:])
        add_notification("success", "Harvest complete", line)
        return {"ok": True, "result": line,
                "learned": len(read_jsonl(DS_LEARNED)), "combined": len(read_jsonl(DS_COMBINED))}
    except Exception as e:
        add_notification("error", "Harvest failed", str(e))
        return {"ok": False, "error": str(e)}


def active_training_job():
    """The training job that is starting / running / paused (None if none active)."""
    for j in PM.jobs.values():
        if j.kind == "training" and j.status in ("running", "starting", "paused"):
            return j
    return None


def last_training_job():
    jobs = [j for j in PM.jobs.values() if j.kind == "training"]
    return jobs[-1] if jobs else None


# --- control that also works for an ORPHANED run (e.g. server was restarted mid-training) ---
_orphan_paused = False
_orphan_cache = {"t": 0.0, "val": False}


def _training_procs():
    """Find the live training processes by command line (survives a server restart)."""
    found = []
    try:
        for p in psutil.process_iter(["pid", "cmdline"]):
            try: cl = " ".join(p.info.get("cmdline") or []).lower()
            except Exception: continue
            if "train_lora.py" in cl or "run_all.ps1" in cl or "learn.ps1" in cl:
                found.append(p)
    except Exception: pass
    return found


def has_training_procs():
    return bool(_training_procs())


def _expand(procs):
    seen = {}
    for p in procs:
        try:
            seen[p.pid] = p
            for c in p.children(recursive=True): seen[c.pid] = c
        except Exception: pass
    return list(seen.values())


def training_pause():
    global _orphan_paused
    j = active_training_job()
    if j and not j.paused: return PM.pause(j.id)
    procs = _expand(_training_procs())
    n = 0
    for p in procs:
        try: p.suspend(); n += 1
        except Exception: pass
    if n: _orphan_paused = True
    return n > 0


def training_resume():
    global _orphan_paused
    j = active_training_job()
    if j and j.paused: return PM.resume(j.id)
    procs = _expand(_training_procs())
    n = 0
    for p in procs:
        try: p.resume(); n += 1
        except Exception: pass
    _orphan_paused = False
    return n > 0


def training_stop():
    global _orphan_paused
    j = active_training_job()
    if j:
        if j.paused:
            try: PM.resume(j.id)
            except Exception: pass
        return PM.stop(j.id)
    killed = False
    for p in _training_procs():
        try: subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True); killed = True
        except Exception: pass
    _orphan_paused = False
    return killed


def start_retrain():
    """Start the one-click Harvest & Retrain job. Returns the Job; caller guards on active."""
    job = PM.start("Harvest & Retrain (learn.ps1)",
                   ps_args(f'& "{TRAIN_DIR / "learn.ps1"}"'), kind="training", source="training")
    audit("training", "retrain", "Harvest & Retrain")
    add_notification("info", "Harvest & Retrain started", "watch the Training Studio log")
    return job


def _hms(s):
    p = [int(x) for x in s.split(":")]
    return p[0]*60 + p[1] if len(p) == 2 else p[0]*3600 + p[1]*60 + p[2]


_PROG_JSON_RE = re.compile(r"\[PROGRESS\]\s+(\{.*?\})")
_PROG_RE = re.compile(r"\[PROGRESS\]\s+step=(\d+)\s+total=(\d+)(?:\s+epoch=([\d.]+))?(?:\s+loss=([\d.]+|nan|None))?(?:\s+elapsed=(\d+))?(?:\s+eta=(\d+))?")
_TQDM_RE = re.compile(r"(\d+)/(\d+)\s*\[(\d+:\d+(?::\d+)?)<(\d+:\d+(?::\d+)?)")


def _parse_train_sub(text):
    """Sub-progress inside the LoRA training step. Preference order: structured
    `[PROGRESS] {json}` → `[PROGRESS] step=… total=…` → tqdm fallback (ignoring the
    dataset-map and checkpoint-shard bars so their counts never read as training steps)."""
    sub = None
    # 1) preferred: structured JSON, e.g. [PROGRESS] {"step":40,"total":120,"loss":1.2}
    for m in _PROG_JSON_RE.finditer(text):
        try:
            j = json.loads(m.group(1))
            if isinstance(j, dict) and "step" in j and "total" in j:
                sub = {"step": int(j["step"]), "total": int(j["total"]),
                       "epoch": j.get("epoch"), "loss": j.get("loss"),
                       "elapsed": j.get("elapsed"), "eta": j.get("eta")}
        except Exception:
            pass
    # 2) key=value form
    for m in _PROG_RE.finditer(text):
        loss = m.group(4)
        sub = {"step": int(m.group(1)), "total": int(m.group(2)),
               "epoch": float(m.group(3)) if m.group(3) else None,
               "loss": (float(loss) if loss and loss not in ("nan", "None") else None),
               "elapsed": int(m.group(5)) if m.group(5) else None,
               "eta": int(m.group(6)) if m.group(6) else None}
    if sub is None:
        # legacy fallback: only the real training region, excluding map/checkpoint bars
        s = text.rfind("starting LoRA training")
        region = text[s:] if s >= 0 else text
        cut = region.find("adapter saved")
        if cut >= 0: region = region[:cut]
        for ln in region.splitlines():
            if "Map:" in ln or "checkpoint shards" in ln or "Generating" in ln or "examples/s" in ln:
                continue
            m2 = _TQDM_RE.search(ln)
            if m2 and int(m2.group(2)) > 1:
                sub = {"step": int(m2.group(1)), "total": int(m2.group(2)), "epoch": None,
                       "loss": None, "elapsed": _hms(m2.group(3)), "eta": _hms(m2.group(4))}
    if sub and sub.get("total"):
        sub["percent"] = round(sub["step"] / sub["total"] * 100)
    return sub


def progress():
    """Live training progress: pipeline step, LoRA sub-progress, ETA, GPU, status."""
    lj = last_training_job()
    tracked_active = bool(lj and lj.status in ("running", "starting", "paused"))
    step, name, complete = 0, "", False
    text = ""; log_fresh = False
    if TRAIN_LOG.exists():
        try:
            log_fresh = (time.time() - TRAIN_LOG.stat().st_mtime) < 180
            data = TRAIN_LOG.read_bytes()[-262144:]   # last 256KB is plenty (avoids huge reads)
            text = data.decode("utf-8", errors="replace")
        except Exception:
            text = ""
        i = text.rfind("OVERNIGHT TRAINING RUN START")
        if i >= 0: text = text[i:]   # only the current/latest run
        for ln in text.splitlines():
            if "==== STEP:" in ln:
                try:
                    seg = ln.split("STEP:")[1].split("====")[0].strip()
                    step = int(seg.split(".")[0]); name = seg
                except Exception: pass
            if "RUN COMPLETE" in ln: complete = True
    # orphan scan is expensive (process_iter) — gate by log state AND cache for a few seconds
    orphan = False
    if not tracked_active and not complete and log_fresh and step > 0:
        now = time.time()
        if now - _orphan_cache["t"] > 15:   # TTL longer than the scan cost, so polls hit cache
            _orphan_cache["val"] = bool(_training_procs()); _orphan_cache["t"] = now
        orphan = _orphan_cache["val"]
    running = bool(lj and lj.status in ("running", "starting")) or (orphan and not _orphan_paused)
    paused = bool(lj and lj.status == "paused") or (orphan and _orphan_paused)
    sub = _parse_train_sub(text) if step == 5 else None
    # overall percent: steps 1-4/6-7 each 1/7, step 5 interpolated by sub-progress
    if complete and not running and not paused:
        pct = 100
    else:
        done = max(0, step - 1)
        frac = (sub["step"] / sub["total"]) if (step == 5 and sub and sub.get("total")) else 0
        pct = round(min(done + frac, TRAIN_STEPS) / TRAIN_STEPS * 100)
    if paused: status = "paused"
    elif running: status = "running"
    elif lj and lj.status == "stopped": status = "stopped"
    elif complete: status = "completed"
    elif lj and lj.status == "error": status = "error"
    else: status = "idle"
    err = ""
    if status == "error":
        for ln in reversed(text.splitlines()):
            if "ERROR" in ln or "FATAL" in ln or "Traceback" in ln: err = ln[-200:]; break
    return {"running": running, "paused": paused, "status": status,
            "step": step, "total": TRAIN_STEPS, "name": name, "percent": pct,
            "complete": complete and not running, "train": sub,
            "gpu": (get_last_metrics() or {}).get("gpu"), "error": err,
            "job_id": lj.id if lj else None}


def learning_stats():
    base, learned, combined = len(read_jsonl(DS_BASE)), len(read_jsonl(DS_LEARNED)), len(read_jsonl(DS_COMBINED))
    c = db(); runs = [dict(r) for r in c.execute("SELECT * FROM training_runs ORDER BY id DESC LIMIT 10").fetchall()]; c.close()
    last = runs[0] if runs else None
    new_since = max(0, combined - (last["combined"] if last else 0))
    nova = nova_installed()
    recs = []
    if not nova: recs.append("Train your first model in Training Studio to create nova-local.")
    if new_since >= 10: recs.append(f"You have {new_since} new examples since the last training — retrain to bank the gains.")
    if learned < 30: recs.append("Use RAG chat and tap 👍 on helpful answers to grow your dataset.")
    if not recs: recs.append("Looking good — keep using RAG and retrain weekly to compound improvements.")
    return {"base": base, "learned": learned, "combined": combined, "nova": nova, "runs": runs,
            "new_since_last": new_since, "last_trained": last["ended"] if last else None, "recommendations": recs}


def training_history(limit=20):
    c = db(); rows = [dict(r) for r in c.execute("SELECT * FROM training_runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]; c.close()
    return rows


def upload_dataset(raw):
    """Append JSONL training examples from an uploaded file; dedupe + rebuild combined."""
    added, bad = 0, 0
    existing = {ex_key(e) for e in read_jsonl(DS_LEARNED) + read_jsonl(DS_BASE)}
    with open(DS_LEARNED, "a", encoding="utf-8") as out:
        for ln in raw.splitlines():
            ln = ln.strip()
            if not ln: continue
            try:
                ex = json.loads(ln)
                if "messages" not in ex: raise ValueError
                k = ex_key(ex)
                if k in existing: continue
                existing.add(k); out.write(json.dumps(ex, ensure_ascii=False) + "\n"); added += 1
            except Exception: bad += 1
    total = rebuild_combined()
    add_notification("success", "Dataset uploaded", f"+{added} examples ({bad} skipped)")
    return {"ok": True, "added": added, "skipped": bad, "learned": len(read_jsonl(DS_LEARNED)), "combined": total}


def record_training_run(job, started, dur):
    base, learned, comb = len(read_jsonl(DS_BASE)), len(read_jsonl(DS_LEARNED)), len(read_jsonl(DS_COMBINED))
    ok_steps = TRAIN_LOG.read_text(encoding="utf-8", errors="replace").count(": OK ----") if TRAIN_LOG.exists() else 0
    note = "completed" if job.exit_code == 0 else f"exit {job.exit_code}"
    c = db()
    c.execute("INSERT INTO training_runs(started,ended,ok,steps,base,learned,combined,note) VALUES(?,?,?,?,?,?,?,?)",
              (started, time.time(), 1 if job.exit_code == 0 else 0, ok_steps, base, learned, comb, note))
    c.commit(); c.close()
    push({"type": "training_done"})


set_training_hook(record_training_run)   # ProcMgr calls this when a training job ends
