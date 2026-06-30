# -*- coding: utf-8 -*-
"""HON-2 / HON-2b / HON-2c — real, SAFE GUI integration test for the Perception & Control stack.

Creates a REAL native Win32 EDIT control (its own HWND, exposes proper UI Automation — a faithful
proxy for real apps like Notepad/browsers/Office, unlike tkinter which exposes no UIA controls), then
drives it through the control stack and verifies the text actually landed by reading the control
(WM_GETTEXT).

Why this shape: synthetic keyboard injection (SendInput) is unreliable/suppressed in this environment
(verified — even a focused native control receives nothing), so the control stack uses **UIA
ValuePattern.SetValue** for text (HON-2c). This test proves that path works end-to-end on a real
control. Fully self-contained: own window (destroyed at the end), no user apps touched. On-demand.

Run:  python scripts/gui_eval.py
"""
import ctypes
import sys
import time
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nova.services import control as C  # noqa: E402

MARKER = "nova-gui-7731"
_u = ctypes.windll.user32


def _make_edit():
    try: ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception: pass
    _u.CreateWindowExW.restype = wintypes.HWND
    _u.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
                                   ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                   wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
    # WS_POPUP|WS_VISIBLE|WS_BORDER ; WS_EX_TOPMOST
    return _u.CreateWindowExW(0x100, "EDIT", "", 0x80000000 | 0x10000000 | 0x00800000,
                              320, 320, 520, 64, None, None, None, None)


def _read(hwnd):
    buf = ctypes.create_unicode_buffer(512)
    _u.SendMessageW(hwnd, 0x000D, 512, buf)   # WM_GETTEXT
    return buf.value


def main():
    C.resume_control()
    h = _make_edit()
    if not h:
        print("could not create test control"); return 1
    ok = False
    try:
        time.sleep(0.3)
        _u.keybd_event(0x12, 0, 0, 0); _u.keybd_event(0x12, 0, 2, 0)   # ALT tap unlocks foreground
        _u.SetForegroundWindow(h); _u.SetFocus(h)
        time.sleep(0.4)
        aw = C.active_window()
        print(f"active window process: {aw.get('process')}")
        r = C.type_text(MARKER)            # the control stack's text path (UIA SetValue)
        print(f"control.type_text -> {r}")
        time.sleep(0.3)
        got = _read(h)
        ok = MARKER in got
        print(f"control read back: {got!r} | marker present: {ok}")
    finally:
        try: _u.DestroyWindow(h)            # destroy ONLY our own control
        except Exception: pass
    print("\n=== HON-2:", "PASS — text landed in a real GUI control via the control stack (UIA) ==="
          if ok else "FAIL ===")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
