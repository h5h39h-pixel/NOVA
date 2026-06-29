# -*- coding: utf-8 -*-
"""
Data layer — the single place that talks to SQLite.

Owns: the connection factory, schema + migrations, settings get/set, and the
command-history writer. Pure data; depends only on `config`. Nothing here imports
events/services, so it sits safely at the bottom of the dependency graph.
"""
import json, time, sqlite3
from config import DB_PATH

DEFAULT_SETTINGS = {
    "mode": "auto",                       # local | cloud | auto
    "default_local_model": "llama3.1:8b",
    "default_cloud_model": "claude-opus-4-8",
    "cloud_api_key": "",
    "accent": "#6366f1",
    "desktop_notifications": True,
    "metrics_interval": 1.5,
    "webhook_url": "",            # Slack/Discord/ntfy/generic incoming webhook
    "webhook_enabled": False,
    "auth_enabled": False,        # require a login token for all API + WebSocket access
    "auth_token": "",             # legacy plaintext (superseded by auth_token_hash)
    "lan_access": False,          # bind 0.0.0.0 instead of localhost (ONLY meaningful with auth on)
    "allow_remote_exec": False,   # permit /api/exec + agent run_command when exposed on LAN (off by default)
    "lite_visuals": False,        # reduce background animations (particles/aurora/tilt) for low-end GPUs
}

def db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
    CREATE TABLE IF NOT EXISTS history  (id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL, command TEXT, exit_code INTEGER, duration REAL, output TEXT, source TEXT);
    CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL, level TEXT, title TEXT, body TEXT, seen INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS chat (id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL, role TEXT, content TEXT);
    CREATE TABLE IF NOT EXISTS conversations (cid TEXT PRIMARY KEY,
        project TEXT DEFAULT 'General', title TEXT, created REAL, updated REAL,
        archived INTEGER DEFAULT 0, tokens INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS training_runs (id INTEGER PRIMARY KEY AUTOINCREMENT,
        started REAL, ended REAL, ok INTEGER, steps INTEGER, base INTEGER, learned INTEGER,
        combined INTEGER, note TEXT);
    CREATE TABLE IF NOT EXISTS kb_docs (id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, chunks INTEGER, created REAL);
    CREATE TABLE IF NOT EXISTS kb_chunks (id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id INTEGER, ord INTEGER, text TEXT, emb TEXT);
    CREATE TABLE IF NOT EXISTS schedules (id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, action TEXT, params TEXT, interval_sec INTEGER, next_run REAL,
        enabled INTEGER DEFAULT 1, last_run REAL, last_status TEXT, created REAL);
    CREATE TABLE IF NOT EXISTS workflows (id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, steps TEXT, created REAL, last_run REAL, last_status TEXT);
    CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL, actor TEXT, action TEXT, detail TEXT, status TEXT);
    CREATE TABLE IF NOT EXISTS bug_reports (id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL, title TEXT, detail TEXT, severity TEXT, status TEXT DEFAULT 'open',
        page TEXT, logs TEXT);
    """)
    # migrate older chat tables to the richer schema
    chat_cols = [r[1] for r in c.execute("PRAGMA table_info(chat)")]
    if "session_id" not in chat_cols: c.execute("ALTER TABLE chat ADD COLUMN session_id TEXT")
    if "model_used" not in chat_cols: c.execute("ALTER TABLE chat ADD COLUMN model_used TEXT")
    if "cid" not in chat_cols: c.execute("ALTER TABLE chat ADD COLUMN cid TEXT")
    ncols = [r[1] for r in c.execute("PRAGMA table_info(notifications)")]
    if "category" not in ncols: c.execute("ALTER TABLE notifications ADD COLUMN category TEXT")
    if "link" not in ncols: c.execute("ALTER TABLE notifications ADD COLUMN link TEXT")
    for k, v in DEFAULT_SETTINGS.items():
        c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k, json.dumps(v)))
    run_migrations(c)
    c.commit(); c.close()


# ─── versioned migrations ───────────────────────────────────────────────
# The schema above is the baseline (v1). Add future changes as (version, fn) entries below;
# each runs once, in order, and the applied version is recorded in `schema_version`.
SCHEMA_VERSION = 1
MIGRATIONS = [
    # (2, lambda c: c.execute("ALTER TABLE kb_docs ADD COLUMN tags TEXT")),
]

def run_migrations(c):
    """Apply ordered, idempotent migrations; stamp the applied version in schema_version."""
    c.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
    row = c.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
    if not row:
        c.execute("INSERT INTO schema_version(version) VALUES(?)", (SCHEMA_VERSION,))
        return SCHEMA_VERSION   # fresh/existing baseline DB → stamp current, nothing to replay
    cur = row[0]
    for ver, fn in MIGRATIONS:
        if cur < ver:
            fn(c); cur = ver
            c.execute("UPDATE schema_version SET version=?", (ver,))
    return cur

def get_settings():
    c = db(); rows = c.execute("SELECT key,value FROM settings").fetchall(); c.close()
    s = dict(DEFAULT_SETTINGS)
    for r in rows:
        try: s[r["key"]] = json.loads(r["value"])
        except Exception: s[r["key"]] = r["value"]
    return s

def set_settings(patch: dict):
    c = db()
    for k, v in patch.items():
        c.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                  (k, json.dumps(v)))
    c.commit(); c.close()
    return get_settings()

def add_history(command, exit_code, duration, output, source="terminal"):
    c = db()
    c.execute("INSERT INTO history(ts,command,exit_code,duration,output,source) VALUES(?,?,?,?,?,?)",
              (time.time(), command, exit_code, duration, (output or "")[-4000:], source))
    c.commit(); c.close()
