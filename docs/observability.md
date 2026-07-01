# Observability — the unified Event Log + Ops Center

Nova records **everything that happens** in one place. Errors, operations, system events, alerts,
notifications, and API access all flow into a single structured store — searchable, filterable, and
exportable — with a smart Ops Center on top for discovery.

## The one store: `event_log`

Every event is a row in the `event_log` SQLite table (`nova/core/eventlog.py`):

| field | meaning |
|---|---|
| `ts` | unix time |
| `level` | `debug` · `info` · `warn` · `error` · `critical` |
| `category` | `error` · `exec` · `file` · `network` · `system` · `action` · `agent` · `security` · `automation` · `media` · `alert` · `api` |
| `source` | where it came from (module.func, or `METHOD /path`) |
| `message` | short human summary |
| `detail` | longer text (params, output snippet) |
| `trace` | full stack trace (errors only) |
| `actor` | `user` · `agent` · `system` · `automation` · … |
| `status` | `ok` · `warn` · `fail` |
| `context` | arbitrary JSON (status code, ms, ids, …) |

**Retention:** capped at `RETAIN = 50000` rows — pruned automatically (every ~500 inserts + a hard
prune in the 6-hourly backup loop) so the log can never fill the disk. Error events are **throttled**
per (type+message) to 1 / 30 s so a broken loop can't flood the log.

## What flows in (complete coverage)

Everything is bridged into the one store — nothing is a separate silo:

| Source | Bridge | Category |
|---|---|---|
| **Exceptions/crashes** (with stack trace) | `errors.record()` → `eventlog.record_exception()` | `error` |
| **Audit trail** (commands, agent, control, security, config) | `audit()` → `eventlog.log()` | derived (exec/security/agent/…) |
| **Notifications / alerts** | `add_notification()` → `eventlog.log()` | `alert` |
| **System events** (server start/stop, config change) | explicit `eventlog.log("system", …)` | `system` |
| **All API requests** (external ops, file/network calls, user actions) | HTTP middleware → `eventlog.log_request()` | `api`/`file`/`exec`/`network` |

The request middleware logs mutations (POST/PUT/DELETE) at `info`, non-poll reads at `debug`, 4xx at
`warn`, 5xx at `error` — and **skips high-frequency polls** (`/api/metrics`, `/api/health`,
`/api/processes`, notifications, events, quality, vision stream/frame/mouse) so the log stays a record of
*real* operations, not thousands of health checks.

## API

- `GET /api/events` — filter/search: `level, category, source, actor, status, q, since, until, limit, offset` → `{total, items}`
- `GET /api/events/{id}` — one event (full trace + context)
- `GET /api/events/stats?hours=24&buckets=48` — counts by category + level + a bucketed timeline
- `GET /api/events/meta` — the level/category vocabularies
- `DELETE /api/events` — clear
- `GET /api/events/export?format=json|csv` — download the (filtered) log
- `GET /api/issues` — **auto-discovered issues** (recurring errors, failing ops, services down)
- `POST /api/issues/file` — turn an issue into a bug report (diagnostics → tasks)
- `GET /api/ops/report` — one JSON diagnostics report (issues + event stats + top errors)

## UI

- **Event Log** (`#/events`, `pages-events.js`) — the explorer: full-text search, category/level/time
  filters, category chips, a **timeline** (errors in red), and expandable rows showing the stack trace +
  context. Live-updates on new audit/notification events.
- **Ops Center** (`#/diagnostics`, the merged hub) — Server Health · Recent Errors · **Discovered
  Issues** (auto-scan + "file as bug") · Self-Test · **Event-log summary + export** (JSON/CSV/report) ·
  **Bug Reports** (file/resolve) · Quality Trend. The old **Audit** page redirects here → the Event Log
  (audit is now part of it); the old **Bugs** page redirects into the Ops Center.

## Design principles

- **One store, many bridges** — never a new silo; every subsystem calls into `eventlog`.
- **Bounded by construction** — retention cap + error throttle (learned from the disk-growth incident).
- **Best-effort** — logging never raises into the caller (`try/except` around every bridge).
- **Layered** — the store is bottom-layer (`nova/core/eventlog.py`, depends only on `nova.core.db`);
  services/API/UI read from it. Issue discovery (`nova/services/issues.py`) is read-only analysis on top.
- **Clean + modular** — short lines, one responsibility per module (`eventlog` store, `issues`
  discovery, `api/events` + `api/ops` routers, `pages-events.js` explorer).
