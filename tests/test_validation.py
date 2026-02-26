import pytest
from src.models import PersonCreate, TodoCreate, TodoUpdate
from pydantic import ValidationError
import uuid
from datetime import date

# --- Person Validation Tests ---


def test_person_name_min_length():
    """Test that person name must be at least 2 characters."""
    with pytest.raises(ValidationError) as excinfo:
        PersonCreate(name="a")
    # Pydantic validation errors contain details, we just check it raised
    assert "name_too_short" in str(excinfo.value) or "min_length" in str(excinfo.value)


def test_person_name_max_length():
    """Test that person name cannot exceed 50 characters."""
    with pytest.raises(ValidationError):
        PersonCreate(name="a" * 51)


def test_person_name_invalid_chars():
    """Test that person name regex excludes digits/special chars."""
    with pytest.raises(ValidationError):
        PersonCreate(name="User123")

    with pytest.raises(ValidationError):
        PersonCreate(name="User!")


def test_person_name_valid_chars():
    """Test allowed characters (dots not allowing based on regex in models.py which allows letters, spaces, hyphens, apostrophes)."""
    # Regex: ^[a-zA-Z\u00C0-\u00FF][a-zA-Z\u00C0-\u00FF \-\']*[a-zA-Z\u00C0-\u00FF]$
    p = PersonCreate(name="Bo-Goran")
    assert p.name == "Bo-Goran"

    p2 = PersonCreate(name="O'Reilly")
    assert p2.name == "O'Reilly"


# --- Todo Validation Tests ---


def test_todo_title_min_length():
    """Test that todo title cannot be empty."""
    pid = uuid.uuid4()
    with pytest.raises(ValidationError):
        TodoCreate(title="", description="Desc", person_id=pid)


def test_todo_title_max_length():
    """Test that todo title cannot exceed 50 characters."""
    pid = uuid.uuid4()
    with pytest.raises(ValidationError):
        TodoCreate(title="a" * 51, description="Desc", person_id=pid)


def test_todo_description_min_length():
    """Test that todo description cannot be empty."""
    pid = uuid.uuid4()
    with pytest.raises(ValidationError):
        TodoCreate(title="Title", description="", person_id=pid)


def test_todo_description_max_length():
    """Test that todo description cannot exceed 500 characters."""
    pid = uuid.uuid4()
    with pytest.raises(ValidationError):
        TodoCreate(title="Title", description="a" * 501, person_id=pid)


def test_todo_valid_creation():
    """Test valid creation."""
    pid = uuid.uuid4()
    t = TodoCreate(
        title="Clean House",
        description="Kitchen and Living room",
        person_id=pid,
        deadline=date.today(),
    )
    assert t.title == "Clean House"


def test_person_name_invalid_type():
    with pytest.raises(ValidationError) as excinfo:
        PersonCreate(name=123)
    assert "invalid_name_type" in str(excinfo.value)


def test_todo_title_invalid_type():
    pid = uuid.uuid4()
    with pytest.raises(ValidationError) as excinfo:
        TodoCreate(title=123, description="Desc", person_id=pid)
    assert "Titeln måste vara en textsträng" in str(excinfo.value)


def test_todo_deadline_invalid_type():
    pid = uuid.uuid4()
    with pytest.raises(ValidationError) as excinfo:
        TodoCreate(title="T", description="D", person_id=pid, deadline=123)
    assert "Deadline måste" in str(excinfo.value)


def test_todo_update_deadline_invalid_type():
    with pytest.raises(ValidationError) as excinfo:
        TodoUpdate(deadline=123)
    assert "Deadline måste" in str(excinfo.value)


def test_todo_update_priority_invalid():
    """Test validating an invalid priority in TodoUpdate."""
    # Test values below minimum priority
    with pytest.raises(ValidationError) as exc_info:
        TodoUpdate(priority=0)
    assert "Prioritet måste vara mellan 1 och 3" in str(
        exc_info.value
    ) or "Input should be greater than or equal to 1" in str(exc_info.value)

    # Test values above maximum priority
    with pytest.raises(ValidationError) as exc_info:
        TodoUpdate(priority=4)
    assert "Prioritet måste vara mellan 1 och 3" in str(
        exc_info.value
    ) or "Input should be less than or equal to 3" in str(exc_info.value)


def test_todo_update_deadline_invalid_type_str():
    """Test passing invalid types to TodoUpdate."""
    with pytest.raises(ValidationError):
        TodoUpdate(deadline=12345)  # Passing integer
