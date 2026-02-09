from unittest.mock import MagicMock
from src.ui.pages.history import HistoryView
from src.models import Person, TodoRead
from uuid import uuid4
from datetime import date


def test_history_view_serialization():
    # Setup Data
    person = Person(id=uuid4(), name="Test Person")
    todo = TodoRead(
        id=uuid4(),
        title="Completed Task",
        description="Desc",
        completed=True,
        person_id=person.id,
        deadline=date.today(),
        priority=1,
        subtasks=[],
    )

    # Mock Callbacks
    mock_delete = MagicMock()
    mock_restore = MagicMock()

    # Init View
    view = HistoryView(
        todos=[todo], persons=[person], on_delete=mock_delete, on_restore=mock_restore
    )

    # Replicate render logic to verify serialization
    completed_todos = [t for t in view.todos if t.completed]
    rows = []
    for t in completed_todos:
        person_name = next(
            (p.name for p in view.persons if str(p.id) == str(t.person_id)), "?"
        )
        rows.append(
            {
                "id": str(t.id),
                "title": t.title,
                "description": t.description or "",
                "person": person_name,
                "deadline": str(t.deadline) if t.deadline else "",
                "priority": t.priority,
                "_raw": t.model_dump(),  # This is what we fixed
            }
        )

    # Assertions
    assert len(rows) == 1
    row = rows[0]
    assert isinstance(row["_raw"], dict)
    assert row["_raw"]["title"] == "Completed Task"
    assert row["_raw"]["id"] == todo.id
