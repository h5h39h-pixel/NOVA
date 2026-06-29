# -*- coding: utf-8 -*-
"""Backup & restore — export the full state (settings minus secrets, conversations + chat,
schedules, workflows, KB docs + chunks, training datasets) as one JSON bundle, and merge a
bundle back in (skips existing conversations, never restores auth). Depends on nova.core.db,
nova.services (audit, training.rebuild_combined) + config (dataset paths)."""
import json
import time
import sqlite3
from config import DS_BASE, DS_LEARNED, DB_PATH
from nova.core.db import db, get_settings, set_settings
from nova.services.audit import audit
from nova.services.training import rebuild_combined

BACKUP_DIR = DB_PATH.parent / "backups"


def snapshot_db(keep=14):
    """Consistent online snapshot of the SQLite DB → data/backups/, pruned to the last `keep`.
    Uses SQLite's backup API (safe while the DB is in use). Returns the snapshot path."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    dest = BACKUP_DIR / f"control-{time.strftime('%Y%m%d_%H%M%S')}.db"
    src = sqlite3.connect(str(DB_PATH)); dst = sqlite3.connect(str(dest))
    try: src.backup(dst)
    finally: dst.close(); src.close()
    snaps = sorted(BACKUP_DIR.glob("control-*.db"))
    for old in snaps[:-keep]:
        try: old.unlink()
        except Exception: pass
    return str(dest)


def list_snapshots():
    if not BACKUP_DIR.exists(): return []
    out = []
    for p in sorted(BACKUP_DIR.glob("control-*.db"), reverse=True):
        try: st = p.stat(); out.append({"name": p.name, "size": st.st_size, "ts": st.st_mtime})
        except Exception: pass
    return out


def make_backup():
    c = db()
    def rows(t): return [dict(r) for r in c.execute(f"SELECT * FROM {t}").fetchall()]
    bundle = {"version": 1, "ts": time.time(),
              "settings": {k: v for k, v in get_settings().items() if k not in ("auth_token", "auth_token_hash")},
              "conversations": rows("conversations"), "chat": rows("chat"),
              "schedules": rows("schedules"), "workflows": rows("workflows"),
              "kb_docs": rows("kb_docs"), "kb_chunks": rows("kb_chunks"),
              "datasets": {"base": DS_BASE.read_text(encoding="utf-8") if DS_BASE.exists() else "",
                           "learned": DS_LEARNED.read_text(encoding="utf-8") if DS_LEARNED.exists() else ""}}
    c.close()
    return bundle


def restore_backup(b):
    """Merge a backup bundle. Returns a count dict, or None if the bundle is unrecognized."""
    if b.get("version") != 1: return None
    s = {k: v for k, v in (b.get("settings") or {}).items() if k not in ("auth_enabled", "auth_token", "auth_token_hash", "lan_access")}
    if s: set_settings(s)
    ds = b.get("datasets", {})
    if ds.get("base"): DS_BASE.write_text(ds["base"], encoding="utf-8")
    if ds.get("learned"): DS_LEARNED.write_text(ds["learned"], encoding="utf-8")
    rebuild_combined()
    c = db(); added = {"conversations": 0, "chat": 0, "schedules": 0, "workflows": 0, "kb_docs": 0}
    have = {r[0] for r in c.execute("SELECT cid FROM conversations")}
    for cv in b.get("conversations", []):
        if cv.get("cid") in have: continue
        c.execute("INSERT INTO conversations(cid,project,title,created,updated,archived,tokens) VALUES(?,?,?,?,?,?,?)",
                  (cv.get("cid"), cv.get("project"), cv.get("title"), cv.get("created"), cv.get("updated"), cv.get("archived", 0), cv.get("tokens", 0)))
        added["conversations"] += 1
        for m in b.get("chat", []):
            if m.get("cid") == cv.get("cid"):
                c.execute("INSERT INTO chat(ts,session_id,cid,role,content,model_used) VALUES(?,?,?,?,?,?)",
                          (m.get("ts"), m.get("session_id"), m.get("cid"), m.get("role"), m.get("content"), m.get("model_used")))
                added["chat"] += 1
    for r in b.get("schedules", []):
        c.execute("INSERT INTO schedules(name,action,params,interval_sec,next_run,enabled,last_run,last_status,created) VALUES(?,?,?,?,?,?,?,?,?)",
                  (r.get("name"), r.get("action"), r.get("params"), r.get("interval_sec"), r.get("next_run"), r.get("enabled"), r.get("last_run"), r.get("last_status"), r.get("created")))
        added["schedules"] += 1
    for r in b.get("workflows", []):
        steps = r.get("steps"); steps = steps if isinstance(steps, str) else json.dumps(steps)
        c.execute("INSERT INTO workflows(name,steps,created,last_run,last_status) VALUES(?,?,?,?,?)",
                  (r.get("name"), steps, r.get("created"), r.get("last_run"), r.get("last_status")))
        added["workflows"] += 1
    for d in b.get("kb_docs", []):
        nid = c.execute("INSERT INTO kb_docs(name,chunks,created) VALUES(?,?,?)", (d.get("name"), d.get("chunks"), d.get("created"))).lastrowid
        for ch in b.get("kb_chunks", []):
            if ch.get("doc_id") == d.get("id"):
                c.execute("INSERT INTO kb_chunks(doc_id,ord,text,emb) VALUES(?,?,?,?)", (nid, ch.get("ord"), ch.get("text"), ch.get("emb")))
        added["kb_docs"] += 1
    c.commit(); c.close()
    audit("settings", "restore", f"restored {added}")
    return added
