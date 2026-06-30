# 🔒 CORE PRINCIPLE — Single‑User · Local‑Only (PERMANENT, NON‑NEGOTIABLE)

> This is a **permanent, core rule** of the project. It overrides any feature request that conflicts
> with it. Every file, every code path, every doc must respect it.

Nova is, and will always be:

1. **Single‑user.** One operator (the owner). **No** multi‑user, accounts, roles, RBAC, or sharing — ever.
2. **Local on the owner's machine.** All AI, data, models, and processing run on this PC. Data lives in
   the local SQLite DB + local files. **No cloud, no telemetry, no analytics, no external services for
   core function.**
3. **No remote/inbound access to the running system.** The server binds **localhost only** by default.
   It is **not** exposed to the LAN/internet for control. No remote desktop, no remote command, no
   inbound API for outsiders.
4. **No phone control.** No mobile remote‑control, no phone pairing, no companion‑app control surface.
5. **No external access.** Nothing outside this machine may drive, read, or control Nova.

## The two narrow, explicit exceptions (owner‑chosen, opt‑in, OUTBOUND only)
These are **outbound** queries the owner explicitly triggers — never inbound access to the system:
- **Web Search** (chat/agent toggle, off by default): an outbound DuckDuckGo query when the owner asks.
  Results are treated as untrusted data. Disable it to be fully offline.
- **Source control (git):** pushing the *code* to the owner's private repo is backup/versioning of
  source files only. It is **not** runtime access to the system, carries **no** secrets (config/keys/DB
  are git‑ignored), and the running app remains localhost‑only regardless.

Everything else stays on the machine. If a future feature would require inbound remote access, a phone
control surface, multi‑user, or a cloud dependency for core function — **it is rejected by this rule.**

## How it's enforced
- **Code:** the server binds `127.0.0.1` unless the owner explicitly sets `lan_access` **and** an auth
  token; command/GUI control additionally require `allow_remote_exec` on the LAN and are off by default.
  `config.py` / `server.py` carry this comment; `nova/services/settings.py::exec_allowed()` gates it.
- **Docs:** referenced from `CLAUDE.md`, `STATUS.md`, `ROADMAP.md`, `PROJECT_PLAN.md`, `WORKFLOW.md`.
- **Excluded forever (do not build):** multi‑user/RBAC · remote/LAN control surface · phone control ·
  cloud hosting/scaling · telemetry · any inbound external access.
