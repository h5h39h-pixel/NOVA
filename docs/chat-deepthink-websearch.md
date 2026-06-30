# Chat: DeepThink + Web Search (and the microphone Stop control)

Core chat‑interface feature, owner‑requested 2026‑06‑30. Shipped in **M62**. This is the complete
spec — what it does, why it matters, how it works, the implementation, and the dependencies — so any
future developer (human or Claude) can understand, extend, or debug it without re‑reading the diff.

Tracked in `TASKS.md` as **CHAT‑1 / CHAT‑2 / CHAT‑3** (P1). See also `ROADMAP.md`,
`PROJECT_PLAN.md` §7, `STATUS.md`.

---

## 1. What it does

Three toggle/controls in the AI Chat page (`Chat()` in `static/js/pages.js`), styled like the existing
RAG / Compare / Speak toggles:

| Control | UI | Effect |
|---|---|---|
| **DeepThink** | `#dtbtn` — 🧠 DeepThink | When ON, the model is told to reason **step by step** before answering, and gets more output room. Better for hard / multi‑step questions. |
| **Web Search** | `#wsbtn` — 🌐 Search | When ON, the turn first runs a **live web search** and injects the top results (with source URLs) into the model's context, so answers can use **current** information and cite sources. |
| **Microphone Stop** | `#mic` — 🎤 ⇄ ⏹ Stop | The mic button now becomes an explicit **⏹ Stop** (red, pulsing) while recording and reverts to 🎤 after. Clear manual stop for voice input. |

All three are **per‑message / per‑session client state** — they do not change global settings.

## 2. Why it's important

- **DeepThink**: small local models (e.g. `qwen2.5:14b`) answer noticeably better on reasoning tasks
  when explicitly prompted to think step by step and given output headroom. It's a zero‑cost quality
  lever that works with **any** local model (no special "reasoning model" required).
- **Web Search**: the system is local‑first and otherwise offline, but real questions often need
  current facts (prices, releases, docs). An **opt‑in** web search keeps the default private/offline
  while making the assistant genuinely useful for live information — with citations the user can verify.
- **Microphone Stop**: voice input already worked but users couldn't tell how to stop it (the button
  stayed a 🎤). An explicit Stop control removes that confusion — a direct usability fix.

## 3. How it should work (behavioral spec)

**DeepThink**
- Toggling `#dtbtn` flips `deepThink` and adds/removes the `.p` (active) class; a toast confirms.
- On send, if on, the request body includes `deepthink: true`.
- Backend prepends a system message: *"Think carefully and reason step by step before answering…"* and
  raises `num_predict` to 1536 so the reasoning isn't truncated. Model‑agnostic.

**Web Search**
- Toggling `#wsbtn` flips `webSearch` similarly.
- On send, if on, the body includes `websearch: true`.
- Backend runs `web_search(prompt, 4)` (DuckDuckGo via `ddgs`), formats the top‑4 results into a
  context block (`title / snippet / Source: url`), and prepends it as context. Citations are returned
  in the `end` event's `sources` (with `url`), shown like RAG citations.
- **Online, opt‑in.** Off by default. If offline / no results, it streams a short
  *"(web search returned no results / offline)"* notice and answers from the model's own knowledge —
  the rest of the app stays offline‑capable.

**Microphone Stop**
- First click starts recording → button shows **⏹ Stop** (`.rec` red pulse).
- Second click (or clicking ⏹ Stop) stops recording → audio is POSTed to `/api/stt` (Whisper) →
  transcript fills the input; button reverts to 🎤. Shared by the chat mic and the agent mic via
  `_micUI(btnEl, recording)`.

## 4. Technical implementation

**Frontend** (`static/js/pages.js`, `Chat()`):
- State: `let … deepThink=false, webSearch=false;`
- Buttons added to the chat toolbar (`.chathd`) next to RAG: `#dtbtn`, `#wsbtn`.
- Handlers mirror the RAG toggle: flip state, toggle `.p`, toast.
- `send()` adds `body.deepthink` / `body.websearch` when on.
- Mic: `_micUI()` helper swaps button text 🎤 ⇄ "⏹ Stop" and the `.rec` class; `dictate()` calls it on
  start and in `onstop`.

**Backend**:
- `nova/api/chat.py` → `/api/chat-send` reads `deepthink` / `websearch` from the JSON body and passes
  them to `stream_chat_send(...)`.
- `nova/services/chat.py` → `stream_chat_send(..., deepthink=False, websearch=False)`:
  - DeepThink: `run_model()` prepends the reasoning system message and sets `body["options"] =
    {"num_predict": 1536}`.
  - Web Search: in `work()`, before running the model, calls `web_context(prompt, 4)` and appends the
    block to `context`; `sources.extend(web_src)` (use `.extend`, **not** `+=`, or the closure rebinds
    `sources` and pyflakes/`UnboundLocalError` bites).
- `nova/services/web_search.py` (new):
  - `web_search(query, k=4) -> [{title, url, snippet}]` — `from ddgs import DDGS; DDGS().text(...)`.
    Returns `[]` on any failure (offline, import error) so it never breaks a chat turn.
  - `web_context(query, k=4) -> (block_str, [{doc, url}])` — formats results + citations.

**Tests**: `tests/test_services_deep.py::test_web_search_mocked` (mocks `ddgs.DDGS`, hermetic — the
autouse no‑network fixture still applies). Chat page render‑verified via Playwright (buttons present,
toggle active, zero console errors).

## 5. Dependencies & requirements

- **`ddgs`** (DuckDuckGo Search, **no API key**) — pinned `ddgs==9.14.4` in `requirements.txt`, ranged
  in `requirements.in`. First new runtime dependency since the lock; verified to clean‑install via
  `scripts/ci_local.py`. Pulls `primp`, `h2`, `brotli`, `fake-useragent`, `socksio` (all wheels).
- **Internet** — only when Web Search is toggled on. Everything else stays offline‑capable.
- **Ollama** — DeepThink needs no new model; works with the current local models.
- **Whisper STT** (`faster-whisper`, already present) — the mic Stop fix is UI‑only; the `/api/stt`
  path is unchanged.

## 6. Extension ideas (not yet built)
- DeepThink: optionally route to a dedicated reasoning model (e.g. `deepseek-r1:14b`) and render its
  `<think>` trace collapsibly.
- Web Search: fetch + summarize the top result's full page (not just the snippet); pluggable engines.
- Persist the toggles per conversation; expose a result count / quality control.
