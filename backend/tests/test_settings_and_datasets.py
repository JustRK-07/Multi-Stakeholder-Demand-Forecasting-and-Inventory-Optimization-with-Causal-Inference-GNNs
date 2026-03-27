from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import dataset_registry, settings_store


def _configure_temp_storage(tmp_path, monkeypatch) -> None:
    storage_dir = tmp_path / "storage"
    uploads_dir = storage_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(settings_store, "STORAGE_DIR", storage_dir)
    monkeypatch.setattr(settings_store, "SETTINGS_PATH", storage_dir / "settings.json")
    monkeypatch.setattr(dataset_registry, "STORAGE_DIR", storage_dir)
    monkeypatch.setattr(dataset_registry, "UPLOADS_DIR", uploads_dir)
    monkeypatch.setattr(dataset_registry, "REGISTRY_PATH", storage_dir / "datasets.json")


def test_settings_store_persists_updates(tmp_path, monkeypatch):
    _configure_temp_storage(tmp_path, monkeypatch)

    initial = settings_store.load_settings()
    assert initial["forecastHorizon"] == 30

    saved = settings_store.save_settings(
        {
            "forecastHorizon": 14,
            "holdingCost": 0.25,
            "stockoutCost": 2.0,
            "notifications": False,
        }
    )
    assert saved["forecastHorizon"] == 14

    reloaded = settings_store.load_settings()
    assert reloaded == saved


def test_dataset_registry_registers_valid_upload(tmp_path, monkeypatch):
    _configure_temp_storage(tmp_path, monkeypatch)

    csv_body = "\n".join(
        [
            "date,store_id,product_id,sales_qty,price,promotion,category",
            "2026-01-01,S001,P001,100,9.99,0,Groceries",
            "2026-01-02,S001,P001,110,9.99,1,Groceries",
        ]
    ).encode("utf-8")

    record = dataset_registry.register_dataset_upload("sales.csv", csv_body)
    assert record["status"] == "completed"
    assert record["rowCount"] == 2
    assert record["validation"]["isValid"] is True
    assert len(record["preview"]) == 2

    fetched = dataset_registry.get_dataset(record["datasetId"])
    assert fetched is not None
    assert fetched["datasetId"] == record["datasetId"]

    listing = dataset_registry.list_datasets()
    assert len(listing) == 1


def test_dataset_registry_reports_missing_required_mapping(tmp_path, monkeypatch):
    _configure_temp_storage(tmp_path, monkeypatch)

    csv_body = "\n".join(
        [
            "day,store_code,sku,units",
            "2026-01-01,S001,P001,100",
        ]
    ).encode("utf-8")

    record = dataset_registry.register_dataset_upload(
        "partial.csv",
        csv_body,
        {"day": "date", "store_code": "store_id", "sku": "product_id"},
    )
    assert record["status"] == "failed"
    assert record["validation"]["isValid"] is False
    assert "sales_qty" in record["validation"]["missingRequired"]
