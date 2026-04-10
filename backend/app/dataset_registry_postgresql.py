"""
Dataset Registry - PostgreSQL Version

Refactored from JSON file-based storage to use SQLAlchemy ORM.
Maintains identical function signatures and Dataset dataclass compatibility.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import pandas as pd
from sqlalchemy.orm import Session

from .database import Dataset, User, SessionLocal
from .audit_log import append_audit_event

ROOT = Path(__file__).resolve().parents[2]
STORAGE_DIR = ROOT / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
NORMALIZED_DIR = STORAGE_DIR / "normalized"

STORAGE_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED_TARGET_COLUMNS = ["date", "store_id", "product_id", "sales_qty", "price"]
OPTIONAL_TARGET_COLUMNS = ["promotion", "category", "inventory_level", "discount"]

COLUMN_ALIASES = {
    "date": {"date", "day", "timestamp", "ds"},
    "store_id": {"store", "store_id", "storeid", "store code", "store_code"},
    "product_id": {"product", "product_id", "productid", "sku", "item", "item_id"},
    "sales_qty": {"sales", "sales_qty", "units_sold", "quantity", "qty", "demand"},
    "price": {"price", "unit_price", "selling_price"},
    "promotion": {"promotion", "promo", "holiday", "holiday_promotion", "is_promo"},
    "category": {"category", "product_category"},
    "inventory_level": {"inventory", "inventory_level", "stock", "stock_level"},
    "discount": {"discount", "markdown"},
}


class DatasetValidationError(Exception):
    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


@dataclass
class DatasetRecord:
    dataset_id: str
    task_id: str
    filename: str
    stored_path: str
    status: str
    progressPct: int
    uploadedAt: str
    rowCount: int
    columns: List[str]
    preview: List[Dict[str, Any]]
    suggestedMapping: Dict[str, str]
    normalizedPath: Optional[str] = None
    isActive: bool = False
    isArchived: bool = False
    archivedAt: Optional[str] = None
    error: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "datasetId": self.dataset_id,
            "taskId": self.task_id,
            "filename": self.filename,
            "storedPath": self.stored_path,
            "status": self.status,
            "progressPct": self.progressPct,
            "uploadedAt": self.uploadedAt,
            "rowCount": self.rowCount,
            "columns": self.columns,
            "preview": self.preview,
            "suggestedMapping": self.suggestedMapping,
            "normalizedPath": self.normalizedPath,
            "isActive": self.isActive,
            "isArchived": self.isArchived,
            "archivedAt": self.archivedAt,
            "error": self.error,
            "validation": self.validation or {},
        }


def register_dataset_upload(
    email: str,
    filename: str,
    file_bytes: bytes,
    columns: List[str],
    task_id: Optional[str] = None
) -> DatasetRecord:
    """Register and store uploaded dataset in PostgreSQL."""
    
    dataset_id = str(uuid4())
    task_id = task_id or str(uuid4())
    
    db = SessionLocal()
    try:
        # Find user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise DatasetValidationError("User not found")
        
        # Save uploaded file
        upload_path = UPLOADS_DIR / f"{dataset_id}_{filename}"
        upload_path.write_bytes(file_bytes)
        
        now = datetime.now(timezone.utc)
        
        # Parse CSV to detect columns
        try:
            df = pd.read_csv(BytesIO(file_bytes))
            detected_columns = list(df.columns)
            row_count = len(df)
            preview = df.head(5).to_dict('records')
        except Exception as e:
            raise DatasetValidationError(f"Could not parse CSV: {str(e)}")
        
        # Suggest column mapping
        suggested_mapping = _suggest_column_mapping(detected_columns)
        
        # Create Dataset record in PostgreSQL
        dataset = Dataset(
            id=dataset_id,
            user_id=user.id,
            filename=filename,
            status="pending",
            row_count=row_count,
            upload_path=str(upload_path),
            column_mapping={"detected": detected_columns, "suggested": suggested_mapping},
            created_at=now,
            updated_at=now,
        )
        
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        # Audit log
        append_audit_event(
            "dataset.upload",
            actor=email,
            target=dataset_id,
            details={"filename": filename, "rows": row_count}
        )
        
        return DatasetRecord(
            dataset_id=dataset_id,
            task_id=task_id,
            filename=filename,
            stored_path=str(upload_path),
            status="pending",
            progressPct=0,
            uploadedAt=now.isoformat(),
            rowCount=row_count,
            columns=detected_columns,
            preview=preview,
            suggestedMapping=suggested_mapping,
        )
    
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


def list_datasets(email: str, limit: int = 100) -> List[DatasetRecord]:
    """List all datasets for a user."""
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return []
        
        datasets = db.query(Dataset).filter(
            Dataset.user_id == user.id
        ).order_by(Dataset.created_at.desc()).limit(limit).all()
        
        records = []
        for ds in datasets:
            columns = ds.column_mapping.get("detected", []) if ds.column_mapping else []
            suggested = ds.column_mapping.get("suggested", {}) if ds.column_mapping else {}
            
            records.append(DatasetRecord(
                dataset_id=ds.id,
                task_id=ds.id,
                filename=ds.filename,
                stored_path=ds.upload_path or "",
                status=ds.status,
                progressPct=100 if ds.status == "completed" else 0,
                uploadedAt=ds.created_at.isoformat() if ds.created_at else "",
                rowCount=ds.row_count or 0,
                columns=columns,
                preview=[],
                suggestedMapping=suggested,
                normalizedPath=ds.normalized_path,
                error=ds.error_message,
            ))
        
        return records
    finally:
        db.close()


def get_dataset(dataset_id: str) -> Optional[DatasetRecord]:
    """Get single dataset metadata."""
    
    db = SessionLocal()
    try:
        ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not ds:
            return None
        
        columns = ds.column_mapping.get("detected", []) if ds.column_mapping else []
        suggested = ds.column_mapping.get("suggested", {}) if ds.column_mapping else {}
        
        return DatasetRecord(
            dataset_id=ds.id,
            task_id=ds.id,
            filename=ds.filename,
            stored_path=ds.upload_path or "",
            status=ds.status,
            progressPct=100 if ds.status == "completed" else 0,
            uploadedAt=ds.created_at.isoformat() if ds.created_at else "",
            rowCount=ds.row_count or 0,
            columns=columns,
            preview=[],
            suggestedMapping=suggested,
            normalizedPath=ds.normalized_path,
            error=ds.error_message,
        )
    finally:
        db.close()


def update_dataset_status(
    dataset_id: str,
    status: str,
    progress_pct: int = 0,
    error: Optional[str] = None,
    normalized_path: Optional[str] = None
) -> None:
    """Update dataset processing status."""
    
    db = SessionLocal()
    try:
        ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if ds:
            ds.status = status
            ds.error_message = error
            if normalized_path:
                ds.normalized_path = normalized_path
            db.commit()
    finally:
        db.close()


def _suggest_column_mapping(source_columns: List[str]) -> Dict[str, str]:
    """Suggest target column names based on source columns and aliases."""
    
    suggestion = {}
    used_targets = set()
    
    for source_col in source_columns:
        source_lower = source_col.lower().strip()
        
        # Try to match with COLUMN_ALIASES
        for target, aliases in COLUMN_ALIASES.items():
            if target not in used_targets and source_lower in aliases:
                suggestion[source_col] = target
                used_targets.add(target)
                break
        
        # If no match, keep original
        if source_col not in suggestion:
            suggestion[source_col] = source_col
    
    return suggestion
