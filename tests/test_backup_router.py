import json

from fastapi.testclient import TestClient
from sqlmodel import Session

from src.models import Person, Todo


def test_backup_router_export_and_import(client: TestClient, session: Session):
    person = Person(name="RouterPerson")
    session.add(person)
    session.commit()

    todo = Todo(
        title="Router Task",
        description="Router Desc",
        priority=1,
        person_id=person.id,
    )
    session.add(todo)
    session.commit()

    # 1. GET /api/backup/export?format=json
    resp_json = client.get("/api/backup/export?format=json")
    assert resp_json.status_code == 200
    assert resp_json.headers["content-type"] == "application/json"
    json_data = resp_json.json()
    assert "todos" in json_data

    # 2. GET /api/backup/export?format=csv
    resp_csv = client.get("/api/backup/export?format=csv")
    assert resp_csv.status_code == 200
    assert "text/csv" in resp_csv.headers["content-type"]
    assert "Router Task" in resp_csv.text

    # 3. POST /api/backup/import (JSON)
    json_bytes = json.dumps(json_data).encode("utf-8")
    resp_import = client.post(
        "/api/backup/import",
        files={"file": ("backup.json", json_bytes, "application/json")},
    )
    assert resp_import.status_code == 200
    assert resp_import.json()["success"] is True

    # 4. POST /api/backup/import (CSV)
    resp_import_csv = client.post(
        "/api/backup/import",
        files={"file": ("backup.csv", resp_csv.text.encode("utf-8"), "text/csv")},
    )
    assert resp_import_csv.status_code == 200
    assert resp_import_csv.json()["success"] is True


def test_backup_router_import_file_too_large(client: TestClient):
    """Ensure uploads exceeding 10MB are rejected with HTTP 413."""
    from src.routers.backup import MAX_BACKUP_SIZE

    oversized_bytes = b" " * (MAX_BACKUP_SIZE + 50)
    resp = client.post(
        "/api/backup/import",
        files={"file": ("large_backup.json", oversized_bytes, "application/json")},
    )
    assert resp.status_code == 413
    assert "File exceeds maximum allowed size" in resp.json()["detail"]


def test_backup_router_import_too_many_records(client: TestClient):
    """Ensure import fails when record count exceeds safety ceiling."""
    too_many_todos = [{"title": f"Task {i}"} for i in range(5001)]
    payload = {"todos": too_many_todos}
    payload_bytes = json.dumps(payload).encode("utf-8")

    resp = client.post(
        "/api/backup/import",
        files={"file": ("overflow.json", payload_bytes, "application/json")},
    )
    assert resp.status_code == 400
    assert "exceeds maximum allowed records" in resp.json()["detail"]
