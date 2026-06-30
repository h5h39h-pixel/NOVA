# -*- coding: utf-8 -*-
"""HON-2 — real GUI integration test for the Perception & Control stack.

⚠️ DANGER / KNOWN-UNSAFE ON WIN11: this drives a live GUI app. Win11's UWP Notepad is a SINGLE shared
window with multi-tab session restore, so launching `notepad.exe` opens a tab inside ANY Notepad you
already have open, and there is no safe automated way to close only our tab. An earlier version of this
script force-killed Notepad and risked the user's other open tabs — DO NOT do that.

Current behavior is NON-DESTRUCTIVE: it requires Notepad to be CLOSED first (refuses to run otherwise),
types into a fresh instance, reads it back via UIA, and then LEAVES Notepad open for the user to close
manually. It does NOT taskkill. On-demand only; needs the real desktop; not in CI.

Conclusion from running it (2026-06-30): the type+readback is FLAKY on UWP Notepad (session-restore /
focus / multi-tab) — this confirms the click-to-act fragility caveat. A reliable GUI integration test
needs an ISOLATED, disposable target app (future work). Run:  python scripts/gui_eval.py
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nova.services import control as C  # noqa: E402

MARKER = "NOVA-GUI-TEST-7731"


def _read_notepad_text():
    """Read the Notepad edit area's text via UI Automation (handles classic + UWP Notepad)."""
    try:
        import uiautomation as auto
    except Exception as e:
        return None, f"uiautomation unavailable: {e}"
    try:
        np = None
        for w, _ in auto.WalkControl(auto.GetRootControl(), includeTop=True, maxDepth=2):
            try:
                if w.ControlTypeName == "WindowControl" and "Notepad" in (w.Name or ""):
                    np = w; break
            except Exception:
                continue
        if not np:
            return None, "Notepad window not found"
        for c, _ in auto.WalkControl(np, includeTop=True, maxDepth=12):
            try:
                if c.ControlTypeName in ("EditControl", "DocumentControl"):
                    try:
                        return c.GetValuePattern().Value, None
                    except Exception:
                        try:
                            return c.GetTextPattern().DocumentRange.GetText(-1), None
                        except Exception:
                            continue
            except Exception:
                continue
        return None, "edit area not found"
    except Exception as e:
        return None, str(e)[:160]


def _notepad_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq notepad.exe"],
                             capture_output=True, text=True).stdout.lower()
        return "notepad.exe" in out
    except Exception:
        return False


def main():
    # SAFETY: refuse to run if Notepad is already open — we must not touch the user's existing tabs,
    # and we will not force-kill Notepad.
    if _notepad_running():
        print("REFUSING: Notepad is already open. Close all Notepad windows first (this test will not "
              "touch your existing tabs). HON-2 stays unverified — see the module docstring.")
        return 2
    C.resume_control()  # ensure not paused
    print("Launching Notepad…")
    subprocess.Popen(["notepad.exe"])
    time.sleep(2.0)
    ok = False
    detail = ""
    try:
        aw = C.active_window()
        print(f"active window: {aw.get('title')!r} ({aw.get('process')})")
        # Notepad focuses its edit area on launch; click lower-center (text area, below any ribbon)
        # to be safe, then type via clipboard paste.
        r = aw.get("rect") or {}
        if r:
            C.click(r["x"] + r["w"] // 2, r["y"] + int(r["h"] * 0.6))
            time.sleep(0.4)
        import pyperclip
        pyperclip.copy(MARKER)
        print("clipboard has marker:", pyperclip.paste() == MARKER)
        C.press_keys("ctrl+v")          # paste directly
        time.sleep(1.0)
        text, err = _read_notepad_text()
        if not (text and MARKER in text):   # one retry via type_text path
            C.type_text(MARKER); time.sleep(1.0); text, err = _read_notepad_text()
        if err:
            detail = f"readback error: {err}"
        else:
            ok = MARKER in (text or "")
            detail = f"read back {len(text or '')} chars; marker present: {ok}"
        print(detail)
    finally:
        # NON-DESTRUCTIVE: leave Notepad open for the user to close. We do NOT taskkill (that would
        # risk other tabs). The test typed into a fresh, empty instance only.
        print("(left Notepad open — close it manually; this test never force-kills Notepad)")
    print("\n=== HON-2:", "PASS — typed text verified in a live app via UIA ===" if ok
          else f"FAIL/FLAKY — {detail} (expected on UWP Notepad; see docstring) ===")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
