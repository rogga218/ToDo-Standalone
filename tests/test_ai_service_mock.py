import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from src.models import PersonCreate, TodoCreate
from src.services import ai_service, person_service, todo_service


# Mock response object
class MockGeminiResponse:
    def __init__(self, text):
        self.text = text


def test_generate_subtasks_success(session: Session):
    # Setup data
    p = person_service.create_person(session, PersonCreate(name="AI User"))
    todo = todo_service.create_todo(session, TodoCreate(title="Plan Party", description="Big party", person_id=p.id))

    # Mock settings to return API Key
    with patch("src.services.ai_service.get_settings") as mock_settings:
        mock_settings.return_value.GEMINI_API_KEY = "TEST_KEY"

        # Mock google.genai.Client
        with patch("google.genai.Client") as mock_client_cls:
            mock_client_instance = MagicMock()
            mock_client_cls.return_value = mock_client_instance

            # Setup response
            expected_subtasks = ["Buy chips", "Invite friends", "Clean house"]
            mock_client_instance.models.generate_content.return_value = MockGeminiResponse(
                text=f"```json\n{str(expected_subtasks).replace("'", '"')}\n```"
            )

            # Call service
            updated_todo = ai_service.generate_subtasks(session, todo.id)

            # Verify
            assert len(updated_todo.subtasks) == 3
            titles = sorted([st.title for st in updated_todo.subtasks])
            assert titles == sorted(expected_subtasks)


def test_generate_subtasks_no_api_key(session: Session):
    # Setup data
    p = person_service.create_person(session, PersonCreate(name="NoKey User"))
    todo = todo_service.create_todo(session, TodoCreate(title="Task", description="Desc", person_id=p.id))

    with patch("src.services.ai_service.get_settings") as mock_settings:
        mock_settings.return_value.GEMINI_API_KEY = None

        with pytest.raises(HTTPException) as excinfo:
            ai_service.generate_subtasks(session, todo.id)
        assert excinfo.value.status_code == 500


def test_generate_subtasks_empty_response(session: Session):
    """Test when Gemini returns an empty response text."""
    from src.models import Todo

    mock_todo = Todo(title="Test", description="Test", person_id=uuid.uuid4())

    with patch.object(session, "get", return_value=mock_todo):
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = ""  # Empty
        mock_client_instance.models.generate_content.return_value = mock_response

        with patch("src.services.ai_service.get_settings") as mock_settings:
            mock_settings.return_value.GEMINI_API_KEY = "dummy-key"
            with patch("google.genai.Client", return_value=mock_client_instance):
                with pytest.raises(HTTPException) as excinfo:
                    from src.services.ai_service import generate_subtasks

                    generate_subtasks(session, uuid.uuid4())

                assert excinfo.value.status_code == 500
                assert "Empty response from AI" in excinfo.value.detail


def test_generate_subtasks_invalid_json(session: Session):
    """Test when Gemini returns text that cannot be parsed as JSON."""
    from src.models import Todo

    mock_todo = Todo(title="Test", description="Test", person_id=uuid.uuid4())

    with patch.object(session, "get", return_value=mock_todo):
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is not JSON data, just plain text"
        mock_client_instance.models.generate_content.return_value = mock_response

        with patch("src.services.ai_service.get_settings") as mock_settings:
            mock_settings.return_value.GEMINI_API_KEY = "dummy-key"
            with patch("google.genai.Client", return_value=mock_client_instance):
                with pytest.raises(HTTPException) as excinfo:
                    from src.services.ai_service import generate_subtasks

                    generate_subtasks(session, uuid.uuid4())

                assert excinfo.value.status_code == 500
                assert "AI Generation Failed" in excinfo.value.detail


def test_generate_subtasks_refresh_fails(session: Session):
    """Test the edge case where the Todo cannot be found after it was updated."""
    from src.models import Todo

    mock_todo = Todo(title="Test", description="Test", person_id=uuid.uuid4())

    with patch.object(session, "get", return_value=mock_todo):
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '["Subtask 1"]'
        mock_client_instance.models.generate_content.return_value = mock_response

        # Force the refresh query (exec().first()) to return None
        mock_exec_result = MagicMock()
        mock_exec_result.first.return_value = None

        with patch.object(session, "exec", return_value=mock_exec_result):
            with patch("src.services.ai_service.get_settings") as mock_settings:
                mock_settings.return_value.GEMINI_API_KEY = "dummy-key"
                with patch("google.genai.Client", return_value=mock_client_instance):
                    with pytest.raises(HTTPException) as excinfo:
                        from src.services.ai_service import generate_subtasks

                        generate_subtasks(session, uuid.uuid4())

                    assert excinfo.value.status_code == 500
                    assert "Todo not found after update" in excinfo.value.detail


def test_generate_subtasks_todo_not_found(session: Session):
    with patch("src.services.ai_service.get_settings") as mock_settings:
        mock_settings.return_value.GEMINI_API_KEY = "TEST_KEY"

        with pytest.raises(HTTPException) as excinfo:
            ai_service.generate_subtasks(session, uuid.uuid4())
        assert excinfo.value.status_code == 404
