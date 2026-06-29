# -*- coding: utf-8 -*-
"""Audit trail — records security/action events to the DB and live-streams them."""
import time
from nova.core.db import db
from nova.core.events import push

def audit(actor, action, detail="", status="ok"):
    """Record a security/action event to the immutable-ish audit trail + live stream."""
    try:
        c = db()
        c.execute("INSERT INTO audit(ts,actor,action,detail,status) VALUES(?,?,?,?,?)",
                  (time.time(), actor, action, (detail or "")[:500], status))
        c.commit(); c.close()
        push({"type": "audit", "ts": time.time(), "actor": actor, "action": action,
              "detail": (detail or "")[:200], "status": status})
    except Exception:
        pass
