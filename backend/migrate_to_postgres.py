#!/usr/bin/env python3
"""
Migration script: JSON files → PostgreSQL

Migrates all data from JSON file-based storage to PostgreSQL.
Usage: python migrate_to_postgres.py <database_url>
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from app.database import init_db, SessionLocal, User, Session as DBSession, Dataset, AuditLog


ROOT = Path(__file__).resolve().parent.parent
STORAGE_DIR = ROOT / "storage"


def migrate_users(db: Session) -> int:
    """Migrate users from JSON to PostgreSQL."""
    users_path = STORAGE_DIR / "users.json"
    if not users_path.exists():
        print("⚠️  No users.json found (expected for new setup)")
        return 0
    
    with open(users_path, 'r') as f:
        users_data = json.load(f)
    
    count = 0
    for email, user_dict in users_data.items():
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"⏭️  User {email} already exists, skipping")
            continue
        
        user = User(
            email=email,
            name=user_dict.get("name", ""),
            password_hash=user_dict.get("passwordHash", ""),
            role=user_dict.get("role", "analyst"),
            store_type=user_dict.get("storeType"),
            assigned_model_id=user_dict.get("assignedModelId"),
            model_last_updated=user_dict.get("modelLastUpdated"),
            created_at=user_dict.get("createdAt"),
            last_login_at=user_dict.get("lastLoginAt"),
        )
        db.add(user)
        count += 1
    
    db.commit()
    print(f"✅ Migrated {count} users")
    return count


def migrate_datasets(db: Session) -> int:
    """Migrate datasets from JSON to PostgreSQL."""
    datasets_path = STORAGE_DIR / "datasets.json"
    if not datasets_path.exists():
        print("⚠️  No datasets.json found")
        return 0
    
    with open(datasets_path, 'r') as f:
        datasets_data = json.load(f)
    
    count = 0
    for dataset_id, dataset_dict in datasets_data.items():
        existing = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if existing:
            print(f"⏭️  Dataset {dataset_id} already exists, skipping")
            continue
        
        # Get user_id from email
        user_email = dataset_dict.get("email")
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            print(f"⚠️  User {user_email} not found for dataset {dataset_id}, skipping")
            continue
        
        dataset = Dataset(
            id=dataset_id,
            user_id=user.id,
            filename=dataset_dict.get("filename", ""),
            status=dataset_dict.get("status", "pending"),
            row_count=dataset_dict.get("rowCount"),
            error_message=dataset_dict.get("error"),
            upload_path=dataset_dict.get("uploadPath"),
            normalized_path=dataset_dict.get("normalizedPath"),
            column_mapping=dataset_dict.get("columnMapping"),
            created_at=dataset_dict.get("createdAt"),
            updated_at=dataset_dict.get("updatedAt"),
        )
        db.add(dataset)
        count += 1
    
    db.commit()
    print(f"✅ Migrated {count} datasets")
    return count


def migrate_audit_logs(db: Session) -> int:
    """Migrate audit logs from JSON to PostgreSQL."""
    audit_path = STORAGE_DIR / "audit_log.json"
    if not audit_path.exists():
        print("⚠️  No audit_log.json found")
        return 0
    
    with open(audit_path, 'r') as f:
        logs_data = json.load(f)
    
    # audit_log.json is either a list or dict of events
    if isinstance(logs_data, dict):
        events = logs_data.get("events", [])
    else:
        events = logs_data if isinstance(logs_data, list) else []
    
    count = 0
    for event in events:
        log = AuditLog(
            event_type=event.get("event_type", ""),
            actor=event.get("actor", ""),
            target=event.get("target"),
            details=event.get("details"),
            created_at=event.get("created_at"),
        )
        db.add(log)
        count += 1
    
    db.commit()
    print(f"✅ Migrated {count} audit logs")
    return count


def main():
    if len(sys.argv) < 2:
        print("Usage: python migrate_to_postgres.py <database_url>")
        print("Example: python migrate_to_postgres.py postgresql://user:pass@localhost:5432/retailcast")
        sys.exit(1)
    
    database_url = sys.argv[1]
    print(f"🔄 Migrating data to: {database_url}")
    
    try:
        init_db(database_url)
        db = SessionLocal()
        
        print("\n📦 Starting migration...")
        migrate_users(db)
        migrate_datasets(db)
        migrate_audit_logs(db)
        
        print("\n✅ Migration complete!")
        db.close()
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
