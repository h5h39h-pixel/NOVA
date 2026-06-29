# -*- coding: utf-8 -*-
"""Insight/analytics routes that read only the DB — the semantic knowledge map
(brain), predictive habits, and achievements. The model-backed insights (copilot,
insights) stay in server.py since they call the LLM + live metrics."""
import json
import time
from fastapi import APIRouter
from nova.core.db import db

router = APIRouter()

# ---- Nova Brain (semantic knowledge map) ----
@router.get("/api/brain")
def api_brain():
    import numpy as np
    from collections import defaultdict
    c = db(); rows = c.execute("SELECT d.id, d.name, c.emb FROM kb_chunks c JOIN kb_docs d ON d.id=c.doc_id").fetchall(); c.close()
    vecs = defaultdict(list); names = {}
    for r in rows:
        try: vecs[r["id"]].append(np.asarray(json.loads(r["emb"]), dtype="float32")); names[r["id"]] = r["name"]
        except Exception: pass
    cents = {}; nodes = []
    for did, vs in vecs.items():
        cen = np.mean(vs, axis=0); cen /= (np.linalg.norm(cen) + 1e-8); cents[did] = cen
        nodes.append({"id": did, "label": names[did], "chunks": len(vs)})
    ids = list(cents); edges = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            s = float(np.dot(cents[ids[i]], cents[ids[j]]))
            if s > 0.5: edges.append({"a": ids[i], "b": ids[j], "w": round(s, 2)})
    return {"nodes": nodes, "edges": edges}

# ---- Predictive habits ----
@router.get("/api/habits")
def api_habits():
    from collections import Counter
    c = db(); rows = c.execute("SELECT actor, action, ts FROM audit ORDER BY id DESC LIMIT 600").fetchall(); c.close()
    byhour, byaction = Counter(), Counter()
    for r in rows:
        byhour[time.localtime(r["ts"]).tm_hour] += 1; byaction[r["action"]] += 1
    tips = []
    if len(rows) >= 4:
        peak = byhour.most_common(1)[0][0]; tips.append(f"You're most active around {peak:02d}:00.")
        for act in ("retrain", "goal", "run_command", "harvest"):
            if byaction.get(act, 0) >= 3:
                tips.append(f"You run '{act}' often — consider scheduling it."); break
    else:
        tips.append("Building your usage profile…")
    return {"by_hour": dict(byhour), "tips": tips}

# ---- Achievements ----
@router.get("/api/achievements")
def api_achievements():
    c = db()
    def one(q): return c.execute(q).fetchone()[0]
    chats = one("SELECT COUNT(*) FROM chat WHERE role='user'")
    trains = one("SELECT COUNT(*) FROM training_runs")
    agent = one("SELECT COUNT(*) FROM audit WHERE actor='agent' AND action='goal'")
    docs = one("SELECT COUNT(*) FROM kb_docs")
    cmds = one("SELECT COUNT(*) FROM audit WHERE action='run_command'")
    c.close()
    defs = [("💬", "Conversationalist", chats, 10, "messages"),
            ("🎓", "Trainer", trains, 5, "training runs"),
            ("🤖", "Delegator", agent, 10, "agent goals"),
            ("📚", "Librarian", docs, 5, "documents"),
            ("⌨️", "Operator", cmds, 25, "commands")]
    ach = [{"icon": e, "title": t, "have": v, "goal": g, "unit": u, "unlocked": v >= g} for e, t, v, g, u in defs]
    return {"achievements": ach, "unlocked": sum(1 for a in ach if a["unlocked"]), "total": len(ach)}
