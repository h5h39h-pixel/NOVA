# -*- coding: utf-8 -*-
"""
Central configuration for the AI Control Center.

Everything that used to be hard-coded lives here and is *derived relative to this
folder* by default, so the project is portable: copy the folder to another PC and
it resolves its own paths. Override anything by editing `config.json` (auto-created
next to this file on first run).

Layout assumed by the defaults:
    <AI_ROOT>/                     e.g. C:\\AI
      agent-workspace/             = WORKSPACE
        control-center/            = this folder (BASE)
        toolkit/  data/
      ComfyUI/   training/   overnight_training.log
"""
import json, shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent          # .../agent-workspace/control-center
WORKSPACE_DEFAULT = BASE.parent                  # .../agent-workspace
AI_ROOT_DEFAULT = WORKSPACE_DEFAULT.parent       # .../  (e.g. C:\AI)

DEFAULTS = {
    "workspace": str(WORKSPACE_DEFAULT),
    "ai_root": str(AI_ROOT_DEFAULT),
    "ollama_url": "http://127.0.0.1:11434",
    "comfy_url": "http://127.0.0.1:8188",
    "comfy_dir": str(AI_ROOT_DEFAULT / "ComfyUI"),
    "owui_url": "http://127.0.0.1:3000",
    "owui_container": "open-webui",
    "training_dir": str(AI_ROOT_DEFAULT / "training"),
    "port": 8900,
    "https_enabled": False,           # serve over TLS (self-signed cert auto-generated)
    "bind_host": "",                  # "" = auto (127.0.0.1, or 0.0.0.0 when auth+lan_access)
}

CONFIG_FILE = BASE / "config.json"
def _load():
    cfg = dict(DEFAULTS)
    try:
        if CONFIG_FILE.exists():
            # utf-8-sig tolerates a BOM (Notepad/PowerShell add one when editing)
            cfg.update({k: v for k, v in json.loads(CONFIG_FILE.read_text(encoding="utf-8-sig")).items() if k in DEFAULTS})
        else:
            CONFIG_FILE.write_text(json.dumps(DEFAULTS, indent=2), encoding="utf-8")
    except Exception as e:
        import sys
        print(f"[config] WARNING: could not parse config.json ({e}); using defaults", file=sys.stderr)
    return cfg

_cfg = _load()

# ---- resolved paths / endpoints (imported by server.py) ----
WORKSPACE   = Path(_cfg["workspace"])
AI_ROOT     = Path(_cfg["ai_root"])
TOOLKIT     = WORKSPACE / "toolkit"
UPLOAD_DIR  = WORKSPACE / "data" / "uploads"   # uploads, generated images, screenshots, browse captures
DB_PATH     = WORKSPACE / "data" / "control.db"
LOG_DIR     = WORKSPACE / "data" / "logs"
CERT_DIR    = WORKSPACE / "data" / "certs"
COMFY       = Path(_cfg["comfy_dir"])
OLLAMA      = _cfg["ollama_url"].rstrip("/")
COMFY_URL   = _cfg["comfy_url"].rstrip("/")
OWUI_URL    = _cfg["owui_url"].rstrip("/")
OWUI_CTR    = _cfg["owui_container"]
NVSMI       = shutil.which("nvidia-smi") or r"C:\WINDOWS\system32\nvidia-smi.exe"
PORT        = int(_cfg["port"])
HTTPS_ENABLED = bool(_cfg["https_enabled"])
BIND_OVERRIDE = (_cfg.get("bind_host") or "").strip()

TRAIN_DIR    = Path(_cfg["training_dir"])
DS_BASE      = TRAIN_DIR / "dataset.jsonl"
DS_LEARNED   = TRAIN_DIR / "dataset_learned.jsonl"
DS_COMBINED  = TRAIN_DIR / "dataset_combined.jsonl"
TRAIN_LOG    = AI_ROOT / "overnight_training.log"
TRAIN_REPORT = AI_ROOT / "training_report.txt"

def ensure_cert():
    """Generate a self-signed cert for HTTPS if one isn't present. Returns (certfile, keyfile)."""
    CERT_DIR.mkdir(parents=True, exist_ok=True)
    crt = CERT_DIR / "nova.crt"; key = CERT_DIR / "nova.key"
    if crt.exists() and key.exists():
        return str(crt), str(key)
    from datetime import datetime, timedelta, timezone
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    import ipaddress
    k = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Nova Control Center")])
    san = x509.SubjectAlternativeName([x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))])
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(k.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
            .not_valid_after(datetime.now(timezone.utc) + timedelta(days=3650))
            .add_extension(san, critical=False)
            .sign(k, hashes.SHA256()))
    key.write_bytes(k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL,
                                    serialization.NoEncryption()))
    crt.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    return str(crt), str(key)
