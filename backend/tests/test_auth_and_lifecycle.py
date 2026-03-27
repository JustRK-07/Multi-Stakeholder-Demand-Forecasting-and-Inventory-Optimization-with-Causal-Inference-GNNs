from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import auth_store, dataset_registry  # noqa: E402
from app.auth_store import create_session, create_user, get_session, update_password  # noqa: E402
from app.dataset_registry import activate_dataset, delete_dataset, register_dataset_upload  # noqa: E402
from app.ml.federated_sim import simulate_federated_rounds  # noqa: E402


def test_auth_store_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(auth_store, "USERS_PATH", tmp_path / "users.json")
    monkeypatch.setattr(auth_store, "SESSIONS_PATH", tmp_path / "sessions.json")

    user = create_user("Analyst", "analyst@example.com", "password123")
    assert user["email"] == "analyst@example.com"

    session = create_session("analyst@example.com", "password123")
    assert session["token"]
    assert get_session(session["token"]) is not None

    updated = update_password("analyst@example.com", "password123", "new-password123")
    assert updated["email"] == "analyst@example.com"
    refreshed = create_session("analyst@example.com", "new-password123")
    assert refreshed["token"]


def test_dataset_delete_promotes_latest_remaining_dataset(tmp_path, monkeypatch):
    monkeypatch.setattr(dataset_registry, "UPLOADS_DIR", tmp_path / "uploads")
    monkeypatch.setattr(dataset_registry, "NORMALIZED_DIR", tmp_path / "normalized")
    monkeypatch.setattr(dataset_registry, "REGISTRY_PATH", tmp_path / "datasets.json")
    monkeypatch.setattr(dataset_registry, "ACTIVE_DATASET_PATH", tmp_path / "active.json")
    dataset_registry.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    dataset_registry.NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)

    csv_one = b"date,store_id,product_id,sales_qty,price\n2024-01-01,S001,P001,10,5.0\n2024-01-02,S001,P001,12,5.1\n"
    csv_two = b"date,store_id,product_id,sales_qty,price\n2024-02-01,S002,P002,8,3.2\n2024-02-02,S002,P002,9,3.3\n"
    first = register_dataset_upload("first.csv", csv_one)
    second = register_dataset_upload("second.csv", csv_two)
    activate_dataset(first["datasetId"])

    deleted = delete_dataset(first["datasetId"])
    assert deleted["datasetId"] == first["datasetId"]

    active_payload = json.loads(dataset_registry.ACTIVE_DATASET_PATH.read_text())
    assert active_payload["datasetId"] == second["datasetId"]


def test_federated_rounds_are_data_driven():
    rounds = simulate_federated_rounds()
    assert rounds
    assert {"round", "globalAccuracy", "localAccuracy", "privacyBudget", "participants"} <= set(rounds[0].keys())
    assert rounds[0]["participants"] >= 1
