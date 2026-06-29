# -*- coding: utf-8 -*-
"""
Notifications + outbound webhooks.

`add_notification` persists a notification, live-streams it to dashboards, mirrors
it to an external webhook (Slack/Discord/ntfy) if configured, and raises a native
desktop toast. Category/deep-link are inferred from the title.
"""
import time, json, threading, subprocess, urllib.request
from config import TOOLKIT
from nova.core.db import db, get_settings
from nova.core.events import push

def send_webhook(title, body="", level="info"):
    """Deliver a notification to an external incoming webhook (Slack/Discord/ntfy/generic)."""
    s = get_settings()
    url = s.get("webhook_url", "")
    if not (s.get("webhook_enabled") and url): return
    icon = {"success": "✅", "error": "❌", "info": "ℹ️"}.get(level, "🔔")
    text = f"{icon} {title}" + (f" — {body}" if body else "")
    payload = json.dumps({"text": text, "content": text, "title": title, "body": body, "level": level}).encode()
    def work():
        try:
            urllib.request.urlopen(urllib.request.Request(url, data=payload,
                headers={"Content-Type": "application/json"}, method="POST"), timeout=10)
        except Exception: pass
    threading.Thread(target=work, daemon=True).start()

def _notif_category(title):
    t = (title or "").lower()
    if any(k in t for k in ("train", "model", "retrain", "harvest", "dataset")): return ("training", "#/training")
    if "agent" in t: return ("agent", "#/agent")
    if "video" in t: return ("video", "#/video")
    if any(k in t for k in ("schedule", "automation", "workflow", "webhook", "briefing")): return ("automation", "#/automation")
    if any(k in t for k in ("document", "knowledge", "indexed", "kb")): return ("knowledge", "#/knowledge")
    if any(k in t for k in ("auth", "security", "login", "restore")): return ("security", "#/audit")
    if "chat" in t or "saved to training" in t: return ("chat", "#/chat")
    return ("system", "")

def add_notification(level, title, body="", category=None, link=None):
    cat, lk = _notif_category(title)
    category = category or cat; link = link if link is not None else lk
    ts = time.time()
    c = db()
    c.execute("INSERT INTO notifications(ts,level,title,body,category,link) VALUES(?,?,?,?,?,?)",
              (ts, level, title, body, category, link))
    c.commit(); c.close()
    push({"type": "notification", "level": level, "title": title, "body": body,
          "category": category, "link": link, "ts": ts})
    send_webhook(title, body, level)
    if get_settings().get("desktop_notifications"):
        try:
            subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                              "-File", str(TOOLKIT / "notify.ps1"), title, body],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception: pass
