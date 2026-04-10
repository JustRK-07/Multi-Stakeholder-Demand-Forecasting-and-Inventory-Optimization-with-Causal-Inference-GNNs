"""
Authentication Store - PostgreSQL Version

Refactored from JSON file-based storage to use SQLAlchemy ORM.
Maintains identical function signatures and error handling.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .database import User, SessionLocal
from .audit_log import append_audit_event


class AuthError(Exception):
    def __init__(self, code: str, message: str, *, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


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


def _sanitize_user(user: User) -> Dict[str, Any]:
    """Convert User ORM object to sanitized dict (no password)."""
    return {
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "storeType": user.store_type,
        "assignedModelId": user.assigned_model_id,
        "modelLastUpdated": user.model_last_updated.isoformat() if user.model_last_updated else None,
        "createdAt": user.created_at.isoformat() if user.created_at else None,
        "lastLoginAt": user.last_login_at.isoformat() if user.last_login_at else None,
    }


def create_user(
    name: str,
    email: str,
    password: str,
    store_type: Optional[str] = None,
    assigned_model_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create new user account in PostgreSQL."""
    
    normalized_email = _normalize_email(email)
    
    if not name.strip():
        raise AuthError("INVALID_NAME", "Name is required.")
    if "@" not in normalized_email:
        raise AuthError("INVALID_EMAIL", "A valid email address is required.")
    if len(password) < 8:
        raise AuthError("WEAK_PASSWORD", "Password must be at least 8 characters long.")
    
    db = SessionLocal()
    try:
        # Check if user exists
        existing = db.query(User).filter(User.email == normalized_email).first()
        if existing:
            raise AuthError("USER_EXISTS", "An account already exists for this email.", details={"email": normalized_email})
        
        # Check if this is first user (should be admin)
        user_count = db.query(User).count()
        role = "admin" if user_count == 0 else "analyst"
        
        now = datetime.now(timezone.utc)
        new_user = User(
            email=normalized_email,
            name=name.strip(),
            password_hash=_hash_password(password),
            role=role,
            store_type=store_type,
            assigned_model_id=assigned_model_id,
            model_last_updated=now if assigned_model_id else None,
            created_at=now,
            last_login_at=None,
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Audit log
        append_audit_event("auth.signup", actor=normalized_email, target=normalized_email, details={"storeType": store_type})
        
        return _sanitize_user(new_user)
    
    except IntegrityError as e:
        db.rollback()
        raise AuthError("USER_EXISTS", "An account already exists for this email.", details={"email": normalized_email})
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


def create_session(email: str, password: str) -> Dict[str, Any]:
    """Create new session token for user."""
    
    normalized_email = _normalize_email(email)
    
    db = SessionLocal()
    try:
        # Find user
        user = db.query(User).filter(User.email == normalized_email).first()
        if not user or not _verify_password(password, user.password_hash):
            raise AuthError("INVALID_CREDENTIALS", "Email or password is incorrect.")
        
        # Create session token
        token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        
        from .database import Session as SessionModel
        session = SessionModel(
            token=token,
            user_id=user.id,
            created_at=now,
            expires_at=None,
        )
        
        # Update last login
        user.last_login_at = now
        
        db.add(session)
        db.commit()
        
        # Audit log
        append_audit_event("auth.login", actor=normalized_email, target=normalized_email)
        
        return {"token": token, "user": _sanitize_user(user)}
    
    except AuthError:
        raise
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


def get_session(token: str) -> Optional[Dict[str, Any]]:
    """Retrieve session and associated user."""
    
    db = SessionLocal()
    try:
        from .database import Session as SessionModel
        session = db.query(SessionModel).filter(SessionModel.token == token).first()
        if not session:
            return None
        
        user = db.query(User).filter(User.id == session.user_id).first()
        if not user:
            return None
        
        return {
            "token": token,
            "user": _sanitize_user(user),
            "createdAt": session.created_at.isoformat() if session.created_at else None,
        }
    finally:
        db.close()


def delete_session(token: str) -> bool:
    """Delete session token."""
    
    db = SessionLocal()
    try:
        from .database import Session as SessionModel
        session = db.query(SessionModel).filter(SessionModel.token == token).first()
        
        if not session:
            return False
        
        db.delete(session)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


def update_password(email: str, current_password: str, new_password: str) -> Dict[str, Any]:
    """Update user password."""
    
    normalized_email = _normalize_email(email)
    
    if len(new_password) < 8:
        raise AuthError("WEAK_PASSWORD", "Password must be at least 8 characters long.")
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == normalized_email).first()
        if not user or not _verify_password(current_password, user.password_hash):
            raise AuthError("INVALID_CREDENTIALS", "Current password is incorrect.")
        
        user.password_hash = _hash_password(new_password)
        db.commit()
        
        # Audit log
        append_audit_event("auth.password_update", actor=normalized_email, target=normalized_email)
        
        return _sanitize_user(user)
    except AuthError:
        raise
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


def update_profile(email: str, *, name: str) -> Dict[str, Any]:
    """Update user profile information."""
    
    normalized_email = _normalize_email(email)
    
    if not name.strip():
        raise AuthError("INVALID_NAME", "Name is required.")
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == normalized_email).first()
        if not user:
            raise AuthError("USER_NOT_FOUND", "User was not found.")
        
        user.name = name.strip()
        db.commit()
        
        # Audit log
        append_audit_event("auth.profile_update", actor=normalized_email, target=normalized_email, details={"name": user.name})
        
        return _sanitize_user(user)
    except AuthError:
        raise
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
