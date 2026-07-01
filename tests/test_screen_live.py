# -*- coding: utf-8 -*-
"""LIVE screen tests — exercise nova/services/screen.py for real, including a DISPOSABLE target app
(a WinForms window this test spawns and owns, then kills) so screen capture + OCR + UIA element
detection are tested against a controllable window (closes the HON-2b "need an isolated target app"
gap). Skipped in the normal gate (they capture the screen / pop a window); run with:

    NOVA_LIVE_TESTS=1 python -m coverage run -m pytest tests/test_screen_live.py

Nothing here is destructive: the target window is a throwaway process we terminate; no user apps touched.
"""
import os
import subprocess
import tempfile
import time
from pathlib import Path
import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("NOVA_LIVE_TESTS"),
                                reason="live screen test (set NOVA_LIVE_TESTS=1)")

# A self-contained WinForms window: big label (for OCR) + a named button (for UIA find_element).
_TARGET_PS = r'''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$f = New-Object System.Windows.Forms.Form
$f.Text = "NOVA Test Target"; $f.TopMost = $true; $f.Width = 640; $f.Height = 360
$f.StartPosition = "CenterScreen"; $f.BackColor = [System.Drawing.Color]::White
$l = New-Object System.Windows.Forms.Label
$l.Text = "NOVA OCR TARGET 4242"; $l.AutoSize = $true
$l.Font = New-Object System.Drawing.Font("Segoe UI", 28, [System.Drawing.FontStyle]::Bold)
$l.ForeColor = [System.Drawing.Color]::Black; $l.Location = New-Object System.Drawing.Point(40, 50)
$b = New-Object System.Windows.Forms.Button
$b.Text = "SaveNovaTest"; $b.Name = "SaveNovaTest"
$b.Location = New-Object System.Drawing.Point(40, 180); $b.Width = 240; $b.Height = 60
$f.Controls.Add($l); $f.Controls.Add($b)
$f.Add_Shown({ $f.Activate() })
[System.Windows.Forms.Application]::Run($f)
'''


class _Target:
    """Spawn the disposable WinForms window as an owned subprocess; kill on exit."""
    def __enter__(self):
        self.script = Path(tempfile.gettempdir()) / "nova_target.ps1"
        self.script.write_text(_TARGET_PS, encoding="utf-8")
        self.proc = subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Normal",
             "-File", str(self.script)])
        time.sleep(3.0)   # let the window render + become foreground
        return self

    def __exit__(self, *a):
        try:
            self.proc.terminate()
        except Exception:
            pass
        try:
            subprocess.run(["taskkill", "/PID", str(self.proc.pid), "/T", "/F"],
                           capture_output=True)   # ensure the child powershell/window is gone
        except Exception:
            pass


# ---- pure helpers (no I/O) ----
def test_valid_lang():
    from nova.services.screen import _valid_lang
    assert _valid_lang("eng") and _valid_lang("eng+ara")
    assert not _valid_lang("eng; rm -rf")   # SEC-6: reject shell-injection in the lang code
    assert not _valid_lang("")


def test_core_term():
    from nova.services.screen import _core_term
    assert _core_term("click the Save button") == "Save"
    assert "OK" in _core_term("please press the OK button")


# ---- real capture (no window needed; grabs whatever is on screen) ----
def test_capture_and_grab():
    from nova.services.screen import capture_screenshot, _grab
    fn, path = capture_screenshot()
    assert path.exists() and path.stat().st_size > 1000 and fn.endswith(".png")
    arr = _grab(region=[0, 0, 200, 100])
    assert arr.shape[0] == 100 and arr.shape[1] == 200 and arr.shape[2] == 3


def test_read_screen_ocr():
    from nova.services.screen import read_screen
    r = read_screen(vision=False)
    assert r["ok"] is True and r["mode"] == "ocr" and isinstance(r["text"], str)


def test_recorder_roundtrip():
    from nova.services.screen import RECORDER, list_recordings
    assert RECORDER.start(fps=8)["ok"] is True
    assert RECORDER.is_recording() is True
    assert RECORDER.start()["ok"] is False           # already recording
    time.sleep(1.5)
    st = RECORDER.status(); assert st["recording"] is True and st["seconds"] > 0
    out = RECORDER.stop()
    assert out["ok"] is True and out["seconds"] >= 1
    recs = list_recordings()
    assert any(r["name"] == out["file"].split("/")[-1] for r in recs)
    assert RECORDER.stop()["ok"] is False            # not recording now


# ---- disposable target app: OCR + UIA element detection against a window we own ----
def test_ocr_reads_disposable_target():
    from nova.services.screen import read_screen
    with _Target():
        text = read_screen(vision=False)["text"].upper()
    assert "NOVA" in text or "4242" in text, f"OCR did not read the target window: {text[:120]!r}"


def test_uia_finds_disposable_button():
    import importlib.util
    if importlib.util.find_spec("uiautomation") is None:
        pytest.skip("uiautomation not installed")
    from nova.services.control import find_element
    with _Target():
        r = find_element("SaveNovaTest", partial=True, max_results=3)
    names = " ".join(m.get("name", "") for m in r.get("matches", []))
    assert r.get("matches"), "UIA did not find the disposable button"
    assert "SaveNovaTest" in names
