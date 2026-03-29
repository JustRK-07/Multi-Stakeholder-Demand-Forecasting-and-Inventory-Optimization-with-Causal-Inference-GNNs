from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import audit_log, auth_store, dataset_registry  # noqa: E402
from app.main import app  # noqa: E402
from app.ml import drift_monitor  # noqa: E402


def _configure_storage(tmp_path, monkeypatch) -> None:
    storage_dir = tmp_path / "storage"
    uploads_dir = storage_dir / "uploads"
    normalized_dir = storage_dir / "normalized"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(auth_store, "USERS_PATH", storage_dir / "users.json")
    monkeypatch.setattr(auth_store, "SESSIONS_PATH", storage_dir / "sessions.json")

    monkeypatch.setattr(dataset_registry, "STORAGE_DIR", storage_dir)
    monkeypatch.setattr(dataset_registry, "UPLOADS_DIR", uploads_dir)
    monkeypatch.setattr(dataset_registry, "NORMALIZED_DIR", normalized_dir)
    monkeypatch.setattr(dataset_registry, "REGISTRY_PATH", storage_dir / "datasets.json")
    monkeypatch.setattr(dataset_registry, "ACTIVE_DATASET_PATH", storage_dir / "active_dataset.json")

    monkeypatch.setattr(audit_log, "AUDIT_LOG_PATH", storage_dir / "audit_log.json")

    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(drift_monitor, "DRIFT_HISTORY_PATH", artifacts_dir / "drift_history.json")
    monkeypatch.setattr(drift_monitor, "SNAPSHOT_PATH", artifacts_dir / "drift_snapshot.csv")


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_auth_and_dataset_routes(tmp_path, monkeypatch):
    _configure_storage(tmp_path, monkeypatch)
    client = TestClient(app)

    signup = client.post("/api/v1/auth/signup", json={"name": "Admin User", "email": "admin@example.com", "password": "password123"})
    assert signup.status_code == 200
    token = signup.json()["data"]["token"]

    session = client.get("/api/v1/auth/session", headers=_auth_header(token))
    assert session.status_code == 200
    assert session.json()["data"]["user"]["role"] == "admin"

    profile = client.put("/api/v1/auth/profile", headers=_auth_header(token), json={"name": "Updated Admin"})
    assert profile.status_code == 200
    assert profile.json()["data"]["user"]["name"] == "Updated Admin"

    csv_body = b"date,store_id,product_id,sales_qty,price\n2024-01-01,S001,P001,10,5.0\n2024-01-02,S001,P001,12,5.1\n"
    upload = client.post(
        "/api/v1/datasets/upload",
        headers=_auth_header(token),
        files={"file": ("sales.csv", csv_body, "text/csv")},
    )
    assert upload.status_code == 200
    dataset_id = upload.json()["data"]["datasetId"]

    listed = client.get("/api/v1/datasets?include_archived=true", headers=_auth_header(token))
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1

    archived = client.post(f"/api/v1/datasets/{dataset_id}/archive", headers=_auth_header(token))
    assert archived.status_code == 200
    assert archived.json()["data"]["isArchived"] is True

    restored = client.post(f"/api/v1/datasets/{dataset_id}/archive?archived=false", headers=_auth_header(token))
    assert restored.status_code == 200
    assert restored.json()["data"]["isArchived"] is False

    activated = client.post(f"/api/v1/datasets/{dataset_id}/activate", headers=_auth_header(token))
    assert activated.status_code == 200
    assert activated.json()["data"]["isActive"] is True

    audit = client.get("/api/v1/audit/logs", headers=_auth_header(token))
    assert audit.status_code == 200
    assert len(audit.json()["data"]["items"]) >= 4


def test_non_admin_cannot_delete_dataset(tmp_path, monkeypatch):
    _configure_storage(tmp_path, monkeypatch)
    client = TestClient(app)

    admin = client.post("/api/v1/auth/signup", json={"name": "Admin User", "email": "admin@example.com", "password": "password123"})
    admin_token = admin.json()["data"]["token"]
    user = client.post("/api/v1/auth/signup", json={"name": "Analyst User", "email": "analyst@example.com", "password": "password123"})
    user_token = user.json()["data"]["token"]

    csv_body = b"date,store_id,product_id,sales_qty,price\n2024-01-01,S001,P001,10,5.0\n2024-01-02,S001,P001,12,5.1\n"
    upload = client.post("/api/v1/datasets/upload", headers=_auth_header(admin_token), files={"file": ("sales.csv", csv_body, "text/csv")})
    dataset_id = upload.json()["data"]["datasetId"]

    deletion = client.delete(f"/api/v1/datasets/{dataset_id}", headers=_auth_header(user_token))
    assert deletion.status_code == 403


def test_drift_scan_and_history_routes(tmp_path, monkeypatch):
    _configure_storage(tmp_path, monkeypatch)
    client = TestClient(app)

    signup = client.post("/api/v1/auth/signup", json={"name": "Admin User", "email": "admin@example.com", "password": "password123"})
    token = signup.json()["data"]["token"]

    scan = client.post("/api/v1/drift/scan", headers=_auth_header(token))
    assert scan.status_code == 200
    assert "entry" in scan.json()["data"]

    history = client.get("/api/v1/drift/history", headers=_auth_header(token))
    assert history.status_code == 200
    assert len(history.json()["data"]["items"]) >= 1
