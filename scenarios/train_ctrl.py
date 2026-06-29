# -*- coding: utf-8 -*-
import json, time, urllib.request, sys
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
B="http://127.0.0.1:8900"
def get(p): return json.loads(urllib.request.urlopen(B+p,timeout=20).read().decode())
def post(p): return json.loads(urllib.request.urlopen(urllib.request.Request(B+p,data=b'{}',headers={"Content-Type":"application/json"},method="POST"),timeout=20).read().decode())
L=[]
def rec(name,ok,detail): L.append(f"[{'PASS' if ok else 'FAIL'}] {name} :: {detail}"); print(L[-1],flush=True)

# 1) START
r=post("/api/learn/retrain"); rec("start training","ok" in r and r.get("ok"),f"job={r.get('job')}")
# wait for real LoRA training to begin
ready=False
for _ in range(80):
    time.sleep(5)
    p=get("/api/learn/progress"); sub=p.get("train") or {}
    if p["status"]=="running" and sub.get("step") and sub["step"]>=1:
        ready=True; g=(p.get("gpu") or {}).get("util"); rec("progress reporting (step/ETA/GPU)",True,f"LoRA {sub['step']}/{sub['total']} eta={sub.get('eta')}s gpu={g}%"); break
    if p["status"] in ("completed","error","stopped","idle") and p["step"]>=6: break
if ready:
    g0=(get("/api/learn/progress").get("gpu") or {}).get("util") or 0
    # 2) PAUSE
    post("/api/learn/pause"); time.sleep(8)
    p=get("/api/learn/progress"); g1=(p.get("gpu") or {}).get("util") or 0
    rec("pause training", p["status"]=="paused" and g1<g0, f"status={p['status']} gpu {g0}->{g1}%")
    # 3) RESUME
    post("/api/learn/resume"); time.sleep(8)
    p=get("/api/learn/progress"); g2=(p.get("gpu") or {}).get("util") or 0
    rec("resume training", p["status"]=="running", f"status={p['status']} gpu={g2}%")
    # 4) STOP
    post("/api/learn/stop"); time.sleep(6)
    p=get("/api/learn/progress")
    rec("stop training", p["status"]=="stopped", f"status={p['status']}")
else:
    rec("pause training",False,"training did not reach LoRA phase")
    rec("resume training",False,"n/a")
    rec("stop training",False,"n/a")
    try: post("/api/learn/stop")
    except Exception: pass
open(r"C:\Users\E121\AppData\Local\Temp\claude\C--AI\ddc0f43e-34e5-439b-acd3-3222c1072f6e\scratchpad\train_ctrl_results.txt","w",encoding="utf-8").write("\n".join(L))
print("DONE", sum(1 for x in L if x.startswith("[PASS]")),"/",len(L))
