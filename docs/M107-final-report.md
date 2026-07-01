# M107 — Final Report: five reliability features + soak

_Recorded 2026-07-01. Single-user · local-only. Authoritative record for the M107 work batch._

This report documents, in full, the five reliability features requested after the honest self-report,
the tests, the 24-hour soak outcome, the bugs found and fixed, ideas still pending, and the complete
project state. Companion docs: `docs/observability.md` (design), `BUILD_LOG.md` (M107 entry),
`TASKS.md` (REL-1…5), `STATUS.md` (live snapshot).

---

## 1 · Features built and completed

All five are built, gated (`scripts/check.py` green), tested, and — where possible — verified live
against the running server. All are layered on the unified event log (no new silos), and all are
local / read-only-or-notify (nothing weakens a safety control).

### REL-1 · Agent session replay ✅ (live-verified)
- **Files:** `nova/services/replay.py`; `GET /api/agent/runs`, `GET /api/agent/runs/{run_id}`
  (`nova/api/agent.py`); Ops-Center "🎬 Agent Session Replay" card (`static/js/pages-system.js`).
- **How:** `agent_run` tags every step with a `run_id` and writes it to the event log via `_rlog()`
  (`goal → thought → action → observation → final`). `list_runs()` groups them into runs;
  `get_run(run_id)` returns the full chronological timeline.
- **Live proof:** a real agent run recorded **8 ordered steps**, retrieved by id via the API — kinds
  in order `goal, thought, action, observation, thought, action, observation, final`.

### REL-2 · Anomaly alerts from the event log ✅ (tested)
- **Files:** `nova/services/anomaly.py`; supervised `anomaly_loop` in `server.py` (registered in the
  `_supervise` fleet; 60 s cadence after a 60 s warm-up).
- **Signals:** `error_spike` (≥15 error/critical events in 10 min), `loop_stall` (metrics loop silent
  >180 s), `rss_climb` (>40 MB/h sustained over ≥20 min of samples).
- **Behaviour:** each finding raises a notification + an `alert` event; throttled 15 min per kind so a
  persistent condition alerts once, not every tick. Read-only + notify-only.

### REL-3 · Dry-run diff before destructive actions ✅ (live-verified)
- **Files:** `nova/services/preview.py`; `POST /api/agent/preview`; wired into `confirm.gate(…, preview=…)`
  (`nova/services/confirm.py`) and rendered in the confirmation popup (`.confirm-diff` / `.confirm-will`
  in `static/js/pages-workspace.js` + `static/css/app-extras.css`).
- **What it shows:** `write_file` → a unified diff vs disk (or "CREATE … N bytes" for a new file);
  `run_command` → the command + a destructive flag (`danger_reason`); `delete_file` / `control` → a
  plain-language effect summary. Never touches disk.
- **Live proof:** destructive `Remove-Item -Recurse -Force` flagged `destructive: true`; new-file write
  previewed as "CREATE … (8 bytes, 2 lines)".

### REL-4 · Resource budget per agent run ✅ (tested)
- **Files:** `agent_max_seconds` (default 300) / `agent_max_tokens` (default 0 = unlimited) in
  `DEFAULT_SETTINGS` (`nova/core/db.py`); budget checks at the top of each step in `agent_run`.
- **Behaviour:** the run ends cleanly with a clear final — "Agent stopped: time budget reached (Ns)."
  or "… token budget reached (~N tokens)." — and the outcome is recorded by replay.

### REL-5 · Backup-restore drill in CI ✅ (tested)
- **File:** `tests/test_backup_restore.py`. Seeds conversations/chat/schedules/workflows →
  `make_backup()` → wipes the tables → `restore_backup()` → asserts the data returned; plus a test that
  a malformed bundle is rejected. Guards against "backups that never restore."

---

## 2 · Tests that passed

- **Full hermetic suite:** `python -m pytest` → **224 passed, 12 skipped** (skips = opt-in live tests:
  `NOVA_LIVE_TESTS` screen/browser + Playwright frontend when its preconditions aren't met).
- **Quality gate:** `python scripts/check.py` → **PASSED** (pyflakes + `node --check` on all 10 JS
  modules + pytest). Verified green at pre-commit **and** pre-push.
- **New this batch — `tests/test_features.py` (12 tests, all pass):**
  - Preview ×5: create-new, overwrite-shows-diff, destructive-command-flagged, benign-command-not-flagged,
    delete-reports-target.
  - Replay ×2: lists-and-reconstructs-run (order + goal/final), isolates-runs (no cross-run leakage).
  - Anomaly ×3: detects-error-spike, error-spike-is-throttled, quiet-when-healthy.
  - Budget ×2: token-budget-stops-run, time-budget-stops-run.
- **`tests/test_backup_restore.py` (2 tests):** roundtrip + bad-bundle rejection.
- **`tests/test_confirm.py`:** updated for the new `gate(…, preview=…)` signature — passes.
- **Frontend sweep (`tests/test_frontend.py`, live Chromium):** extended to the `diagnostics` + `events`
  routes → **zero console errors** across all swept routes.

---

## 3 · Final status of the 24-hour soak

The longevity soak (`scripts/soak_test.py --hours 24`) samples the server process every ~30 s for RSS
(leak slope), request count, HTTP errors, runtime errors, and background-loop liveness.

- **First run — ran clean for ~7h before it was intentionally interrupted:**
  - **173,176 requests · 0 HTTP errors · 0 runtime errors**
  - **RSS slope −0.3 MB/h (no leak; memory flat/declining)**
  - **0 dead-loop samples** (all background loops alive throughout)
  - *Interruption cause:* restarting the server to load the new M107 endpoints orphaned the soak's
    target PID (the soak binds to the PID it found at startup). Not a fault — a planned deploy.
- **Second run — relaunched fresh against the new server, then stopped on request:**
  - **~2.5h · 61,672 requests · 0 HTTP errors · 0 runtime errors**
  - **RSS slope −8.3 MB/h (no leak)** · **0 dead-loop samples** · 295 samples
  - Stopped cleanly at the operator's "stop" instruction.

**Verdict:** across ~9.5 hours of combined runtime and ~235k requests, **zero errors, zero leaks, zero
dead loops.** A full uninterrupted 24h pass was not completed — real wall-clock time cannot be
fast-forwarded — but the evidence over 9.5h is strongly stable. Re-running `soak_test.py --hours 24`
and leaving it undisturbed for a full day would produce the final 24h stamp. Observable live via
`../data/logs/soak_progress.json`.

**Feature soak** (`scripts/feature_soak.py --load 8`): all **16 components PASS** — 0 errors, 0 leaks,
0 slowdowns, 0 dead loops; the concurrent load generator did **11,807 requests / 0 errors** during the
soak. Report: `../data/logs/feature_soak_report.{json,md}`.

---

## 4 · Issues found and fixed (this batch)

1. **Session-replay goal step silently dropped** — `_rlog("start", goal, run_id, 0, kind="goal")` passed
   `kind` both positionally (first arg) and as a keyword → `TypeError`, which `_rlog`'s own try/except
   swallowed, so the goal step never reached the log and replay couldn't show the goal. **Fix:** call
   `_rlog("goal", goal, run_id, 0)`. Verified live (goal now first step).
2. **Confirm test broke on the new preview arg** — `test_confirm.py` monkeypatched `gate` with the old
   2-arg signature; adding `preview=` made the lambda raise "unexpected keyword argument". **Fix:**
   updated the stub to `lambda action, detail="", preview=None: …`.
3. **Deploy hazard noted (not a code bug):** restarting the server orphans a running soak's PID. Handled
   by relaunching the soak after the restart; documented here so it isn't mistaken for a regression.

Prior-batch bugs (M106.1, still relevant context): `agent_run` had no `return` (always None) and
returned None when the model was unreachable — both fixed there; M107's budget/replay code builds on
that corrected `agent_run`.

---

## 5 · Ideas still pending

- **Full uninterrupted 24h soak stamp** — the only genuinely open item; needs ~24 real hours undisturbed.
- **Anomaly loop live-fire confirmation** — the detectors are unit-tested; a live end-to-end trip
  (inject a real error burst and observe the notification) would upgrade it from "tested" to
  "live-verified" like replay/preview.
- **Replay diffing / export** — compare two runs, or export a run as JSON/markdown for sharing.
- **Preview for more tool types** — currently write_file/run_command/delete_file/control; could extend to
  schedule/workflow mutations.
- **Budget telemetry** — surface tokens-used / seconds-used per run in the replay UI (data is already
  estimated in `agent_run`; just not displayed).
- **Anomaly thresholds as settings** — they're constants at the top of `anomaly.py`; could be exposed in
  Settings for tuning.
- **Hosted-CI result visibility** — `gh` CLI is unauthenticated locally, so the GitHub Actions result
  can't be read from here; the local gate is the authoritative signal. (Owner-credential boundary — not
  to be worked around.)

None of these block anything; the shipped features are complete and green.

---

## 6 · Complete project state

- **Repo:** `github.com/h5h39h-pixel/NOVA` (private). Branch `main` at `e01da76` — M107 committed and
  **pushed** (gate passed at pre-commit and pre-push). Working tree clean before this report's doc edits.
- **Server:** FastAPI on `localhost:8900`, running. Health OK, metrics loop alive. Background fleet:
  metrics · status · scheduler · backup · narration · **anomaly** (new), all under `_supervise`
  auto-restart.
- **Quality gate:** green. Hermetic tests **224 passed / 12 skipped**. Live suite `run_tests.py` 42/42
  and self-test 13/13 remain the live guardrails (run against the running server).
- **Constraints upheld:** single-user, local-only; no cloud/telemetry/inbound-remote/LAN/multi-user; no
  safety control disabled or overridden; no credential stores read; owner git credentials untouched.
- **Source-of-truth files updated:** `STATUS.md` (dated 2026-07-01, M107 section), `BUILD_LOG.md`
  (M107 entry), `TASKS.md` (REL-1…5 ✅), `docs/observability.md` (Reliability-features section), and
  this report.
- **Honest bar:** REL-1 and REL-3 are **live-verified**; REL-2, REL-4, REL-5 are **unit-tested** (not
  yet live-fired). Treat ✅ as "verified to its stated bar," per the project's honesty rule.

### Definition-of-done checklist (M107)
- [x] All 5 features implemented
- [x] Unit tests for each (+14 new)
- [x] `scripts/check.py` green (pyflakes + node --check + pytest)
- [x] Frontend routes render with zero console errors (incl. new UI)
- [x] Live verification where feasible (replay, preview)
- [x] 24h soak run (≥9.5h clean; full 24h stamp pending wall-clock only)
- [x] Feature soak 16/16
- [x] Docs updated + committed + pushed
- [ ] Full uninterrupted 24h soak stamp (open — time only)
