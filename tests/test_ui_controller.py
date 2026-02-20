import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from src.ui.controller import ToDoController
from src.models import TodoRead


@pytest.fixture
def controller():
    return ToDoController()


@pytest.mark.asyncio
@patch("src.ui.controller.api")
async def test_initialize(mock_api, controller):
    mock_api.get_todos = AsyncMock(return_value=[])
    mock_api.get_persons = AsyncMock(return_value=[])

    await controller.initialize()

    mock_api.get_todos.assert_awaited_once()
    mock_api.get_persons.assert_awaited_once()


@pytest.mark.asyncio
@patch("src.ui.controller.api")
@patch("src.ui.controller.ui")
@patch("src.ui.controller.app")
@patch("src.ui.controller.Layout")
@patch("src.ui.controller.BoardView")
@patch("src.ui.controller.HistoryView")
@patch("src.ui.controller.TodoDialog")
async def test_controller_rendering_and_actions(
    mock_todo_dialog,
    mock_history,
    mock_board,
    mock_layout,
    mock_app,
    mock_ui,
    mock_api,
    controller,
):
    mock_api.get_todos = AsyncMock(return_value=[])
    mock_api.get_persons = AsyncMock(return_value=[])

    # Enable app.storage.user access
    mock_app.storage.user = {"language": "sv"}

    # Execute layout rendering
    await controller.render_layout("board", 0)

    mock_layout.assert_called_once()
    mock_board.assert_called_once()

    # Extract the nested callbacks passed to BoardView
    board_kwargs = mock_board.call_args.kwargs
    on_update = board_kwargs["on_update"]
    on_edit = board_kwargs["on_edit"]
    on_delete = board_kwargs["on_delete"]
    on_generate_subtasks = board_kwargs["on_generate_subtasks"]

    # Dummy TodoRead data
    dummy_todo = TodoRead(
        id=uuid.uuid4(), title="Test", description="Test Desc", person_id=uuid.uuid4()
    )

    # Test on_update callback
    mock_api.update_todo = AsyncMock(return_value={"success": True})
    await on_update(dummy_todo)
    mock_api.update_todo.assert_awaited_once()

    # Test on_update failure path
    mock_api.update_todo = AsyncMock(return_value={"success": False, "error": "err"})
    await on_update(dummy_todo)

    # Test on_edit callback
    mock_dialog_instance = MagicMock()
    mock_todo_dialog.return_value = mock_dialog_instance
    on_edit(dummy_todo)
    mock_dialog_instance.edit.assert_called_once()

    # Test on_delete callback
    mock_api.delete_todo = AsyncMock(return_value={"success": True})
    await on_delete(dummy_todo)
    mock_api.delete_todo.assert_awaited_once()

    # Test on_delete failure path
    mock_api.delete_todo = AsyncMock(return_value={"success": False, "error": "err"})
    await on_delete(dummy_todo)

    # Test on_generate_subtasks callback
    mock_api.generate_subtasks = AsyncMock(return_value={"success": True})
    await on_generate_subtasks(dummy_todo)
    mock_api.generate_subtasks.assert_awaited_once()

    # Test on_generate_subtasks failure path
    mock_api.generate_subtasks = AsyncMock(
        return_value={"success": False, "error": "err"}
    )
    await on_generate_subtasks(dummy_todo)

    # Switch to history view to extract its unique callbacks
    await controller.render_layout("history", 0)
    mock_history.assert_called_once()

    history_kwargs = mock_history.call_args.kwargs
    on_restore = history_kwargs["on_restore"]
    on_bulk_delete = history_kwargs["on_bulk_delete"]

    # Test on_restore callback
    mock_api.update_todo = AsyncMock(return_value={"success": True})
    await on_restore(dummy_todo)
    mock_api.update_todo.assert_awaited_once()

    # Test on_restore failure path
    mock_api.update_todo = AsyncMock(return_value={"success": False, "error": "err"})
    await on_restore(dummy_todo)

    # Test on_bulk_delete callback
    mock_api.delete_todo = AsyncMock()
    await on_bulk_delete([dummy_todo, dummy_todo])
    assert mock_api.delete_todo.call_count == 2

    # Extract callbacks passed to Layout to test handlers
    layout_kwargs = mock_layout.call_args.kwargs
    on_filter_change = layout_kwargs["on_filter_change"]
    on_language_change = layout_kwargs["on_language_change"]
    on_create_person = layout_kwargs["on_create_person"]
    on_create_todo = layout_kwargs["on_create_todo"]

    await on_filter_change("person", "new_val")
    assert mock_app.storage.user["filter_person"] == "new_val"

    await on_language_change("en")
    assert mock_app.storage.user["language"] == "en"

    with patch("src.ui.controller.PersonDialog") as mock_person_dialog:
        mock_p_inst = MagicMock()
        mock_person_dialog.return_value = mock_p_inst
        await on_create_person(None)
        mock_p_inst.open.assert_called_once()

    await on_create_todo(None)
    mock_dialog_instance.create.assert_called_once()
