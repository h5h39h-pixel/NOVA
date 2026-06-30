# -*- coding: utf-8 -*-
"""At-rest secret encryption (SEC-4). Fernet (AES-128-CBC + HMAC) via the `cryptography` dep.
The key lives in a git-ignored file next to the DB (`<data>/.nova_key`), NOT in the DB — so a
stolen `control.db` alone can't reveal encrypted secrets. Values are stored as `enc:<token>`;
plaintext/legacy values pass through unchanged (transparent migration on next save).
Named `secretbox` to avoid shadowing the stdlib `secrets` module."""
from cryptography.fernet import Fernet, InvalidToken
from config import DB_PATH

_KEY_FILE = DB_PATH.parent / ".nova_key"
_PREFIX = "enc:"
_fernet = None


def _get_fernet():
    global _fernet
    if _fernet is None:
        _KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        if _KEY_FILE.exists():
            key = _KEY_FILE.read_bytes()
        else:
            key = Fernet.generate_key()
            _KEY_FILE.write_bytes(key)
            try:
                import os
                os.chmod(_KEY_FILE, 0o600)   # best-effort restrictive perms
            except Exception:
                pass
        _fernet = Fernet(key)
    return _fernet


def encrypt_secret(plaintext):
    """Return `enc:<token>` for a non-empty secret; pass through empty / already-encrypted values."""
    if not plaintext or (isinstance(plaintext, str) and plaintext.startswith(_PREFIX)):
        return plaintext
    return _PREFIX + _get_fernet().encrypt(str(plaintext).encode()).decode()


def decrypt_secret(value):
    """Return the plaintext for an `enc:` value; pass through plaintext/legacy unchanged."""
    if not value or not isinstance(value, str) or not value.startswith(_PREFIX):
        return value
    try:
        return _get_fernet().decrypt(value[len(_PREFIX):].encode()).decode()
    except (InvalidToken, Exception):
        return ""
