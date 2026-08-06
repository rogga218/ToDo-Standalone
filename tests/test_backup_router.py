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
