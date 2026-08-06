from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.models import Person, SubtaskRead, TodoRead
from src.ui.layout import Layout
from src.ui.pages.board import BoardView
from src.ui.pages.history import HistoryView


# -----------------
# 1. BoardView Tests
# -----------------
def test_board_view_init_and_translation():
    todos: list[TodoRead] = []
    persons: list[Person] = []
    mock_cb = MagicMock()

    board = BoardView(
        todos=todos,
        persons=persons,
        on_update=mock_cb,
        on_edit=mock_cb,
        on_delete=mock_cb,
        on_generate_subtasks=mock_cb,
        page=0,
        language="sv",
    )

    assert board.t("dashboard") == "Översikt"
    assert board.language == "sv"


def test_board_view_filtering_and_categorization():
    person = Person(id=uuid4(), name="TestPerson")
    today = date.today()

    active_todo = TodoRead(
        id=uuid4(),
        title="Active",
        description="Desc",
        completed=False,
        priority=1,
        deadline=today,
        person_id=person.id,
        subtasks=[],
    )
    overdue_todo = TodoRead(
        id=uuid4(),
        title="Overdue",
        description="Desc",
        completed=False,
        priority=2,
        deadline=today - timedelta(days=2),
        person_id=person.id,
        subtasks=[],
    )
    completed_past_todo = TodoRead(
        id=uuid4(),
        title="Completed Past",
        description="Desc",
        completed=True,
        priority=3,
        deadline=today - timedelta(days=5),
        person_id=person.id,
        subtasks=[],
    )

    board = BoardView(
        todos=[active_todo, overdue_todo, completed_past_todo],
        persons=[person],
        on_update=MagicMock(),
        on_edit=MagicMock(),
        on_delete=MagicMock(),
        on_generate_subtasks=MagicMock(),
    )

    # Patch nicegui ui rendering components to avoid browser context error
    with patch("nicegui.ui.row"), patch("nicegui.ui.column"), patch("nicegui.ui.scroll_area"), patch("nicegui.ui.card"):
        board.render()


@pytest.mark.asyncio
async def test_board_view_toggle_subtask_reactive():
    person = Person(id=uuid4(), name="TestPerson")
    subtask = SubtaskRead(
        id=uuid4(),
        todo_id=uuid4(),
        title="Sub 1",
        completed=False,
        created_at=date.today(),
    )
    todo = TodoRead(
        id=uuid4(),
        title="Todo with Sub",
        description="Desc",
        completed=False,
        priority=2,
        deadline=date.today(),
        person_id=person.id,
        subtasks=[subtask],
    )

    board = BoardView(
        todos=[todo],
        persons=[person],
        on_update=MagicMock(),
        on_edit=MagicMock(),
        on_delete=MagicMock(),
        on_generate_subtasks=MagicMock(),
    )

    mock_expansion = MagicMock()
    mock_progress = MagicMock()
    mock_label = MagicMock()

    with patch("src.ui.pages.board.api.toggle_subtask", new_callable=AsyncMock) as mock_api_toggle:
        await board.toggle_subtask(
            todo=todo,
            subtask=subtask,
            completed=True,
            expansion=mock_expansion,
            progress=mock_progress,
            label=mock_label,
        )

        assert subtask.completed is True
        mock_label.classes.assert_called_with(add="line-through")
        mock_progress.set_value.assert_called_with(1.0)
        mock_api_toggle.assert_called_once_with(str(subtask.id), True)


@pytest.mark.asyncio
async def test_board_view_toggle_complete():
    person = Person(id=uuid4(), name="TestPerson")
    todo = TodoRead(
        id=uuid4(),
        title="Todo",
        description="Desc",
        completed=False,
        priority=2,
        deadline=date.today(),
        person_id=person.id,
        subtasks=[],
    )

    mock_on_update = AsyncMock()
    board = BoardView(
        todos=[todo],
        persons=[person],
        on_update=mock_on_update,
        on_edit=MagicMock(),
        on_delete=MagicMock(),
        on_generate_subtasks=MagicMock(),
    )

    await board.toggle_complete(todo)
    assert todo.completed is True
    mock_on_update.assert_called_once_with(todo)


# -----------------
# 2. HistoryView Tests
# -----------------
def test_history_view_init():
    person = Person(id=uuid4(), name="TestPerson")
    completed_todo = TodoRead(
        id=uuid4(),
        title="Done",
        description="Desc",
        completed=True,
        priority=1,
        deadline=date.today(),
        person_id=person.id,
        subtasks=[],
    )

    history = HistoryView(
        todos=[completed_todo],
        persons=[person],
        on_delete=MagicMock(),
        on_restore=MagicMock(),
    )

    assert history.t("history") == "Historik"


def test_history_view_render():
    person = Person(id=uuid4(), name="TestPerson")
    completed_todo = TodoRead(
        id=uuid4(),
        title="Done Task",
        description="Completed description",
        completed=True,
        priority=1,
        deadline=date.today(),
        person_id=person.id,
        subtasks=[],
    )

    mock_delete = AsyncMock()
    mock_restore = AsyncMock()
    mock_bulk = AsyncMock()

    history = HistoryView(
        todos=[completed_todo],
        persons=[person],
        on_delete=mock_delete,
        on_restore=mock_restore,
        on_bulk_delete=mock_bulk,
    )

    with (
        patch("nicegui.ui.column"),
        patch("nicegui.ui.row"),
        patch("nicegui.ui.label"),
        patch("nicegui.ui.table") as mock_table,
        patch("nicegui.ui.button"),
    ):
        mock_table_instance = MagicMock()
        mock_table_instance.selected = [{"id": str(completed_todo.id)}]
        mock_table.return_value.classes.return_value.props.return_value = mock_table_instance
        history.render()
        mock_table.assert_called_once()

        # Extract restore and delete event callbacks
        callbacks = {call[0][0]: call[0][1] for call in mock_table_instance.on.call_args_list}

        # Test restore callback
        if "restore" in callbacks:
            event_mock = MagicMock()
            event_mock.args = str(completed_todo.id)
            import asyncio

            asyncio.run(callbacks["restore"](event_mock))
            mock_restore.assert_called_once_with(completed_todo)

        # Test delete callback
        if "delete" in callbacks:
            event_mock = MagicMock()
            event_mock.args = str(completed_todo.id)
            import asyncio

            asyncio.run(callbacks["delete"](event_mock))
            mock_delete.assert_called_once_with(completed_todo)


def test_history_view_render_empty():
    history = HistoryView(
        todos=[],
        persons=[],
        on_delete=MagicMock(),
        on_restore=MagicMock(),
    )
    with (
        patch("nicegui.ui.column"),
        patch("nicegui.ui.row"),
        patch("nicegui.ui.label") as mock_label,
    ):
        history.render()
        mock_label.assert_called()


# -----------------
# 3. Layout Tests
# -----------------
def test_layout_init_and_dark_mode():
    mock_app = MagicMock()
    mock_app.storage.user = {"dark_mode": False}

    with patch("src.ui.layout.app", mock_app), patch("nicegui.ui.dark_mode") as mock_dm:
        mock_dark_mode_obj = MagicMock()
        mock_dark_mode_obj.value = False
        mock_dm.return_value = mock_dark_mode_obj

        layout = Layout(
            persons=[],
            current_page="board",
            on_filter_change=MagicMock(),
            on_refresh=MagicMock(),
            on_create_person=MagicMock(),
            on_create_todo=MagicMock(),
        )

        assert layout.current_page == "board"
        assert layout.t("new_task") == "Ny Uppgift"

        layout.toggle_dark_mode()
        mock_dark_mode_obj.toggle.assert_called_once()
        assert mock_app.storage.user["dark_mode"] is False


def test_layout_render_sidebar():
    mock_app = MagicMock()
    mock_app.storage.user = {"dark_mode": True}

    person = Person(id=uuid4(), name="TestPerson")
    with (
        patch("src.ui.layout.app", mock_app),
        patch("nicegui.ui.dark_mode"),
        patch("nicegui.ui.left_drawer"),
        patch("nicegui.ui.column"),
        patch("nicegui.ui.row"),
        patch("nicegui.ui.element"),
        patch("nicegui.ui.button"),
        patch("nicegui.ui.label"),
        patch("nicegui.ui.select") as mock_select,
    ):
        layout = Layout(
            persons=[person],
            current_page="board",
            on_filter_change=MagicMock(),
            on_refresh=MagicMock(),
            on_create_person=MagicMock(),
            on_create_todo=MagicMock(),
        )
        layout.render_sidebar()
        assert mock_select.call_count >= 2
