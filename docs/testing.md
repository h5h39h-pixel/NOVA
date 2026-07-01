# Testing — what's covered, how deep, and how to run it

Nova's tests are in three layers. The point of this doc is **honesty about depth**: which tests are real
assertions of behavior vs. which are smoke/presence checks, and where the genuine risk still lives.

## How to run

```
python scripts/check.py            # the gate: pyflakes + node --check + pytest (hermetic + live-frontend)
python run_tests.py                # live integration suite (needs the server on :8900) → 42/42
python -m coverage run -m pytest && python -m coverage report   # coverage (~57%)
# outcome/eval scripts (NOT in the gate — run after model/dep/prompt changes):
python scripts/agent_eval.py --record       # agent goal battery
python scripts/rag_eval.py                  # RAG precision@1 / MRR
python scripts/stt_eval.py --record         # STT word error rate (EN + AR)
python scripts/gen_eval.py                  # image generation (SDXL)
```

## Layer 1 — hermetic unit tests (`tests/`, network-blocked)

Fast, deterministic, no live services. Highlights:

| File | What it really tests |
|---|---|
| `test_core.py` | settings/history/WAL, error persistence, **`_supervise` restart-on-crash** (IDEA-10). |
| `test_services.py` | chat store, KB chunk/folder/text ingest, backup, training-progress parse, **memory** (dedupe/rank/pin), **macro recorder** step-building, **quality** record/summary, **control macro action**, **screen_if** region/absent. |
| `test_services_deep.py` | run_action branches, **web-search fencing + injection detection**, job reconcile. |
| `test_api.py` | endpoint contracts incl. security headers, memory/quality/macro CRUD, agent save-workflow. |
| `test_screen_vision.py` | every capture route gated on opt-in; **SV-2 narrate gate**, **SV-4 keystroke gate + master `allow_input_capture` gate + reconcile stop** (privacy). |
| `test_coverage_boost.py` | automodel routing (all branches), PowerShell quoting, analytics/insights/search/media/owui routes. |

### The deep safety/edge/failure suites (added M105.6)

These were written specifically to **test the dangerous, weak, and failure paths** — and they found real bugs.

- **`test_dangerous.py`** — the safety-critical surfaces:
  - The **panic kill-switch** blocks *every* mutating control action (parametrized over all 8).
  - The **protected-window guard** blocks click/type/keys when the focused window looks like a password
    manager / bank / auth prompt; configurable; clears on a normal window.
  - The **credential-store denylist** across every reader (paths, folder-ingest, file-read API) — incl.
    forward-slash + bare-dir variants.
  - The **LAN exec gate**, the **destructive-command denylist** (many real variants + false-positive
    guards), the **agent GUI-control gate**.
  - The **prompt-injection detector's honest limits** — it asserts the detector CATCHES obvious attempts
    and **MISSES a paraphrase** (encoded in a test so nobody over-trusts it).
- **`test_edges.py`** — boundaries: memory dedupe/empty/unicode/**semantic recall**, screen-memory
  retention at keep=0 and keep≫count, quality divide-by-zero, KB chunking on empty/huge, macro backspace
  + event cap, automodel single-model fallback.
- **`test_failures.py`** — failure injection: **embeddings/Ollama down** → graceful empty; unreachable
  service → `http_ok` False; malformed agent-action JSON; **bad request bodies return clean errors, not
  500s**; oversized output truncation; recall caps; guard survives a settings-read exception; `understand`
  blocks credential paths.

**Bugs these deep tests caught and fixed (real, not theoretical):**
1. **Credential-denylist bypass** — `.git\config` matched only backslash paths; a forward-slash path
   (`.git/config`) slipped through. Fixed: `is_credential_path` is now separator-agnostic + segment-aware.
2. **`screen_memory_keep: 0` ignored** — `or 50` clobbered a valid "keep none" to 50. Fixed.
3. **Macro save fallback bug** — an explicit empty `steps:[]` fell back to the leftover recorded buffer.
   Fixed to respect an explicit list.
4. **Semantic recall silently disabled** — `recall()` called `get_settings()` which wasn't imported →
   `NameError` swallowed → always keyword. Fixed the import.

## Layer 2 — live integration (`run_tests.py`, needs the server)

Real HTTP against a running server: endpoint round-trips, chat stream, agent dry-run, WebSocket. 42/42.
Plus a **render sweep** (`scripts/…/rendersweep.py` pattern): loads all 22 routes in headless Chromium and
asserts **zero console errors**.

## Layer 3 — outcome/eval scripts (not gated)

These measure *quality*, which is model- and run-dependent, so they're not in the commit gate — run them
after changing a model, dependency, or prompt, and record to the quality dashboard (`--record`):

- `agent_eval` 9/9 (safe goals) · `rag_eval` 11/12 (overlapping corpus) · **`stt_eval` EN ~0.07 WER
  (~93%) / AR ~0.26 (~74%)** · `gen_eval` (SDXL image) · `nova_eval` (trained model identity/GPU/Arabic).

## Honest gaps that remain (see `docs/honest-state.md`)

- Coverage is **~57%**; the riskiest modules are still the least covered (`control.py` 57%, `browser.py`
  ~17%, `screen.py` ~21%) because they drive real hardware and can't be exercised headlessly.
- The eval batteries are **small samples** — credible, not statistically strong. STT numbers are a
  TTS→STT round-trip, not clean ASR.
- No **soak/longevity** test (24h loops, memory growth, VLM queue). No real **multi-app agent** test.
- Video generation and training-output quality are verified **shallowly** (a valid file is produced /
  orchestration parses) — not "the result is good."
