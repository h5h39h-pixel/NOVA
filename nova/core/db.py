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
    "desktop_notifications": True,
    "metrics_interval": 1.5,
    "webhook_url": "",            # Slack/Discord/ntfy/generic incoming webhook
    "webhook_enabled": False,
    "auth_enabled": False,        # require a login token for all API + WebSocket access
    "auth_token": "",             # legacy plaintext (superseded by auth_token_hash)
    "lan_access": False,          # bind 0.0.0.0 instead of localhost (ONLY meaningful with auth on)
    "allow_remote_exec": False,   # permit /api/exec + agent run_command when exposed on LAN (off by default)
    "stt_model": "small",         # local Whisper size: tiny | base | small | medium | large-v3 (small = good Arabic, GPU-fast)
    "confirm_exit": True,         # warn before closing the tab/window ("Nova is still running")
    "tts_rate": 1.0,              # speech rate for Piper TTS (1.0 normal, >1 faster, <1 slower)
    # ---- AI Screen Vision (Phase 7) — ALL opt-in, local-only, non-persistent by default ----
    "screen_vision_enabled": False,  # master switch for the live screen stream + vision loop
    "vision_fps": 4,                 # live stream frames/sec (throttled; 1–15)
    "vision_max_width": 1280,        # downscale frames to this width before JPEG (bandwidth/CPU bound)
    "vision_quality": 70,            # JPEG quality 30–95
    "track_mouse": False,            # expose live cursor position (opt-in)
    "track_keyboard": False,         # SV-4: capture active-window + recent-keystroke context (most sensitive; opt-in)
    "vision_narrate": False,         # SV-2: opt-in continuous VLM narration loop (cost-aware; off by default)
    "vision_narrate_interval": 30,   # SV-2: seconds between narration frames (10–300)
    "screen_memory_enabled": False,  # IDEA-2: opt-in — OCR snapshots of the screen into the KB ("what did I see earlier?")
    "screen_memory_keep": 50,        # IDEA-2b: retention cap — keep only the newest N screen-memory docs
    "upload_keep": 300,              # retention cap: newest N of each ephemeral upload type (screenshots/browse/recordings) kept; older auto-pruned so generated media can't fill the disk
    "agent_can_control": True,       # HON-1b: allow the AUTONOMOUS agent to drive mouse/keyboard (control/act_on_screen). Turn OFF to keep the agent from GUI control while still allowing manual control + the kill-switch.
    "control_mode": "auto",          # confirmation policy for dangerous agent actions: auto (no prompt) | confirm (ask before click/type/delete/run) | full (no prompt + run anything). Default auto.
    "control_protected_patterns": None,  # HON-1b: window-title patterns where click/type is BLOCKED (None = built-in default list: password managers, banking, auth). Set [] to disable, or a custom list.
    "allow_input_capture": False,    # master gate for the keylogger-class features (macro recording + SV-4 keystroke context). OFF by default — both refuse to start unless this is on.
    "memory_semantic": False,        # IDEA-8: use embedding-based (semantic) memory recall instead of keyword. Off = free/fast keyword on the chat hot path; on = one embed call per recall.
}

def db():
    # timeout/busy_timeout let a writer wait for a lock instead of failing with "database is locked"
    # under the app's concurrent loops + request handlers (STB-5).
    c = sqlite3.connect(DB_PATH, timeout=5.0)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA busy_timeout=5000")
    c.execute("PRAGMA synchronous=NORMAL")   # durable across app crash; safe + fast with WAL
    return c

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = db()
    c.execute("PRAGMA journal_mode=WAL")      # persistent on the file: readers don't block the writer

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
    CREATE TABLE IF NOT EXISTS metrics_history (id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL, cpu REAL, ram REAL, gpu_util REAL, vram_used REAL, vram_total REAL, gpu_temp REAL);
    CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT,
        jid TEXT, name TEXT, kind TEXT, status TEXT, started REAL, ended REAL, exit_code INTEGER, source TEXT);
    CREATE TABLE IF NOT EXISTS memory (id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL, kind TEXT DEFAULT 'fact', text TEXT, tags TEXT, source TEXT, pinned INTEGER DEFAULT 0, emb TEXT);
    CREATE TABLE IF NOT EXISTS quality_runs (id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL, suite TEXT, score REAL, total REAL, pct REAL, detail TEXT);
    """)
    # migrate older chat tables to the richer schema
    chat_cols = [r[1] for r in c.execute("PRAGMA table_info(chat)")]
    if "session_id" not in chat_cols: c.execute("ALTER TABLE chat ADD COLUMN session_id TEXT")
    if "model_used" not in chat_cols: c.execute("ALTER TABLE chat ADD COLUMN model_used TEXT")
    if "cid" not in chat_cols: c.execute("ALTER TABLE chat ADD COLUMN cid TEXT")
    ncols = [r[1] for r in c.execute("PRAGMA table_info(notifications)")]
    if "category" not in ncols: c.execute("ALTER TABLE notifications ADD COLUMN category TEXT")
    if "link" not in ncols: c.execute("ALTER TABLE notifications ADD COLUMN link TEXT")
    mcols = [r[1] for r in c.execute("PRAGMA table_info(memory)")]
    if mcols and "emb" not in mcols: c.execute("ALTER TABLE memory ADD COLUMN emb TEXT")  # IDEA-8 semantic recall
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
