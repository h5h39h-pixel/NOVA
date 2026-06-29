# -*- coding: utf-8 -*-
"""Text-to-speech — speak text aloud via the local Piper voice (toolkit/speak.ps1).
Fire-and-forget: launches the speak script detached. Depends on config (TOOLKIT) +
nova.core.process (ps_args/_q)."""
import subprocess
from config import TOOLKIT
from nova.core.process import ps_args, _q


def speak(text):
    """Speak `text` aloud in the background; raises on launch failure."""
    subprocess.Popen(ps_args(f'& "{TOOLKIT / "speak.ps1"}" {_q(text)}'),
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
