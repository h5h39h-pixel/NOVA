# -*- coding: utf-8 -*-
"""HON-5 — load / concurrency smoke test. Hammers the live API with concurrent reads AND writes to
confirm WAL holds up (no "database is locked") and the server stays responsive. Non-destructive:
write load creates + deletes its own throwaway conversations.

Run (server must be up):  python scripts/load_test.py [--workers 24] [--rounds 8]
"""
import argparse
import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

B = "http://127.0.0.1:8900"


def _get(path):
    t = time.time()
    try:
        with urllib.request.urlopen(B + path, timeout=10) as r:
            r.read()
            return True, time.time() - t
    except Exception:
        return False, time.time() - t


def _post(path, body):
    try:
        rq = urllib.request.Request(B + path, data=json.dumps(body).encode(),
                                    headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(rq, timeout=10) as r:
            return True, json.loads(r.read())
    except Exception:
        return False, None


def _del(path):
    try:
        rq = urllib.request.Request(B + path, method="DELETE")
        with urllib.request.urlopen(rq, timeout=10) as r:
            r.read(); return True
    except Exception:
        return False


READ_PATHS = ["/api/health", "/api/settings", "/api/conversations", "/api/metrics/history",
              "/api/control/screen", "/api/errors"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--rounds", type=int, default=8)
    args = ap.parse_args()

    ok, _ = _get("/api/health")
    if not ok:
        print("ERROR: server not up on :8900"); return 1

    # ---- concurrent READS ----
    jobs = READ_PATHS * args.rounds
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        res = list(ex.map(_get, jobs))
    wall = time.time() - t0
    oks = sum(1 for s, _ in res if s)
    lat = sorted(d for _, d in res)
    p95 = lat[int(len(lat) * 0.95) - 1] if lat else 0
    print(f"READS: {oks}/{len(res)} ok in {wall:.1f}s | p95 {p95*1000:.0f}ms | workers={args.workers}")

    # ---- concurrent WRITES (create + delete throwaway conversations → stresses WAL) ----
    created = []
    def _mk(i):
        s, r = _post("/api/conversations", {"project": "LOADTEST"})
        return r.get("cid") if (s and r) else None
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        cids = [c for c in ex.map(_mk, range(args.workers * 2)) if c]
    created = cids
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        dels = list(ex.map(lambda c: _del("/api/conversations/" + c), created))
    print(f"WRITES: created {len(created)} conversations concurrently, deleted {sum(dels)} | "
          f"{'no lock errors' if len(created) == args.workers*2 else 'SOME WRITES FAILED'}")

    # ---- single-flight chat lock: two concurrent chat-sends; one should be accepted, the system
    #      must not wedge (we don't assert busy text — models may answer fast — just that both return)
    with ThreadPoolExecutor(max_workers=2) as ex:
        chat = list(ex.map(lambda _: _post("/api/chat-send", {"prompt": "say hi", "model": "llama3.2:3b"}),
                           range(2)))
    print(f"CHAT single-flight: {sum(1 for s,_ in chat if s)}/2 requests returned cleanly")

    passed = oks == len(res) and len(created) == args.workers * 2
    print("\n=== HON-5:", "PASS — concurrent reads+writes held up (WAL ok, no lock errors) ==="
          if passed else "FAIL — see above ===")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
