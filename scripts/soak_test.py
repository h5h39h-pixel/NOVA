# -*- coding: utf-8 -*-
"""Soak / longevity test — hammer the running server for a configurable duration and watch for the
things that only show up over time: **memory growth (leaks), background-loop liveness, error
accumulation, and VLM-queue backpressure**.

Honest by design: prints a linear RSS slope (MB/hour) so a real leak is visible, not hidden behind a
single before/after number. Non-destructive (reads + throwaway memory rows it deletes).

    python scripts/soak_test.py --minutes 20            # accelerated soak (real metrics)
    python scripts/soak_test.py --hours 24              # the real overnight run
    python scripts/soak_test.py --hours 24 --vlm        # also exercise the VLM describe queue

Needs the server on :8900 + psutil. Records a summary to the quality dashboard (suite='soak').
"""
import argparse
import sys
import time
import urllib.request
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
BASE = "http://127.0.0.1:8900"


def _get(path, timeout=10):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _post(path, body, timeout=30):
    data = json.dumps(body).encode()
    rq = urllib.request.Request(BASE + path, data=data,
                                headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(rq, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _server_pid():
    import psutil
    for c in psutil.net_connections(kind="inet"):
        if c.laddr and c.laddr.port == 8900 and c.status == "LISTEN" and c.pid:
            return c.pid
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if p.info["cmdline"] and any("server.py" in str(a) for a in p.info["cmdline"]):
                return p.info["pid"]
        except Exception:
            pass
    return None


def _write_progress(d):
    """Write live progress to data/logs/soak_progress.json so a long (24h) run is observable."""
    try:
        from config import LOG_DIR
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        (LOG_DIR / "soak_progress.json").write_text(json.dumps(d, indent=2), encoding="utf-8")
    except Exception:
        pass


def _slope(xs, ys):
    """Least-squares slope of ys over xs (per unit x)."""
    n = len(xs)
    if n < 2:
        return 0.0
    mx = sum(xs) / n; my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den if den else 0.0


def run(seconds, vlm):
    import psutil
    pid = _server_pid()
    if not pid:
        print("could not find the server process (is it running on :8900?)"); return
    proc = psutil.Process(pid)
    print(f"soaking server pid={pid} for {seconds/3600:.2f}h  (vlm={'on' if vlm else 'off'})")

    t0 = time.time()
    samples = []            # (elapsed_h, rss_mb)
    reqs = errs = 0
    vlm_lat = []
    loop_dead = 0
    last_sample = 0
    last_vlm = 0
    last_hour_mark = 0.0
    start_err = _get("/api/errors").get("total", 0)

    while time.time() - t0 < seconds:
        cycle = time.time()
        # cheap, high-frequency traffic to exercise loops + handlers
        for path in ("/api/health", "/api/processes", "/api/notifications", "/api/memory",
                     "/api/quality", "/api/metrics/history?n=20"):
            try:
                _get(path); reqs += 1
            except Exception:
                errs += 1
        # a heavier write path periodically (memory add/delete — throwaway)
        try:
            r = _post("/api/memory", {"text": f"soak throwaway {int(cycle)}"})
            if r.get("ok"):
                _req_delete(f"/api/memory/{r['item']['id']}")
            reqs += 2
        except Exception:
            errs += 1
        # VLM queue pressure (optional; only if screen vision + narrate are user-enabled)
        if vlm and time.time() - last_vlm > 20:
            last_vlm = time.time()
            try:
                v0 = time.time()
                d = _post("/api/vision/describe", {}, timeout=120)
                if d.get("ok") is not False:
                    vlm_lat.append(time.time() - v0)
            except Exception:
                pass
        # sample RSS + loop liveness every 30s
        if time.time() - last_sample >= 30:
            last_sample = time.time()
            try:
                rss = proc.memory_info().rss / (1024 * 1024)
                h = (time.time() - t0) / 3600
                samples.append((h, rss))
                alive = _get("/api/health").get("metrics_loop_alive", True)
                if not alive:
                    loop_dead += 1
                cur_err = _get("/api/errors").get("total", 0) - start_err
                slope_now = _slope([s[0] for s in samples], [s[1] for s in samples])
                print(f"  t={h*60:7.1f}min  rss={rss:8.1f}MB  reqs={reqs}  errs={errs}+{cur_err}  "
                      f"loop_alive={alive}  slope={slope_now:+.1f}MB/h"
                      + (f"  vlm_p50={_p50(vlm_lat):.1f}s" if vlm_lat else ""))
                sys.stdout.flush()          # so a 24h run is observable live (block-buffered otherwise)
                _write_progress({"elapsed_min": round(h * 60, 1), "rss_mb": round(rss, 1),
                                 "rss_slope_mb_per_h": round(slope_now, 1), "requests": reqs,
                                 "http_errors": errs, "runtime_errors": cur_err,
                                 "loop_dead_samples": loop_dead, "samples": len(samples),
                                 "vlm_calls": len(vlm_lat), "vlm_p50_s": round(_p50(vlm_lat), 1)})
                # hourly checkpoint to the quality dashboard so long runs leave a trail
                if h - last_hour_mark >= 1.0:
                    last_hour_mark = h
                    try:
                        _post("/api/quality", {"suite": "soak-hourly", "score": 1, "total": 1,
                                               "detail": f"h{int(h)} rss{rss:.0f} slope{slope_now:+.1f}"})
                    except Exception:
                        pass
            except Exception as e:
                print(f"  sample failed: {e}"); sys.stdout.flush()
        time.sleep(1)

    # ---- report ----
    end_err = _get("/api/errors").get("total", 0)
    rss_slope = _slope([s[0] for s in samples], [s[1] for s in samples]) if len(samples) > 1 else 0.0
    rss_min = min((s[1] for s in samples), default=0)
    rss_max = max((s[1] for s in samples), default=0)
    dur_h = (time.time() - t0) / 3600
    print("\n=== SOAK REPORT ===")
    print(f"duration:        {dur_h*60:.1f} min ({dur_h:.2f} h)")
    print(f"requests:        {reqs}  (errors: {errs})")
    print(f"RSS:             min {rss_min:.1f}MB / max {rss_max:.1f}MB / slope {rss_slope:+.1f} MB/hour")
    print(f"runtime errors:  +{end_err - start_err} during soak")
    print(f"metrics loop:    {loop_dead} dead samples of {len(samples)}")
    if vlm_lat:
        print(f"VLM describe:    n={len(vlm_lat)}  p50={_p50(vlm_lat):.1f}s  max={max(vlm_lat):.1f}s")
    # honest verdict
    leaking = rss_slope > 50 and rss_max - rss_min > 100     # >50MB/h AND >100MB absolute growth
    verdict = "LEAK SUSPECTED" if leaking else "no leak signal"
    print(f"verdict:         {verdict}")
    try:
        _post("/api/quality", {"suite": "soak", "score": 0 if leaking else 1, "total": 1,
                               "detail": f"{dur_h:.1f}h slope {rss_slope:+.1f}MB/h err+{end_err-start_err}"})
    except Exception:
        pass
    return not leaking


def _p50(xs):
    if not xs: return 0.0
    s = sorted(xs); return s[len(s) // 2]


def _req_delete(path):
    rq = urllib.request.Request(BASE + path, method="DELETE")
    urllib.request.urlopen(rq, timeout=10).read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=0)
    ap.add_argument("--hours", type=float, default=0)
    ap.add_argument("--vlm", action="store_true", help="also exercise the VLM describe queue")
    args = ap.parse_args()
    seconds = args.hours * 3600 + args.minutes * 60
    if seconds <= 0:
        seconds = 20 * 60
    ok = run(seconds, args.vlm)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
