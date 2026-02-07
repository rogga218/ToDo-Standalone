from src.services import person_service
from src.models import PersonCreate, Person
from sqlmodel import Session
import pytest
from fastapi import HTTPException
import uuid


def test_create_person(session: Session):
    person_data = PersonCreate(name="Alice")
    person = person_service.create_person(session, person_data)
    assert person.id is not None
    assert person.name == "Alice"


def test_create_duplicate_person(session: Session):
    person_service.create_person(session, PersonCreate(name="Bob"))
    with pytest.raises(HTTPException) as excinfo:
        person_service.create_person(session, PersonCreate(name="Bob"))
    assert excinfo.value.status_code == 409


def test_get_persons(session: Session):
    person_service.create_person(session, PersonCreate(name="Charlie"))
    person_service.create_person(session, PersonCreate(name="Dave"))
    persons = person_service.get_persons(session)
    assert len(persons) == 2
    # Should be sorted by name
    assert persons[0].name == "Charlie"
    assert persons[1].name == "Dave"


def test_delete_person_success(session: Session):
    p = person_service.create_person(session, PersonCreate(name="Eve"))
    person_service.delete_person(session, str(p.id))
    assert session.get(Person, p.id) is None


def test_delete_person_with_todos_fails(session: Session):
    # Create person
    p = person_service.create_person(session, PersonCreate(name="Frank"))

    # Manually adding a Todo via service would require importing todo_service
    # To avoid circular imports in tests or complexity, we can use the model directly or valid service call
    from src.services import todo_service
    from src.models import TodoCreate

    todo_service.create_todo(
        session, TodoCreate(title="Task", description="Desc", person_id=p.id)
    )

    with pytest.raises(HTTPException) as excinfo:
        person_service.delete_person(session, str(p.id))
    assert excinfo.value.status_code == 400


def test_delete_person_not_found(session: Session):
    with pytest.raises(HTTPException) as excinfo:
        person_service.delete_person(session, str(uuid.uuid4()))
    assert excinfo.value.status_code == 404
