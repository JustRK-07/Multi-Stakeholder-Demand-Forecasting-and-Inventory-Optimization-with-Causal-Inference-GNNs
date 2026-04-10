"""
PostgreSQL Database Configuration and Models

Migration from JSON file-based storage to PostgreSQL for scalability.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import create_engine, Column, String, DateTime, Text, JSON, Integer, ForeignKey, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path

# Database URL - can be configured via environment variables
# For local development: postgresql://user:password@localhost:5432/retailcast
# Format: postgresql://[user[:password]@][netloc][:port][/dbname]

Base = declarative_base()


class User(Base):
    """User account and profile information."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="analyst", nullable=False)  # admin, analyst
    store_type = Column(String(50), nullable=True)  # grocery, fashion, electronics
    assigned_model_id = Column(String(255), nullable=True)  # e.g., model-grocery-v1.0
    model_last_updated = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('idx_email', 'email'),
        UniqueConstraint('email', name='uq_email'),
    )


class Session(Base):
    """User session tokens for authentication."""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # NULL = no expiry
    
    __table_args__ = (
        Index('idx_token', 'token'),
        Index('idx_user_id', 'user_id'),
    )


class Dataset(Base):
    """Dataset registry and metadata."""
    __tablename__ = "datasets"
    
    id = Column(String(255), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    filename = Column(String(255), nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending, training, completed, failed
    row_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # File paths
    upload_path = Column(String(512), nullable=True)  # storage/uploads/...
    normalized_path = Column(String(512), nullable=True)  # storage/normalized/...
    
    # Column mapping
    column_mapping = Column(JSON, nullable=True)  # { "source_col": "target_col" }
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_status', 'status'),
        Index('idx_created_at', 'created_at'),
    )


class AuditLog(Base):
    """Audit trail for all system events."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(100), nullable=False)  # auth.signup, auth.login, dataset.upload, etc
    actor = Column(String(255), nullable=False)  # user email
    target = Column(String(255), nullable=True)  # resource being acted upon
    details = Column(JSON, nullable=True)  # additional event data
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    __table_args__ = (
        Index('idx_event_type', 'event_type'),
        Index('idx_actor', 'actor'),
        Index('idx_created_at', 'created_at'),
    )


# Global database engine (initialized in main.py)
engine = None
SessionLocal = None


def init_db(database_url: str) -> None:
    """Initialize database connection and create tables."""
    global engine, SessionLocal
    
    engine = create_engine(
        database_url,
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,   # Recycle connections after 1 hour
        echo=False,          # Set True for SQL debugging
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database on module import
import os as _os
_database_url = _os.getenv("DATABASE_URL", "sqlite:///./test.db")
init_db(_database_url)
