# Test coverage (HON-3)

Honest coverage measurement of the **hermetic** pytest suite over `nova/` + `server.py`.
(The live frontend tests and the eval scripts are NOT counted — they exercise more at runtime, so the
true exercised fraction is higher, but this is the number the automated suite guarantees.)

## How to run
```
python -m coverage run -m pytest -q
python -m coverage report          # text summary
python -m coverage html            # htmlcov/index.html (browsable)
```
Config in `.coveragerc` (source = `nova,server`; omits tests/scenarios).

## Baseline — 2026-06-30: **49%** total (3456 stmts, 1749 missed)

**Well covered (≥80%):** `core/safety` 100%, `services/metrics` 92%, `core/http` 92%, `core/db` 88%,
`services/ollama` 88%, `core/secretbox` 83%, `services/settings` 82%, `services/audit` 82%,
`services/web_search` 82%, `services/backup` 78%, `services/notifications` 77%.

**Weakly covered (≤40%) — mostly GUI/process/live‑only code, hard to unit‑test hermetically:**
`services/browser` 17%, `services/insights` 20%, `services/screen` 21%, `core/process` 28%,
`services/jobs` 30%, `core/errors` 33%, `services/chat` 37%, `services/tts` 38%, `services/training` 38%,
`services/kb` 40%, `services/schedules` 41%. `server.py` 47%.

## Honest read
- 49% is a **real, modest** number — the security/data/util core is well tested; the
  screen/browser/process/agent‑heavy paths are not (they need a real desktop/services, which the
  hermetic suite deliberately avoids).
- This is the gap HON‑2 (real GUI integration test) and HON‑7 (larger eval batteries) target — they
  raise *effective* confidence even where unit coverage is structurally low.
- Coverage is **not in the gate** (it would need a target threshold + the live deps); run it manually
  after meaningful changes and watch for regressions in the well‑covered modules.
