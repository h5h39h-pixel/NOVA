# Security Model — Nova / AI Control Center

This is a **local, single-user** control center that can run commands and drive the desktop. That
power is the point — and the risk. This document is the honest security posture and how to stay safe.

## Threat model (what this is / isn't)
- **Designed for:** one trusted user, on their own machine, bound to `localhost`.
- **Not designed for:** the public internet, shared/multi-tenant use, or untrusted networks.

## Defaults (secure out of the box)
- **Binds to `127.0.0.1` only.** It is *not* reachable from other devices unless you explicitly
  enable **both** token auth and LAN access in Settings.
- **Auth off** by default (safe because localhost-only). When enabled, the access token is stored
  **hashed (SHA-256)** — the raw token is shown once for you to save and never persisted in clear.
- **HTTPS off** by default (opt-in via `config.json` → `https_enabled: true`). On a LAN without
  HTTPS, traffic is unencrypted — only use on trusted networks.

## Command-execution surface (the big one)
The Terminal (`/api/exec`) and the Agent's `run_command` tool execute **arbitrary PowerShell**.
This is intentional for a local control center, but it is effectively remote code execution if
exposed.

- **Mitigation:** execution is **always allowed on localhost**, but when the server is exposed on
  the LAN (auth **and** `lan_access` on), it is **blocked unless you explicitly set
  `allow_remote_exec: true`** in Settings. Default is off.
- The agent keeps a destructive-command denylist for non-full-access runs, but treat it as a
  speed-bump, not a sandbox. **Do not enable `allow_remote_exec` on an untrusted network.**
- For risky/unknown scripts, prefer running inside WSL2 or a container, not the host.

## Secrets
- **`config.json` is git-ignored** (it holds machine paths; commit `config.example.json` instead).
- **Auth token:** hashed at rest. **`cloud_api_key`:** currently stored in plaintext in the SQLite
  `settings` table and redacted in API responses. _Planned (TASKS T-016 follow-up): optional
  at-rest encryption._ Until then, protect the DB file (`<workspace>/data/control.db`).
- Credential stores are deny-listed for the agent's `read_file` (`.ssh`, `.aws`, `.env`,
  `credentials`, private keys, …).

## Data safety
- **Automatic daily DB snapshots** → `<workspace>/data/backups/` (last 14 kept); manual snapshot via
  `POST /api/backup/snapshot`; full export/restore in Settings.
- Background jobs run under a Windows **Job Object** so they can't orphan — but they are also killed
  if the server restarts (by design).

## Hardening checklist (if you ever expose it)
1. Enable **token auth** before enabling **LAN access**.
2. Leave **`allow_remote_exec` off** unless you fully trust every device on the network.
3. Turn on **HTTPS** with one command: `python scripts/https.py enable` (generates a self-signed
   cert and flips `https_enabled`), then restart the server → `https://localhost:8900`. Off again:
   `python scripts/https.py disable`.
4. Keep the machine and `data/control.db` physically/OS-secured.
5. Prefer a VPN/SSH tunnel over raw LAN exposure.

## Reporting
This is a personal project — file issues via the in-app **Bug Reports** page.
