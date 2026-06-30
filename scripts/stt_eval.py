# -*- coding: utf-8 -*-
"""HON-7 — Speech-to-text accuracy (WER) for English AND Arabic.

Synthesizes reference sentences with the local Piper voices (en_US-lessac / ar_JO-kareem) to WAV,
transcribes them back through the live `/api/stt` (faster-whisper), and reports Word Error Rate per
language. This turns "Arabic STT works" into a measured number. Local-only; needs the server running.

Usage:
  python scripts/stt_eval.py                 # measure + print
  python scripts/stt_eval.py --record        # also record the score to the quality dashboard (IDEA-6)
"""
import argparse
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")   # Arabic output on cp1252 consoles
except Exception:
    pass
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import toolkit_script  # noqa: E402
import urllib.request  # noqa: E402

BASE = "http://127.0.0.1:8900"

EN = [
    "the quick brown fox jumps over the lazy dog",
    "please open the settings page and enable screen vision",
    "system metrics show ninety percent memory usage",
    "generate an image of a red apple on a wooden table",
]
AR = [
    "مرحبا كيف حالك اليوم",
    "افتح صفحة الاعدادات وفعل الرؤية",
    "ولد صورة لتفاحة حمراء على طاولة",
]


def _norm(s):
    s = unicodedata.normalize("NFKC", s or "").lower()
    keep = []
    for ch in s:
        if ch.isalnum() or ch.isspace():
            keep.append(ch)
        else:
            keep.append(" ")
    return " ".join("".join(keep).split())


def _wer(ref, hyp):
    r = _norm(ref).split()
    h = _norm(hyp).split()
    # Levenshtein over words
    d = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1): d[i][0] = i
    for j in range(len(h) + 1): d[0][j] = j
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            cost = 0 if r[i - 1] == h[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
    return d[len(r)][len(h)] / max(1, len(r))


def _speak_to_wav(text):
    out = Path(tempfile.gettempdir()) / "stt_eval.wav"
    if out.exists(): out.unlink()
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                    str(toolkit_script("speak.ps1")), text, "-Save", str(out)],
                   capture_output=True, text=True, timeout=120)
    return out if out.exists() else None


def _transcribe(wav, lang):
    boundary = "----stt"
    body = bytearray()
    data = wav.read_bytes()
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"audio\"; filename=\"a.wav\"\r\nContent-Type: audio/wav\r\n\r\n".encode()
    body += data + b"\r\n"
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"lang\"\r\n\r\n{lang}\r\n".encode()
    body += f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(BASE + "/api/stt", data=bytes(body),
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    import json
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read()).get("text", "")


def run():
    rows = []
    for lang, refs in (("en", EN), ("ar", AR)):
        for ref in refs:
            wav = _speak_to_wav(ref)
            if not wav:
                print(f"[skip] could not synthesize ({lang}): {ref[:30]}")
                continue
            hyp = _transcribe(wav, lang)
            w = _wer(ref, hyp)
            rows.append((lang, w))
            print(f"[{lang}] WER={w:.2f}  ref='{ref[:40]}'  hyp='{(hyp or '').strip()[:40]}'")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", action="store_true")
    args = ap.parse_args()
    rows = run()
    if not rows:
        print("no measurements (is the server running + Piper voices present?)"); return
    for lang in ("en", "ar"):
        ws = [w for l, w in rows if l == lang]
        if ws:
            avg = sum(ws) / len(ws)
            acc = max(0.0, 1 - avg)
            print(f"\n=== {lang.upper()} STT: mean WER {avg:.3f} (~{acc*100:.0f}% word accuracy) over {len(ws)} clips ===")
            if args.record:
                from nova.services.quality import record
                record(f"stt-{lang}", round(acc * len(ws), 3), len(ws), f"mean WER {avg:.3f}")


if __name__ == "__main__":
    main()
