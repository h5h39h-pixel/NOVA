# -*- coding: utf-8 -*-
"""
One-command intensive test suite for the AI Control Center.
Usage:  python run_tests.py     (server must be running on :8900)
Exercises every GET endpoint, key create/use/delete round-trips, and the live
WebSocket chat + agent flows. Exits non-zero if anything fails.
"""
import json, time, sys, urllib.request, asyncio
try:
    import websockets
except ImportError:
    websockets = None
B = "http://127.0.0.1:8900"

def jget(p): return json.loads(urllib.request.urlopen(B + p, timeout=60).read().decode())
def post(p, b=None): return json.loads(urllib.request.urlopen(urllib.request.Request(
    B + p, data=(json.dumps(b).encode() if b is not None else None),
    headers={"Content-Type": "application/json"}, method="POST")).read().decode())
def delete(p): return json.loads(urllib.request.urlopen(urllib.request.Request(B + p, method="DELETE")).read().decode())

passed, failures = 0, []
def check(name, fn):
    global passed
    try:
        if fn(): passed += 1; print(f"  PASS  {name}")
        else: failures.append(name); print(f"  FAIL  {name}")
    except Exception as e:
        failures.append(f"{name}: {e}"); print(f"  FAIL  {name} :: {e}")

GETS = ["/api/services", "/api/metrics", "/api/models", "/api/media-models", "/api/toolkit/list", "/api/owui",
        "/api/processes", "/api/processes/system", "/api/comfy/status", "/api/history", "/api/notifications",
        "/api/settings", "/api/auth/status", "/api/conversations", "/api/db-status", "/api/training/status",
        "/api/training/log", "/api/training/history", "/api/learning/stats", "/api/learn/progress",
        "/api/kb/status", "/api/kb/docs", "/api/schedules", "/api/workflows", "/api/audit", "/api/insights",
        "/api/search?q=test", "/api/selftest", "/api/briefing", "/api/logs", "/api/copilot", "/api/brain"]

print("== endpoints ==")
for g in GETS: check("GET " + g, (lambda g=g: jget(g) is not None))

print("== self-test detail ==")
st = jget("/api/selftest"); check(f"self-test {st['passed']}/{st['total']}", lambda: st["ok"])

print("== round-trips ==")
def rt_conv():
    cid = post("/api/conversations", {"project": "TEST"})["cid"]
    ok = isinstance(jget(f"/api/conversations/{cid}/messages"), list)
    delete(f"/api/conversations/{cid}"); return ok
check("conversation CRUD", rt_conv)
def rt_sched():
    post("/api/schedules", {"name": "TESTsched", "action": "notify", "params": {"text": "x"}, "interval_sec": 0, "first_delay_sec": 99999})
    s = [x for x in jget("/api/schedules") if x["name"] == "TESTsched"][0]
    post(f"/api/schedules/{s['id']}/run"); delete(f"/api/schedules/{s['id']}"); return True
check("schedule create/run/delete", rt_sched)
def rt_wf():
    post("/api/workflows", {"name": "TESTwf", "steps": [{"action": "notify", "params": {"text": "a"}}]})
    w = [x for x in jget("/api/workflows") if x["name"] == "TESTwf"][0]
    post(f"/api/workflows/{w['id']}/run"); time.sleep(1); delete(f"/api/workflows/{w['id']}"); return True
check("workflow create/run/delete", rt_wf)
def rt_browse():
    r = post("/api/browse", {"url": "https://example.com"})
    return r.get("title") == "Example Domain" and bool(r.get("screenshot"))
check("browser automation (Playwright)", rt_browse)
def rt_security():
    s = jget("/api/settings")  # token must never be exposed
    return "auth_token" not in s and "auth_token_hash" not in s
check("settings redact secret token", rt_security)
def rt_screen():
    r = post("/api/screen/shot", {})
    return bool(r.get("file"))
check("screen capture", rt_screen)
def rt_bugs():
    post("/api/bugs", {"title": "TESTbug", "detail": "x", "severity": "low"})
    items = jget("/api/bugs").get("items", [])
    b = [x for x in items if x["title"] == "TESTbug"]
    if b: delete("/api/bugs/" + str(b[0]["id"]))
    return bool(b)
check("bug report CRUD", rt_bugs)

if websockets:
    print("== live flows ==")
    async def flows():
        async with websockets.connect("ws://127.0.0.1:8900/ws") as ws:
            post("/api/chat-send", {"prompt": "reply OK", "model": "llama3.2:3b"})
            post("/api/agent", {"goal": "notify me the time", "model": "llama3.1:8b", "dry_run": True})
            gc = ga = False; t = time.time()
            while time.time() - t < 120:
                m = json.loads(await asyncio.wait_for(ws.recv(), timeout=120))
                if m.get("type") == "chat" and m.get("ev") == "end": gc = True
                if m.get("type") == "agent" and m.get("ev") == "done": ga = True
                if gc and ga: break
            return gc, ga
    gc, ga = asyncio.new_event_loop().run_until_complete(flows())
    check("chat stream", lambda: gc); check("agent dry-run", lambda: ga)

print(f"\n{'='*40}\nPASSED {passed} / {passed + len(failures)}")
if failures:
    print("FAILURES:"); [print("  -", f) for f in failures]; sys.exit(1)
print("ALL CHECKS PASSED")
