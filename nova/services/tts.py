# -*- coding: utf-8 -*-
"""Text-to-speech — speak text aloud via the local Piper voice (toolkit/speak.ps1).
Fire-and-forget: launches the speak script detached. Depends on config (TOOLKIT) +
nova.core.process (ps_args/_q)."""
import subprocess
from config import TOOLKIT
from nova.core.process import ps_args, _q
from nova.core.db import get_settings


def speak(text):
    """Speak `text` aloud in the background; raises on launch failure. Honors the `tts_rate` setting
    (1.0 normal, >1 faster) via Piper's length_scale = 1/rate (best-effort)."""
    arg = ""
    try:
        rate = float(get_settings().get("tts_rate", 1.0) or 1.0)
        if rate > 0 and abs(rate - 1.0) > 0.01:
            arg = f" -Length {round(1.0 / rate, 3)}"
    except Exception:
        arg = ""
    subprocess.Popen(ps_args(f'& "{TOOLKIT / "speak.ps1"}" {_q(text)}{arg}'),
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
