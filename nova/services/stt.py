# -*- coding: utf-8 -*-
"""Speech-to-text — lazily loads a local faster-whisper model (GPU/CUDA float16, CPU/int8 fallback).
Size is configurable via the `stt_model` setting. Extracted from server.py (HON-11)."""
import threading
import logging
from nova.core.db import get_settings

log = logging.getLogger("nova")
_WHISPER = None
_WHISPER_LOCK = threading.Lock()
_WHISPER_SIZE = None


def get_whisper():
    """Lazily load the local Whisper STT model. Size via the `stt_model` setting
    (tiny/base/small/medium/large-v3) — larger = more accurate (esp. Arabic), slower."""
    global _WHISPER, _WHISPER_SIZE
    size = (get_settings().get("stt_model") or "small").strip()
    if size not in ("tiny", "base", "small", "medium", "large-v3"):
        size = "small"
    if _WHISPER is None or size != _WHISPER_SIZE:
        with _WHISPER_LOCK:
            if _WHISPER is None or size != _WHISPER_SIZE:
                from faster_whisper import WhisperModel
                try:   # GPU (RTX 5090) — far faster + lets large models run for good Arabic accuracy
                    _WHISPER = WhisperModel(size, device="cuda", compute_type="float16")
                    log.info(f"Whisper STT model loaded ({size} / cuda / float16) — fully local")
                except Exception as e:
                    _WHISPER = WhisperModel(size, device="cpu", compute_type="int8")
                    log.info(f"Whisper STT model loaded ({size} / cpu / int8) — cuda unavailable: {str(e)[:80]}")
                _WHISPER_SIZE = size
    return _WHISPER
