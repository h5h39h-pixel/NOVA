# Perception & Control (Phase 8)

Owner‑requested 2026‑06‑30. Gives the system **perfect awareness of the screen/window layout** and
**precise control** of mouse + keyboard, plus a unified **read & understand** tool. Exposed three ways:
**agent tools**, **chat commands**, and **API endpoints**. Tracked as **PC‑1…6** (P1).

## Components

### PC‑1 — Read & Understand  (`nova/services/understand.py`)
OCR + VLM for files / images / screenshots / the live screen → the text present, what it shows, its
purpose, and notable details.
- `understand(path|region, question)` · `understand_image` (OCR via `extract_text` + VLM via
  `screen.vlm_image`) · `understand_file` (document → extract + LLM summary).
- `POST /api/understand {path|region|question}` · agent tool `understand {path}` · **image chat uploads
  are auto‑enriched** with a VLM description + OCR, so "read this" / "describe this" just works.

### PC‑2 — Window & screen awareness  (`nova/services/control.py`)
Stdlib `ctypes` (Win32) + `psutil`; **per‑monitor DPI‑aware** for true pixels.
- `active_window()` → `{hwnd, title, process, pid, rect{x,y,w,h}}`
- `list_windows()` → all visible titled windows with process + rect
- `screen_info()` → `{primary, virtual, dpi, scale}` (e.g. 3840×2160 @144dpi, scale 1.5)
- `awareness()` → active + windows + screen in one call
- `GET /api/control/{active,windows,screen,awareness}`

### PC‑3 — Element detection  (`uiautomation`)
- `find_element(name, partial=True)` → matches with `{name, type, rect, center}` (center is ready to
  click). `click_element(name)` finds + clicks the first match.
- `POST /api/control/find {name, partial}`

### PC‑4 — Precise mouse control  (`pyautogui`, DPI‑aware)
- `move_mouse(x,y)` · `click(x,y,button,double)` · `drag(x1,y1,x2,y2)` · `scroll(amount)`
- `POST /api/control/mouse {action:move|click|drag|scroll, …}`

### PC‑5 — Precise keyboard control
- `press_keys('ctrl+s' | ['ctrl','s'] | 'enter')` · `type_text(text)` (clipboard paste → Unicode/Arabic safe)
- `POST /api/control/key {keys}` or `{text}`

### PC‑6 — Surfaces
- **Agent tools:** `understand`, `screen_awareness`, `find_element`, `control {action,…}`.
- **Chat commands** (handled before the model, instant): `where am i` / `what's open` / `list windows`;
  `move mouse to X,Y`; `click X,Y` / `double click X,Y`; `click the "<name>" button`; `read this` /
  `describe this` (with an attached file/image).
- **API:** everything under `/api/understand` and `/api/control/*`.

## Safety & privacy
- **Mutating control** (`/api/control/mouse|key|click-element`, agent `control`) is gated by
  `exec_allowed()` — allowed on localhost by design, requires `allow_remote_exec` on the LAN — and
  **audited** (`actor=control` / `agent`). Read‑only awareness is ungated (local, no side effects).
- Windows‑only (degrades to errors elsewhere). DPI awareness is set process‑wide at import so all
  coordinates are real physical pixels.

## Dependencies
- New: **`uiautomation==2.0.29`** (UI Automation; pulls `comtypes`) — pinned in `requirements.txt`,
  ranged in `requirements.in`, clean‑install verified via `scripts/ci_local.py`.
- Reused (already present): `pyautogui`, `pyperclip`, `psutil`, `mss`, qwen2.5‑VL.

## Tests / verification
- Hermetic: `test_control_awareness`, `test_control_find_element_safe`, `test_control_api_readonly`
  (read‑only; no input ever sent in tests).
- Live‑verified: awareness endpoints (true 4K/DPI), a safe no‑op `move_mouse`, key parsing, and the
  "where am i" chat command (render‑verified, zero console errors).

## Notes / limits
- Coordinate control is pixel‑exact; element detection depends on the app exposing UIA names (most
  native + Electron + browser chrome do; some custom‑drawn UIs don't).
- `act_on_screen` (vision‑based click) remains for when there's no UIA name — complementary to PC‑3/4.
