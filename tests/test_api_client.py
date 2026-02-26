import pytest
import uuid
from unittest.mock import patch
from src.ui.api_client import ApiClient
from src.models import Person, Todo


@pytest.fixture
def client():
    return ApiClient()


@pytest.mark.asyncio
@patch("src.ui.api_client.run_db")
async def test_get_todos(mock_run_db, client):
    todo_id = uuid.uuid4()
    person_id = uuid.uuid4()
    # Mock service returning SQLModel Todo objects
    mock_run_db.return_value = [
        Todo(id=todo_id, title="Test", description="Test Desc", person_id=person_id)
    ]

    result = await client.get_todos()
    assert len(result) == 1
    assert result[0].title == "Test"
    mock_run_db.assert_called_once()


@pytest.mark.asyncio
@patch("src.ui.api_client.run_db")
async def test_get_persons(mock_run_db, client):
    person_id = uuid.uuid4()
    mock_run_db.return_value = [Person(id=person_id, name="Test Person")]

    result = await client.get_persons()
    assert len(result) == 1
    assert result[0].name == "Test Person"


@pytest.mark.asyncio
@patch("src.ui.api_client.run_db")
async def test_create_person(mock_run_db, client):
    mock_person = Person(id=uuid.uuid4(), name="New Person")
    mock_run_db.return_value = mock_person

    res = await client.create_person("New Person")
    assert res["success"] is True
    assert res["data"]["name"] == "New Person"


@pytest.mark.asyncio
@patch("src.ui.api_client.run_db")
async def test_delete_person(mock_run_db, client):
    res = await client.delete_person(str(uuid.uuid4()))
    assert res["success"] is True


@pytest.mark.asyncio
@patch("src.ui.api_client.run_db")
async def test_create_todo(mock_run_db, client):
    todo_data = {
        "title": "New Todo",
        "description": "New Desc",
        "person_id": str(uuid.uuid4()),
    }
    res = await client.create_todo(todo_data)
    assert res["success"] is True


@pytest.mark.asyncio
@patch("src.ui.api_client.run_db")
async def test_update_todo(mock_run_db, client):
    todo_data = {
        "id": str(uuid.uuid4()),
        "completed": True,
        "title": "Updated",
        "description": "Updated",
    }
    res = await client.update_todo(todo_data)
    assert res["success"] is True


@pytest.mark.asyncio
@patch("src.ui.api_client.run_db")
async def test_delete_todo(mock_run_db, client):
    res = await client.delete_todo(str(uuid.uuid4()))
    assert res["success"] is True


@pytest.mark.asyncio
@patch("src.ui.api_client.run_db")
async def test_generate_subtasks(mock_run_db, client):
    # Mocking the AI service returning a Todo
    mock_todo = Todo(
        id=uuid.uuid4(), title="Gen", description="Gen Desc", person_id=uuid.uuid4()
    )
    mock_run_db.return_value = mock_todo
    res = await client.generate_subtasks(str(uuid.uuid4()))
    assert res["success"] is True
    assert res["data"]["title"] == "Gen"


@pytest.mark.asyncio
@patch("src.ui.api_client.run_db")
async def test_toggle_subtask(mock_run_db, client):
    res = await client.toggle_subtask(str(uuid.uuid4()), True)
    assert res["success"] is True


@pytest.mark.asyncio
@patch("src.ui.api_client.run_db")
async def test_delete_subtask(mock_run_db, client):
    res = await client.delete_subtask(str(uuid.uuid4()))
    assert res["success"] is True


@pytest.mark.asyncio
@patch("src.ui.api_client.run_db")
async def test_api_client_exception_handling(mock_run_db, client):
    # Force run_db to raise an exception to verify error handling
    mock_run_db.side_effect = Exception("DB Error")

    # Check that exceptions are caught and false/empty lists are returned
    assert await client.get_todos() == []
    assert await client.get_persons() == []

    res = await client.create_person("Fail")
    assert res["success"] is False
    assert "error" in res

    res2 = await client.update_todo({"id": str(uuid.uuid4())})
    assert res2["success"] is False

    assert (await client.delete_person(str(uuid.uuid4())))["success"] is False
    assert (await client.create_todo({}))["success"] is False
    assert (await client.delete_todo(str(uuid.uuid4())))["success"] is False
    assert (await client.generate_subtasks(str(uuid.uuid4())))["success"] is False
    assert (await client.toggle_subtask(str(uuid.uuid4()), True))["success"] is False
    assert (await client.delete_subtask(str(uuid.uuid4())))["success"] is False
