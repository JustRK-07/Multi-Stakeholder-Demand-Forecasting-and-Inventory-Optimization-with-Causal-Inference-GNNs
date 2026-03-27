from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
STORAGE_DIR = ROOT / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
REGISTRY_PATH = STORAGE_DIR / "datasets.json"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

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
            "error": self.error,
            "validation": self.validation or {},
        }


def _read_registry() -> Dict[str, Dict[str, Any]]:
    if not REGISTRY_PATH.exists():
        return {}
    try:
        data = json.loads(REGISTRY_PATH.read_text())
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _write_registry(data: Dict[str, Dict[str, Any]]) -> None:
    REGISTRY_PATH.write_text(json.dumps(data, indent=2, sort_keys=True))


def list_datasets() -> List[Dict[str, Any]]:
    data = _read_registry()
    rows = list(data.values())
    rows.sort(key=lambda row: row.get("uploadedAt", ""), reverse=True)
    return rows


def get_dataset(dataset_id: str) -> Optional[Dict[str, Any]]:
    return _read_registry().get(dataset_id)


def _normalize_column_name(name: str) -> str:
    return name.strip().lower().replace("-", "_").replace(" ", "_")


def suggest_mapping(columns: List[str]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for column in columns:
        normalized = _normalize_column_name(column)
        for target, aliases in COLUMN_ALIASES.items():
            if normalized in {_normalize_column_name(alias) for alias in aliases}:
                mapping[column] = target
                break
    return mapping


def _apply_mapping(columns: List[str], mapping: Dict[str, str]) -> Tuple[List[str], List[str]]:
    mapped_targets = list(mapping.values())
    missing = [col for col in REQUIRED_TARGET_COLUMNS if col not in mapped_targets]
    extras = [col for col in columns if col not in mapping]
    return missing, extras


def _parse_json_bytes(content: bytes) -> pd.DataFrame:
    raw = json.loads(content.decode("utf-8"))
    if isinstance(raw, list):
        return pd.DataFrame(raw)
    if isinstance(raw, dict):
        if "data" in raw and isinstance(raw["data"], list):
            return pd.DataFrame(raw["data"])
        return pd.DataFrame([raw])
    raise DatasetValidationError("Unsupported JSON payload.", details={"expected": "object or array"})


def parse_dataset_bytes(filename: str, content: bytes) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(BytesIO(content))
    if suffix == ".json":
        return _parse_json_bytes(content)
    if suffix in {".xlsx", ".xls"}:
        try:
            return pd.read_excel(BytesIO(content))
        except ImportError as exc:
            raise DatasetValidationError(
                "Excel support requires the 'openpyxl' package.",
                details={"filename": filename},
            ) from exc
    raise DatasetValidationError(
        "Unsupported file format.",
        details={"filename": filename, "supportedFormats": [".csv", ".json", ".xlsx", ".xls"]},
    )


def _serialize_preview(df: pd.DataFrame, rows: int = 5) -> List[Dict[str, Any]]:
    preview_df = df.head(rows).copy()
    preview_df = preview_df.where(pd.notnull(preview_df), None)
    records = preview_df.to_dict(orient="records")
    return [{str(k): v for k, v in row.items()} for row in records]


def _create_record(
    *,
    dataset_id: str,
    task_id: str,
    filename: str,
    stored_path: Path,
    status: str,
    progress: int,
    row_count: int,
    columns: List[str],
    preview: List[Dict[str, Any]],
    suggested_mapping: Dict[str, str],
    error: Optional[str] = None,
    validation: Optional[Dict[str, Any]] = None,
) -> DatasetRecord:
    return DatasetRecord(
        dataset_id=dataset_id,
        task_id=task_id,
        filename=filename,
        stored_path=str(stored_path),
        status=status,
        progressPct=progress,
        uploadedAt=datetime.now(timezone.utc).isoformat(),
        rowCount=row_count,
        columns=columns,
        preview=preview,
        suggestedMapping=suggested_mapping,
        error=error,
        validation=validation,
    )


def register_dataset_upload(filename: str, content: bytes, column_mapping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    dataset_id = str(uuid4())
    task_id = str(uuid4())
    stored_path = UPLOADS_DIR / f"{dataset_id}_{Path(filename).name}"
    stored_path.write_bytes(content)

    try:
        df = parse_dataset_bytes(filename, content)
        if df.empty:
            raise DatasetValidationError("Uploaded dataset is empty.", details={"filename": filename})
        columns = [str(c) for c in df.columns.tolist()]
        inferred_mapping = suggest_mapping(columns)
        effective_mapping = dict(inferred_mapping)
        if column_mapping:
            effective_mapping.update({str(k): str(v) for k, v in column_mapping.items() if k in columns and v})
        missing_required, unmapped_columns = _apply_mapping(columns, effective_mapping)
        validation = {
            "requiredColumns": REQUIRED_TARGET_COLUMNS,
            "optionalColumns": OPTIONAL_TARGET_COLUMNS,
            "missingRequired": missing_required,
            "unmappedColumns": unmapped_columns,
            "isValid": len(missing_required) == 0,
        }
        status = "completed" if validation["isValid"] else "failed"
        error = None if validation["isValid"] else "Missing required mapped columns."
        record = _create_record(
            dataset_id=dataset_id,
            task_id=task_id,
            filename=filename,
            stored_path=stored_path,
            status=status,
            progress=100 if validation["isValid"] else 0,
            row_count=int(len(df)),
            columns=columns,
            preview=_serialize_preview(df),
            suggested_mapping=effective_mapping,
            error=error,
            validation=validation,
        )
    except DatasetValidationError as exc:
        record = _create_record(
            dataset_id=dataset_id,
            task_id=task_id,
            filename=filename,
            stored_path=stored_path,
            status="failed",
            progress=0,
            row_count=0,
            columns=[],
            preview=[],
            suggested_mapping={},
            error=exc.message,
            validation={"isValid": False, **exc.details},
        )

    registry = _read_registry()
    registry[dataset_id] = record.to_dict()
    _write_registry(registry)
    return registry[dataset_id]
