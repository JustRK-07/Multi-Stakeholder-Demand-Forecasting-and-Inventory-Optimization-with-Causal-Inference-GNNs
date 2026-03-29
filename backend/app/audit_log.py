from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[2]
STORAGE_DIR = ROOT / "storage"
AUDIT_LOG_PATH = STORAGE_DIR / "audit_log.json"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _read_log() -> List[Dict[str, Any]]:
    if not AUDIT_LOG_PATH.exists():
        return []
    try:
        payload = json.loads(AUDIT_LOG_PATH.read_text())
    except Exception:
        return []
    return payload if isinstance(payload, list) else []


def _write_log(entries: List[Dict[str, Any]]) -> None:
    AUDIT_LOG_PATH.write_text(json.dumps(entries, indent=2))


def append_audit_event(action: str, *, actor: Optional[str] = None, target: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    entries = _read_log()
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "actor": actor,
        "target": target,
        "details": details or {},
    }
    entries.append(event)
    entries = entries[-500:]
    _write_log(entries)
    return event


def list_audit_events(limit: int = 50) -> List[Dict[str, Any]]:
    entries = _read_log()
    return list(reversed(entries[-limit:]))
