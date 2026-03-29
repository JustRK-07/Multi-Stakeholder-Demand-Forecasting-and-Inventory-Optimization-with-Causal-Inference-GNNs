from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .audit_log import append_audit_event

ROOT = Path(__file__).resolve().parents[2]
STORAGE_DIR = ROOT / "storage"
USERS_PATH = STORAGE_DIR / "users.json"
SESSIONS_PATH = STORAGE_DIR / "sessions.json"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class AuthError(Exception):
    def __init__(self, code: str, message: str, *, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text())
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _hash_password(password: str, salt: Optional[bytes] = None) -> str:
    salt = salt or secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"{base64.b64encode(salt).decode()}${base64.b64encode(derived).decode()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt_b64, digest_b64 = stored.split("$", 1)
        salt = base64.b64decode(salt_b64.encode())
        expected = base64.b64decode(digest_b64.encode())
    except Exception:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return hmac.compare_digest(candidate, expected)


def _sanitize_user(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": record.get("name", ""),
        "email": record.get("email", ""),
        "role": record.get("role", "analyst"),
        "createdAt": record.get("createdAt"),
        "lastLoginAt": record.get("lastLoginAt"),
    }


def create_user(name: str, email: str, password: str) -> Dict[str, Any]:
    normalized_email = _normalize_email(email)
    if not name.strip():
        raise AuthError("INVALID_NAME", "Name is required.")
    if "@" not in normalized_email:
        raise AuthError("INVALID_EMAIL", "A valid email address is required.")
    if len(password) < 8:
        raise AuthError("WEAK_PASSWORD", "Password must be at least 8 characters long.")

    users = _read_json(USERS_PATH)
    if normalized_email in users:
        raise AuthError("USER_EXISTS", "An account already exists for this email.", details={"email": normalized_email})

    now = _utcnow()
    users[normalized_email] = {
        "name": name.strip(),
        "email": normalized_email,
        "role": "admin" if not users else "analyst",
        "passwordHash": _hash_password(password),
        "createdAt": now,
        "lastLoginAt": None,
    }
    _write_json(USERS_PATH, users)
    append_audit_event("auth.signup", actor=normalized_email, target=normalized_email)
    return _sanitize_user(users[normalized_email])


def create_session(email: str, password: str) -> Dict[str, Any]:
    normalized_email = _normalize_email(email)
    users = _read_json(USERS_PATH)
    user = users.get(normalized_email)
    if not user or not _verify_password(password, str(user.get("passwordHash", ""))):
        raise AuthError("INVALID_CREDENTIALS", "Email or password is incorrect.")

    token = secrets.token_urlsafe(32)
    sessions = _read_json(SESSIONS_PATH)
    now = _utcnow()
    sessions[token] = {"email": normalized_email, "createdAt": now}
    user["lastLoginAt"] = now
    _write_json(SESSIONS_PATH, sessions)
    _write_json(USERS_PATH, users)
    append_audit_event("auth.login", actor=normalized_email, target=normalized_email)
    return {"token": token, "user": _sanitize_user(user)}


def get_session(token: str) -> Optional[Dict[str, Any]]:
    sessions = _read_json(SESSIONS_PATH)
    session = sessions.get(token)
    if not session:
        return None
    users = _read_json(USERS_PATH)
    user = users.get(str(session.get("email", "")))
    if not user:
        return None
    return {"token": token, "user": _sanitize_user(user), "createdAt": session.get("createdAt")}


def delete_session(token: str) -> bool:
    sessions = _read_json(SESSIONS_PATH)
    removed = token in sessions
    if removed:
        sessions.pop(token, None)
        _write_json(SESSIONS_PATH, sessions)
    return removed


def update_password(email: str, current_password: str, new_password: str) -> Dict[str, Any]:
    normalized_email = _normalize_email(email)
    if len(new_password) < 8:
        raise AuthError("WEAK_PASSWORD", "Password must be at least 8 characters long.")
    users = _read_json(USERS_PATH)
    user = users.get(normalized_email)
    if not user or not _verify_password(current_password, str(user.get("passwordHash", ""))):
        raise AuthError("INVALID_CREDENTIALS", "Current password is incorrect.")
    user["passwordHash"] = _hash_password(new_password)
    _write_json(USERS_PATH, users)
    append_audit_event("auth.password_update", actor=normalized_email, target=normalized_email)
    return _sanitize_user(user)


def update_profile(email: str, *, name: str) -> Dict[str, Any]:
    normalized_email = _normalize_email(email)
    if not name.strip():
        raise AuthError("INVALID_NAME", "Name is required.")
    users = _read_json(USERS_PATH)
    user = users.get(normalized_email)
    if not user:
        raise AuthError("USER_NOT_FOUND", "User was not found.")
    user["name"] = name.strip()
    _write_json(USERS_PATH, users)
    append_audit_event("auth.profile_update", actor=normalized_email, target=normalized_email, details={"name": user["name"]})
    return _sanitize_user(user)
