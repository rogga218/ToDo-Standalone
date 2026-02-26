from src.services import todo_service
from src.models import TodoCreate, Person
from sqlmodel import Session
import pytest
import uuid


def test_create_todo(session: Session):
    # Setup Person
    person = Person(name="Test Person")
    session.add(person)
    session.commit()
    session.refresh(person)

    # Test
    todo_data = TodoCreate(
        title="Test Task", description="Test Description", person_id=person.id
    )
    todo = todo_service.create_todo(session, todo_data)

    assert todo.id is not None
    assert todo.title == "Test Task"
    assert todo.person_id == person.id
    assert todo.completed is False


def test_get_todos(session: Session):
    # Setup
    person = Person(name="Test Person")
    session.add(person)
    session.commit()
    session.refresh(person)

    _ = todo_service.create_todo(
        session, TodoCreate(title="Task 1", description="Desc 1", person_id=person.id)
    )
    _ = todo_service.create_todo(
        session, TodoCreate(title="Task 2", description="Desc 2", person_id=person.id)
    )

    # Test
    todos = todo_service.get_todos(session)
    assert len(todos) == 2
    assert todos[0].title == "Task 1"
    assert todos[1].title == "Task 2"


def test_delete_todo(session: Session):
    # Setup
    person = Person(name="Test Person")
    session.add(person)
    session.commit()
    session.refresh(person)

    t1 = todo_service.create_todo(
        session, TodoCreate(title="Task 1", description="Desc 1", person_id=person.id)
    )

    # Test
    todo_service.delete_todo(session, t1.id)

    todos = todo_service.get_todos(session)
    assert len(todos) == 0


def test_create_todo_person_not_found(session: Session):
    from fastapi import HTTPException

    todo_data = TodoCreate(
        title="Test Task", description="Test Description", person_id=uuid.uuid4()
    )
    with pytest.raises(HTTPException) as excinfo:
        todo_service.create_todo(session, todo_data)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Person not found"


def test_update_todo_not_found(session: Session):
    from fastapi import HTTPException
    from src.models import TodoUpdate

    with pytest.raises(HTTPException) as excinfo:
        todo_service.update_todo(session, uuid.uuid4(), TodoUpdate())
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Todo not found"


def test_delete_todo_not_found(session: Session):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as excinfo:
        todo_service.delete_todo(session, uuid.uuid4())
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Todo not found"


def test_create_subtask_not_found(session: Session):
    from fastapi import HTTPException
    from src.models import SubtaskCreate

    with pytest.raises(HTTPException) as excinfo:
        todo_service.create_subtask(
            session, SubtaskCreate(title="Test", todo_id=uuid.uuid4())
        )
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Todo not found"


def test_update_subtask_not_found(session: Session):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as excinfo:
        todo_service.update_subtask(session, uuid.uuid4(), True)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Subtask not found"


def test_delete_subtask_not_found(session: Session):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as excinfo:
        todo_service.delete_subtask(session, uuid.uuid4())
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Subtask not found"
