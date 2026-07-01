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


def soak(name, fn, n):
    lat, errs, gpu_peak, vram_peak = [], 0, 0, 0
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
    rss1 = _rss()
    loop_alive = _get("/api/health").get("metrics_loop_alive", True)
    r = {"feature": name, "n": n, "errors": errs,
         "p50_s": round(statistics.median(lat), 2) if lat else 0,
         "max_s": round(max(lat), 2) if lat else 0,
         "first_s": round(lat[0], 2) if lat else 0, "last_s": round(lat[-1], 2) if lat else 0,
         "rss_before": rss0, "rss_after": rss1,
         "rss_delta": (round(rss1 - rss0, 1) if (rss0 and rss1) else None),
         "gpu_peak_pct": gpu_peak, "vram_peak_mb": vram_peak, "loop_alive": loop_alive}
    RESULTS.append(r)
    print(f"    n={n} errors={errs} p50={r['p50_s']}s first={r['first_s']}s last={r['last_s']}s "
          f"rss {rss0}->{rss1}MB gpu_peak={gpu_peak}% loop_alive={loop_alive}", flush=True)
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


# ---------------- feature exercises ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--light", type=int, default=30)
    ap.add_argument("--medium", type=int, default=8)
    ap.add_argument("--heavy", type=int, default=2)
    args = ap.parse_args()
    L, M, H = args.light, args.medium, args.heavy

    from nova.services import memory as MEM
    from nova.services import kb as KB
    from nova.services.schedules import run_action
    from nova.services.notifications import add_notification
    from nova.services import control as CTL

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

    # ---- report ----
    print("\n================ FEATURE SOAK REPORT ================")
    total_err = sum(r["errors"] for r in RESULTS)
    for r in RESULTS:
        drift = ""
        if r["first_s"] and r["last_s"] and r["first_s"] > 0:
            ratio = r["last_s"] / r["first_s"]
            drift = f"  drift x{ratio:.1f}" + (" ⚠SLOWDOWN" if ratio > 2 and r["last_s"] > 1 else "")
        print(f"{r['feature']:22} n={r['n']:<3} err={r['errors']} p50={r['p50_s']}s "
              f"rssΔ={r['rss_delta']}MB gpu={r['gpu_peak_pct']}%{drift}")
    print(f"\nTOTAL ERRORS: {total_err}")
    try:
        _post("/api/quality", {"suite": "feature-soak", "score": len(RESULTS) - sum(1 for r in RESULTS if r["errors"]),
                               "total": len(RESULTS), "detail": f"{total_err} errors across {len(RESULTS)} features"})
    except Exception:
        pass
    return total_err == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
