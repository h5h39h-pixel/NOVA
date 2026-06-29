# -*- coding: utf-8 -*-
"""Proactive intelligence — rule-based insight tips, the LLM daily briefing, and the
one-line co-pilot suggestion. Reads cross-cutting state (KB, learning stats, live metrics,
running jobs) and asks the local model for prose. Registers `build_briefing` as the
automation briefing hook at import. Depends on nova.core.db + nova.services
(kb/training/metrics/jobs/ollama) + nova.services.schedules (hook registration)."""
from nova.core.db import db, get_settings
from nova.services.kb import kb_status
from nova.services.training import learning_stats
from nova.services.metrics import get_last_metrics
from nova.services.jobs import PM
from nova.services.ollama import ollama_chat_once
from nova.services.schedules import set_briefing_hook


def insights():
    """Rule-based proactive tips from current system state."""
    tips = []
    s = kb_status()
    learn = learning_stats()
    if learn["new_since_last"] >= 10:
        tips.append({"icon": "🎓", "text": f"{learn['new_since_last']} new training examples since last run — retrain to bank them.", "action": "retrain"})
    if not learn["nova"]:
        tips.append({"icon": "🤖", "text": "You haven't trained a personal model yet — create nova-local in Training Studio.", "go": "#/training"})
    if s["docs"] == 0:
        tips.append({"icon": "📚", "text": "Your Knowledge Base is empty — add documents to unlock RAG answers in chat.", "go": "#/knowledge"})
    m = get_last_metrics() or {}
    if m.get("gpu") and m["gpu"]["vram_total"]:
        vp = m["gpu"]["vram_used"] / m["gpu"]["vram_total"] * 100
        if vp > 85:
            tips.append({"icon": "💾", "text": f"VRAM is {round(vp)}% full — unload a model from the Models page to free memory.", "go": "#/models"})
    try:
        running = any(j.kind == "training" and j.status in ("running", "starting") for j in PM.jobs.values())
        if running: tips.append({"icon": "⏳", "text": "Training is running now — watch live progress in Training Studio.", "go": "#/training"})
    except Exception: pass
    if not tips:
        tips.append({"icon": "✨", "text": "Everything looks healthy. Try Agent Mode to automate a multi-step goal.", "go": "#/agent"})
    return {"insights": tips}


def build_briefing():
    c = db()
    recent = [f"{r['actor']}/{r['action']}" for r in c.execute("SELECT actor,action FROM audit ORDER BY id DESC LIMIT 12")]
    notifs = [r["title"] for r in c.execute("SELECT title FROM notifications ORDER BY id DESC LIMIT 8")]
    c.close()
    learn = learning_stats(); kb = kb_status()
    facts = (f"KB: {kb['docs']} documents, {kb['chunks']} chunks. "
             f"Training: {learn['base']} base + {learn['learned']} learned = {learn['combined']} examples; "
             f"{learn['new_since_last']} new since last training; personal model {'installed' if learn['nova'] else 'not built'}. "
             f"Recent actions: {', '.join(recent) or 'none'}. Recent events: {', '.join(notifs) or 'none'}.")
    model = get_settings().get("default_local_model", "llama3.1:8b")
    prompt = ("Write a short, friendly daily briefing for the user about their local AI system. "
              "4-5 concise bullet points summarizing status, then 1-2 suggested next actions. "
              "Use markdown bullets. Data:\n" + facts)
    try: text = ollama_chat_once(model, [{"role": "user", "content": prompt}], 0.4)
    except Exception as e: text = f"(briefing unavailable: {e})"
    return {"text": text, "facts": facts}


def copilot():
    learn = learning_stats(); kb = kb_status(); m = get_last_metrics() or {}
    gutil = round((m.get("gpu") or {}).get("util", 0))
    state = (f"KB: {kb['docs']} docs/{kb['chunks']} chunks. Training: {learn['combined']} examples, "
             f"{learn['new_since_last']} new since last train, personal model {'ready' if learn['nova'] else 'not built'}. GPU {gutil}% used.")
    model = get_settings().get("default_local_model", "llama3.1:8b")
    prompt = ("You are Nova, a proactive co-pilot for a local AI command center. Given the state, suggest ONE "
              "specific high-value next action in a single short sentence (max 16 words). State:\n" + state)
    try: text = ollama_chat_once(model, [{"role": "user", "content": prompt}], 0.5).strip().split("\n")[0]
    except Exception as e: text = f"(co-pilot unavailable: {e})"
    tl = text.lower(); action = None
    if "retrain" in tl or "train" in tl: action = "retrain"
    elif "video" in tl: action = {"go": "#/video"}
    elif any(k in tl for k in ("document", "knowledge", "index", "ingest")): action = {"go": "#/knowledge"}
    elif "agent" in tl: action = {"go": "#/agent"}
    return {"text": text, "action": action}


set_briefing_hook(build_briefing)   # let the automation "briefing" action use this generator
