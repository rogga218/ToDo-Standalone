from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.models import Person, TodoRead
from src.ui.components.dialogs import PersonDialog, TodoDialog


def test_todo_dialog_edit_data_handling():
    person = Person(id=uuid4(), name="Test Person")
    mock_success = MagicMock()

    dialog = TodoDialog(persons=[person], on_success=mock_success)

    todo = TodoRead(
        id=uuid4(),
        title="Test Task",
        description="Desc",
        person_id=person.id,
        priority=1,
        deadline=date.today(),
        completed=False,
        subtasks=[],
    )

    with patch.object(dialog, "_render_dialog") as mock_render:
        dialog.edit(todo)
        mock_render.assert_called_once_with("Redigera Uppgift", todo)


def test_person_dialog_init():
    persons = [Person(id=uuid4(), name="P1")]
    todos = []
    mock_success = MagicMock()

    dialog = PersonDialog(persons, todos, mock_success)
    assert len(dialog.persons) == 1
    assert dialog.persons[0].name == "P1"
    assert dialog.t("name_required") == "Namn krävs"


def test_todo_dialog_create_rendering():
    person = Person(id=uuid4(), name="Test Person")
    mock_success = MagicMock()

    dialog = TodoDialog(persons=[person], on_success=mock_success)
    with patch.object(dialog, "_render_dialog") as mock_render:
        dialog.create()
        mock_render.assert_called_once_with("Ny Uppgift")


@pytest.mark.asyncio
async def test_person_dialog_refresh_list():
    person = Person(id=uuid4(), name="P1")
    dialog = PersonDialog([person], [], MagicMock())
    dialog.list_container = MagicMock()

    new_persons = [person, Person(id=uuid4(), name="P2")]
    with patch("src.ui.components.dialogs.api.get_persons", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = new_persons
        with patch.object(dialog, "render_list_items"):
            await dialog.refresh_list()
            assert len(dialog.persons) == 2


def test_person_dialog_render_list_items():
    p1 = Person(id=uuid4(), name="P1")
    p2 = Person(id=uuid4(), name="P2")
    todo = TodoRead(
        id=uuid4(),
        title="T1",
        description="Desc",
        person_id=p1.id,
        priority=1,
        deadline=date.today(),
        completed=False,
        subtasks=[],
    )

    dialog = PersonDialog(persons=[p1, p2], todos=[todo], on_success=MagicMock())

    with patch("nicegui.ui.row"), patch("nicegui.ui.label"), patch("nicegui.ui.button") as mock_btn:
        dialog.render_list_items()
        assert mock_btn.call_count >= 2


@pytest.mark.asyncio
async def test_person_dialog_delete_person_handler():
    p1 = Person(id=uuid4(), name="P1")
    mock_on_success = AsyncMock()
    dialog = PersonDialog(persons=[p1], todos=[], on_success=mock_on_success)
    dialog.refresh_list = AsyncMock()

    with patch("src.ui.components.dialogs.api.delete_person", new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = {"success": True}
        with patch("nicegui.ui.notify"):
            # Execute render to capture delete handler
            with patch("nicegui.ui.row"), patch("nicegui.ui.label"), patch("nicegui.ui.button") as mock_btn:
                dialog.render_list_items()
                # Get the on_click handler passed to ui.button for delete
                delete_handler = mock_btn.call_args[1].get("on_click")
                if delete_handler:
                    await delete_handler()
                    mock_delete.assert_called_once_with(str(p1.id))
                    mock_on_success.assert_called_once()
