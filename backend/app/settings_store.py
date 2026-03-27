from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[2]
STORAGE_DIR = ROOT / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_PATH = STORAGE_DIR / "settings.json"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "forecastHorizon": 30,
    "holdingCost": 0.15,
    "stockoutCost": 1.5,
    "notifications": True,
}


def load_settings() -> Dict[str, Any]:
    if not SETTINGS_PATH.exists():
        save_settings(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)

    try:
        payload = json.loads(SETTINGS_PATH.read_text())
    except Exception:
        save_settings(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)

    settings = dict(DEFAULT_SETTINGS)
    settings.update(payload if isinstance(payload, dict) else {})
    return settings


def save_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(DEFAULT_SETTINGS)
    merged.update(settings)
    SETTINGS_PATH.write_text(json.dumps(merged, indent=2, sort_keys=True))
    return merged
