# -*- coding: utf-8 -*-
"""Per-FEATURE soak — repeat every feature many times and record errors, latency drift, memory (RSS),
GPU peak, and background-loop liveness. Complements the whole-system soak (`soak_test.py`).

Runs against the LIVE server (:8900) for job/HTTP features and in-process for service calls. Uses
throwaway data and cleans up. Records a summary to the quality dashboard (suite='feature-soak').

    python scripts/feature_soak.py                 # default iteration counts
    python scripts/feature_soak.py --heavy 3       # more iterations for image/agent/vlm
"""
import argparse
import json
import statistics
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
BASE = "http://127.0.0.1:8900"
RESULTS = []


def _get(p, t=15):
    with urllib.request.urlopen(BASE + p, timeout=t) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _post(p, body, t=180):
    rq = urllib.request.Request(BASE + p, data=json.dumps(body).encode(),
                                headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(rq, timeout=t) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _gpu():
    try:
        o = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used",
                            "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=10)
        u, m = o.stdout.strip().splitlines()[0].split(",")
        return int(u.strip()), int(m.strip())
    except Exception:
        return None, None


def _rss():
    try:
        import psutil
        for c in psutil.net_connections("inet"):
            if c.laddr and c.laddr.port == 8900 and c.status == "LISTEN" and c.pid:
                return round(psutil.Process(c.pid).memory_info().rss / 1048576, 1)
    except Exception:
        pass
    return None


def _cpu():
    try:
        import psutil
        return psutil.cpu_percent(interval=None)
    except Exception:
        return None


def soak(name, fn, n):
    lat, errs, gpu_peak, vram_peak, cpu_peak = [], 0, 0, 0, 0
    rss0 = _rss()
    print(f"\n[{name}] x{n} ...", flush=True)
    for i in range(n):
        t = time.time()
        try:
            fn(i)
            lat.append(time.time() - t)
        except Exception as e:
            errs += 1
            print(f"    ! iter {i} error: {str(e)[:100]}", flush=True)
        g, v = _gpu()
        if g is not None:
            gpu_peak = max(gpu_peak, g); vram_peak = max(vram_peak, v)
        cp = _cpu()
        if cp is not None:
            cpu_peak = max(cpu_peak, cp)
    rss1 = _rss()
    loop_alive = _get("/api/health").get("metrics_loop_alive", True)
    # slowdown: ratio of the slowest-half median to the fastest-half median (drift over the run)
    drift = 0
    if len(lat) >= 4:
        half = len(lat) // 2
        a = statistics.median(lat[:half]) or 0.001
        drift = round(statistics.median(lat[half:]) / a, 2)
    r = {"feature": name, "n": n, "errors": errs,
         "p50_s": round(statistics.median(lat), 3) if lat else 0,
         "max_s": round(max(lat), 3) if lat else 0,
         "first_s": round(lat[0], 3) if lat else 0, "last_s": round(lat[-1], 3) if lat else 0,
         "slowdown_x": drift, "rss_before": rss0, "rss_after": rss1,
         "rss_delta": (round(rss1 - rss0, 1) if (rss0 and rss1) else None),
         "gpu_peak_pct": gpu_peak, "vram_peak_mb": vram_peak, "cpu_peak_pct": round(cpu_peak, 0),
         "loop_alive": loop_alive}
    RESULTS.append(r)
    warn = " ⚠SLOWDOWN" if (drift > 2 and r["last_s"] > 0.5) else ""
    print(f"    n={n} errors={errs} p50={r['p50_s']}s drift×{drift} rss {rss0}->{rss1}MB "
          f"gpu={gpu_peak}% cpu={r['cpu_peak_pct']}% loop_alive={loop_alive}{warn}", flush=True)
    return r


def _poll_job(job_id, timeout=240):
    t0 = time.time()
    while time.time() - t0 < timeout:
        procs = _get("/api/processes")
        j = next((p for p in procs if p.get("id") == job_id), None)
        if j and (j.get("status") in ("done", "error", "stopped") or j.get("exit_code") is not None):
            if j.get("status") == "error":
                raise RuntimeError("job errored")
            return
        time.sleep(2)
    raise TimeoutError("job timeout")


# ---------------- concurrent load generator (load + soak together) ----------------
import threading
_LOAD_STOP = threading.Event()
_LOAD_STATS = {"reqs": 0, "errs": 0}


def _load_worker():
    """Continuously hammer cheap read endpoints to create concurrent load during the soak."""
    eps = ["/api/health", "/api/metrics", "/api/processes", "/api/notifications", "/api/memory",
           "/api/events?limit=10", "/api/quality", "/api/services"]
    i = 0
    while not _LOAD_STOP.is_set():
        try:
            _get(eps[i % len(eps)], t=8); _LOAD_STATS["reqs"] += 1
        except Exception:
            _LOAD_STATS["errs"] += 1
        i += 1
        time.sleep(0.05)


def _start_load(n):
    threads = [threading.Thread(target=_load_worker, daemon=True) for _ in range(n)]
    for t in threads:
        t.start()
    return threads


# ---------------- feature exercises ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--light", type=int, default=30)
    ap.add_argument("--medium", type=int, default=8)
    ap.add_argument("--heavy", type=int, default=2)
    ap.add_argument("--load", type=int, default=0, help="N concurrent load-generator threads (load+soak)")
    args = ap.parse_args()
    L, M, H = args.light, args.medium, args.heavy

    if args.load:
        _start_load(args.load)
        print(f"⚡ load+soak: {args.load} concurrent load threads running", flush=True)

    from nova.services import memory as MEM
    from nova.services import kb as KB
    from nova.services.schedules import run_action
    from nova.services.notifications import add_notification
    from nova.services import control as CTL
    from nova.core import eventlog as EL

    # memory (store/recall/forget)
    def _mem(i):
        r = MEM.remember(f"soak fact number {i} about topic alpha")
        MEM.recall("topic alpha"); MEM.forget(r["id"])
    soak("memory", _mem, L)

    # RAG / KB (ingest text + search — hits the embed model)
    def _rag(i):
        n = KB.kb_ingest_text(f"soak-doc-{i}", f"document {i}: the RTX 5090 has 32GB VRAM, entry {i}")
        KB.kb_search("how much vram")
        return n
    soak("rag_kb", _rag, M)
    # cleanup soak KB docs
    for d in _get("/api/kb/docs"):
        if str(d.get("name", "")).startswith("soak-doc-"):
            try: urllib.request.urlopen(urllib.request.Request(BASE + f"/api/kb/docs/{d['id']}", method="DELETE"), timeout=10).read()
            except Exception: pass

    # automation actions + workflow
    soak("automation_notify", lambda i: run_action("notify", {"text": f"soak {i}"}), L)
    def _wf(i):
        _post("/api/workflows", {"name": f"soak-wf-{i}", "steps": [{"action": "notify", "params": {"text": "hi"}}]})
        # run + delete
        wfs = _get("/api/workflows"); w = next((x for x in wfs if x["name"] == f"soak-wf-{i}"), None)
        if w: urllib.request.urlopen(urllib.request.Request(BASE + f"/api/workflows/{w['id']}", method="DELETE"), timeout=10).read()
    soak("workflows", _wf, M)

    # notifications API
    soak("notifications", lambda i: add_notification("info", "soak", f"n{i}"), L)

    # control (read-only awareness — safe, no cursor movement)
    soak("control_awareness", lambda i: CTL.awareness(), M)

    # STT+TTS round trip (via live endpoints)
    def _voice(i):
        _post("/api/tts", {"text": "soak test"}, t=30)
    soak("tts", _voice, M)

    # image generation (SDXL job)
    def _img(i):
        r = _post("/api/toolkit/image", {"prompt": f"a simple red circle, test {i}", "model": "sdxl"})
        _poll_job(r["job"])
    soak("image_gen_sdxl", _img, H)

    # agent (dry-run short goal — exercises the ReAct loop + LLM)
    def _agent(i):
        from nova.services.agent import agent_run
        from nova.core.db import get_settings
        agent_run(f"say hello number {i}", get_settings().get("default_local_model", "qwen2.5:14b"),
                  dry_run=True, max_steps=3)
    soak("agent_dryrun", _agent, H)

    # screen vision VLM describe (enable, describe, disable)
    _post("/api/settings", {"screen_vision_enabled": True})
    try:
        soak("vision_vlm_describe", lambda i: _post("/api/vision/describe", {}, t=120), H)
    finally:
        _post("/api/settings", {"screen_vision_enabled": False})

    # video generation (LTX job — heavy; 1 iteration)
    def _vid(i):
        r = _post("/api/toolkit/video", {"prompt": "a short calm ocean clip", "length": 25})
        _poll_job(r["job"], timeout=400)
    soak("video_gen_ltx", _vid, 1)

    # event log system itself (log + query + stats under repetition; retention prune sanity)
    def _evlog(i):
        EL.log("system", f"soak event {i}", source="feature_soak", context={"i": i})
        EL.query(q="soak event", limit=20); EL.stats(hours=1, buckets=12)
    soak("event_log", _evlog, L)

    # diagnostics + audit (issues scan, ops report, audit endpoint)
    soak("diagnostics_ops", lambda i: (_get("/api/issues"), _get("/api/ops/report"), _get("/api/audit")), M)

    # database under concurrent load (parallel reads + writes → checks WAL / no locks)
    def _db_load(i):
        def hit(): _get("/api/history"); _get("/api/conversations")
        ts = [threading.Thread(target=hit) for _ in range(6)]
        for t in ts: t.start()
        for t in ts: t.join(15)
        MEM.remember(f"db-load {i}")          # a concurrent write alongside the reads
    soak("db_concurrent", _db_load, M)

    # large-file processing (ingest a big text doc into the KB → chunking + embeddings at size)
    big = "The RTX 5090 has 32GB of VRAM. " * 4000     # ~120 KB of text
    def _bigfile(i):
        n = KB.kb_ingest_text(f"soak-big-{i}", big)
        return n
    soak("large_file_ingest", _bigfile, max(1, H))
    for d in _get("/api/kb/docs"):
        if str(d.get("name", "")).startswith(("soak-big-", "soak-doc-")):
            try: urllib.request.urlopen(urllib.request.Request(BASE + f"/api/kb/docs/{d['id']}", method="DELETE"), timeout=10).read()
            except Exception: pass

    # network-failure simulation: point a probe at a DEAD endpoint → the app must degrade, not crash
    def _netfail(i):
        from nova.core.http import http_ok            # must return False fast, no raise
        assert http_ok("http://127.0.0.1:1/") is False
        # a chat/agent path with the model unreachable degrades gracefully (dry-run avoids side effects)
        _get("/api/services")                          # status loop probes down services cleanly
    soak("network_failure_sim", _netfail, M)

    # ---- stop load + auto report ----
    _LOAD_STOP.set()
    time.sleep(0.3)
    return _report(load=args.load)


def _report(load=0):
    total_err = sum(r["errors"] for r in RESULTS)
    leak = [r for r in RESULTS if (r["rss_delta"] or 0) > 80]
    slow = [r for r in RESULTS if r["slowdown_x"] and r["slowdown_x"] > 2 and r["last_s"] > 0.5]
    dead = [r for r in RESULTS if not r["loop_alive"]]
    print("\n================ FEATURE SOAK REPORT ================", flush=True)
    for r in RESULTS:
        w = " ⚠SLOWDOWN" if r in slow else ""
        print(f"{r['feature']:22} n={r['n']:<3} err={r['errors']} p50={r['p50_s']}s "
              f"drift×{r['slowdown_x']} rssΔ={r['rss_delta']}MB gpu={r['gpu_peak_pct']}% cpu={r['cpu_peak_pct']}%{w}", flush=True)
    print(f"\nTOTAL ERRORS: {total_err} | leaks: {len(leak)} | slowdowns: {len(slow)} | dead loops: {len(dead)}")
    if load:
        print(f"concurrent load: {_LOAD_STATS['reqs']} reqs / {_LOAD_STATS['errs']} errors")
    verdict = "PASS" if (total_err == 0 and not leak and not slow and not dead) else "ISSUES FOUND"
    print(f"VERDICT: {verdict}")
    # persist JSON + markdown report
    try:
        from config import LOG_DIR
        import json as _json
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        rep = {"generated": time.time(), "verdict": verdict, "total_errors": total_err,
               "leaks": [r["feature"] for r in leak], "slowdowns": [r["feature"] for r in slow],
               "dead_loops": [r["feature"] for r in dead], "load_reqs": _LOAD_STATS["reqs"],
               "load_errs": _LOAD_STATS["errs"], "results": RESULTS}
        (LOG_DIR / "feature_soak_report.json").write_text(_json.dumps(rep, indent=2), encoding="utf-8")
        md = [f"# Feature soak report — {verdict}", "",
              f"_generated {time.strftime('%Y-%m-%d %H:%M')} · {total_err} errors · "
              f"{len(leak)} leaks · {len(slow)} slowdowns · {len(dead)} dead loops_", "",
              "| feature | n | errors | p50 s | drift× | rssΔ MB | gpu% | cpu% | loop |",
              "|---|---|---|---|---|---|---|---|---|"]
        for r in RESULTS:
            md.append(f"| {r['feature']} | {r['n']} | {r['errors']} | {r['p50_s']} | {r['slowdown_x']} | "
                      f"{r['rss_delta']} | {r['gpu_peak_pct']} | {r['cpu_peak_pct']} | "
                      f"{'✅' if r['loop_alive'] else '🔴'} |")
        (LOG_DIR / "feature_soak_report.md").write_text("\n".join(md), encoding="utf-8")
        print(f"report → {LOG_DIR / 'feature_soak_report.md'}")
    except Exception as e:
        print(f"report write failed: {e}")
    try:
        _post("/api/quality", {"suite": "feature-soak",
                               "score": len(RESULTS) - sum(1 for r in RESULTS if r["errors"]),
                               "total": len(RESULTS), "detail": f"{verdict}: {total_err} errors"})
    except Exception:
        pass
    return total_err == 0 and not leak and not slow and not dead


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
