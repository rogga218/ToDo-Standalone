from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

from src.models import Person
from src.ui.components.dialogs import PersonDialog, TodoDialog


def test_todo_dialog_edit_data_handling():
    # Setup
    person = Person(id=uuid4(), name="Test Person")
    mock_success = MagicMock()

    dialog = TodoDialog(persons=[person], on_success=mock_success)

    # Test Data (Dictionary as expected by current implementation)
    todo_data = {
        "id": uuid4(),
        "title": "Test Task",
        "description": "Desc",
        "person_id": person.id,
        "priority": 1,
        "deadline": date.today(),
        "completed": False,
    }

    # Verify _render_dialog is called with correct data
    # We patch _render_dialog to avoid actual UI rendering which requires a browser context
    with patch.object(dialog, "_render_dialog") as mock_render:
        dialog.edit(todo_data)

        # Assert
        mock_render.assert_called_once()
        args, _ = mock_render.call_args
        assert args[1] == todo_data
        assert args[1]["title"] == "Test Task"


def test_person_dialog_init():
    # Verify PersonDialog initializes correctly
    persons = [Person(id=uuid4(), name="P1")]
    todos = []
    mock_success = MagicMock()

    dialog = PersonDialog(persons, todos, mock_success)
    assert len(dialog.persons) == 1
    assert dialog.persons[0].name == "P1"
