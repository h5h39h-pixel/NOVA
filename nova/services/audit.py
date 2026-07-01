# -*- coding: utf-8 -*-
"""Audit trail — records security/action events to the DB and live-streams them. Every audit entry is
also mirrored into the unified event log (nova.core.eventlog) so operations, security and errors all
live in one searchable place."""
import time
from nova.core.db import db
from nova.core.events import push
from nova.core import eventlog

# map an audit actor → an event-log category (so ops/security/agent events land in the right bucket)
_CATEGORY = {
    "security": "security", "agent": "agent", "automation": "automation", "browser": "network",
    "image": "media", "vision": "media", "video": "media", "control": "action", "macro": "action",
    "terminal": "exec", "exec": "exec", "user": "action", "settings": "system", "system": "system",
}


def _category(actor, action):
    a = (action or "").lower()
    if "command" in a or "exec" in a:
        return "exec"
    if "file" in a or "write" in a or "read" in a or "ingest" in a:
        return "file"
    return _CATEGORY.get(actor, "action")


def audit(actor, action, detail="", status="ok"):
    """Record a security/action event to the immutable-ish audit trail + live stream + event log."""
    try:
        c = db()
        c.execute("INSERT INTO audit(ts,actor,action,detail,status) VALUES(?,?,?,?,?)",
                  (time.time(), actor, action, (detail or "")[:500], status))
        c.commit(); c.close()
        push({"type": "audit", "ts": time.time(), "actor": actor, "action": action,
              "detail": (detail or "")[:200], "status": status})
    except Exception:
        pass
    # bridge into the unified event log (best-effort; never breaks the audit path)
    level = "warn" if status in ("warn", "fail", "error") else "info"
    eventlog.log(_category(actor, action), action, level=level, source=f"{actor}",
                 detail=detail, actor=actor, status=status)
