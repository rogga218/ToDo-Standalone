from datetime import date

import pytest
from sqlmodel import Session, select

from src.models import Person, Subtask, Todo
from src.services.export_service import ExportService


def test_export_and_import_json(session: Session):
    person = Person(name="BackupPerson")
    session.add(person)
    session.commit()

    todo = Todo(
        title="Backup Task",
        description="Backup description",
        priority=1,
        deadline=date.today(),
        completed=False,
        person_id=person.id,
    )
    session.add(todo)
    session.commit()

    subtask = Subtask(todo_id=todo.id, title="Backup Subtask", completed=True)
    session.add(subtask)
    session.commit()

    # 1. Export to JSON
    json_data = ExportService.export_data_json(session)
    assert json_data["version"] == 1
    assert len(json_data["persons"]) >= 1
    assert len(json_data["todos"]) >= 1

    # 2. Clear database
    session.delete(subtask)
    session.delete(todo)
    session.delete(person)
    session.commit()

    # 3. Import JSON back
    res = ExportService.import_data_json(session, json_data)
    assert res["success"] is True
    assert res["imported_todos"] >= 1

    # 4. Verify items re-created
    imported_todos = session.exec(select(Todo)).all()
    assert any(t.title == "Backup Task" for t in imported_todos)

    imported_subs = session.exec(select(Subtask)).all()
    assert any(s.title == "Backup Subtask" and s.completed is True for s in imported_subs)


def test_export_and_import_csv(session: Session):
    person = Person(name="CSVPerson")
    session.add(person)
    session.commit()

    todo = Todo(
        title="CSV Task",
        description="CSV description",
        priority=2,
        deadline=date.today(),
        completed=True,
        person_id=person.id,
    )
    session.add(todo)
    session.commit()

    subtask = Subtask(todo_id=todo.id, title="CSV Subtask", completed=False)
    session.add(subtask)
    session.commit()

    # 1. Export CSV
    csv_str = ExportService.export_data_csv(session)
    assert "CSV Task" in csv_str
    assert "CSVPerson" in csv_str
    assert "CSV Subtask" in csv_str

    # 2. Import CSV
    res = ExportService.import_data_csv(session, csv_str)
    assert res["success"] is True
    assert res["imported_todos"] >= 1


def test_import_data_json_invalid(session: Session):
    with pytest.raises(ValueError, match="Invalid JSON backup structure"):
        ExportService.import_data_json(session, {"invalid": True})
