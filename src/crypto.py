"""Encrypt and decrypt credentials stored on disk."""

import os
from pathlib import Path

from cryptography.fernet import Fernet


def _key_path() -> Path:
    p = Path.home() / ".llm-usage-tracker" / ".key"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _get_or_create_key() -> bytes:
    kp = _key_path()
    if kp.exists():
        return kp.read_bytes()
    key = Fernet.generate_key()
    kp.write_bytes(key)
    os.chmod(kp, 0o600)
    return key


def encrypt(plaintext: str) -> str:
    f = Fernet(_get_or_create_key())
    return f.encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    f = Fernet(_get_or_create_key())
    return f.decrypt(token.encode()).decode()
