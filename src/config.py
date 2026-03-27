"""Persistent configuration for provider credentials and settings."""

import json
import os
from pathlib import Path
from typing import Any

from . import crypto

CONFIG_DIR = Path.home() / ".llm-usage-tracker"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "refresh_interval_minutes": 5,
    "providers": {},
}


def _ensure_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load() -> dict[str, Any]:
    _ensure_dir()
    if not CONFIG_FILE.exists():
        return dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_CONFIG)


def save(cfg: dict[str, Any]):
    _ensure_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
    os.chmod(CONFIG_FILE, 0o600)


def save_provider(name: str, auth_type: str, credential: str, enabled: bool = True):
    """Save a provider configuration with encrypted credential."""
    cfg = load()
    cfg.setdefault("providers", {})[name] = {
        "auth_type": auth_type,
        "credential": crypto.encrypt(credential),
        "enabled": enabled,
    }
    save(cfg)


def get_provider(name: str) -> dict[str, Any] | None:
    cfg = load()
    prov = cfg.get("providers", {}).get(name)
    if prov is None:
        return None
    return {
        "auth_type": prov["auth_type"],
        "credential": crypto.decrypt(prov["credential"]),
        "enabled": prov.get("enabled", True),
    }


def remove_provider(name: str):
    cfg = load()
    cfg.get("providers", {}).pop(name, None)
    save(cfg)


def get_refresh_interval() -> int:
    return load().get("refresh_interval_minutes", 5)


def set_refresh_interval(minutes: int):
    cfg = load()
    cfg["refresh_interval_minutes"] = max(1, minutes)
    save(cfg)
