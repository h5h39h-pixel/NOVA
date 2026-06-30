# Click-to-act reliability — evaluation & decision (T-032)

## Current state
Screen "click-to-act" (`act_on_screen` / `/api/screen/{act,click,type}`) works by asking the
qwen2.5-VL vision model for pixel coordinates of a described element, then driving the mouse/keyboard
with `pyautogui` (+ clipboard paste for text). It is **best-effort and unreliable** for two real reasons:

1. **Grounding imprecision** — a 7B vision model returns approximate coordinates; at 4K the located
   point often misses the target by enough to click the wrong thing.
2. **Foreground-focus rules** — Windows 11 forbids a *background* process from stealing foreground
   focus, so synthetic input can land in the wrong window. (Documented in the workspace `CLAUDE.md`:
   click *inside* the window first to activate it, then type.)

## Options evaluated
| Option | Pros | Cons |
|---|---|---|
| **A. UI Automation via `pywinauto`** (target controls by name/automation-id; `AttachThreadInput` to focus) | Deterministic, robust, no pixel guessing; proper focus handling | Windows-only; only works for apps exposing UIA (most native/Win32/WinUI do; some Electron/games don't); new dependency + non-trivial integration |
| **B. Stronger grounding model** (e.g., a larger/се grounding-specialized VLM) | Keeps the "describe it" UX; works on any visual UI incl. canvas/games | Heavier VRAM/latency; still pixel-based → never as exact as UIA; model availability |
| **C. Hybrid** — try UIA by control name; fall back to vision grounding | Best of both: deterministic where possible, visual fallback | Most engineering effort |

## Decision
**Park as best-effort for now; plan the hybrid (C) as the eventual fix.**
- The feature is honestly labeled best-effort in the UI and `ROADMAP.md`; it is not on the critical
  path for the product's core value (chat, agent, KB, training, screen *reading*).
- The right fix is **Option C**: add `pywinauto` UI Automation as the primary path (find control by
  name/automation-id, `AttachThreadInput` + `SetForegroundWindow` to focus, invoke/click/type), and
  keep the current vision-grounding path as a fallback for non-UIA surfaces.
- **Not done now** because it's a multi-day effort with platform-specific edge cases, and lower
  priority than the hardening this plan prioritizes. Tracked as a future enhancement.

## If/when implemented
- Add `pywinauto` to `requirements.in`/`.txt`.
- New `nova/services/uia.py`: `find_control(title_or_name)`, `focus(hwnd)`, `invoke/click/set_text`.
- `act_on_screen` tries UIA first (by the instruction text → control name match), falls back to the
  existing vision+pyautogui path; report which path was used.
- Add a unit/integration smoke test against a known app (e.g., Notepad) on the Windows CI runner.
