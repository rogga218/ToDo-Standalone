from typing import List, Optional
import uuid
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from src.models import (
    Todo,
    TodoCreate,
    TodoUpdate,
    Person,
    Subtask,
    SubtaskCreate,
)


def create_todo(session: Session, todo: TodoCreate) -> Todo:
    if not session.get(Person, todo.person_id):
        raise HTTPException(status_code=404, detail="Person not found")

    db_todo = Todo.model_validate(todo)
    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)
    # Prime subtasks
    _ = db_todo.subtasks
    return db_todo


def get_todos(
    session: Session,
    offset: int = 0,
    limit: int = 1000,
    filter_person_id: Optional[uuid.UUID] = None,
    filter_priority: Optional[int] = None,
) -> List[Todo]:
    query = select(Todo).options(selectinload(Todo.subtasks)).order_by(Todo.title)

    # Apply filters if provided (useful for direct service calls even if API didn't fully use them yet)
    if filter_person_id:
        query = query.where(Todo.person_id == filter_person_id)
    if filter_priority:
        query = query.where(Todo.priority == filter_priority)

    query = query.offset(offset).limit(limit)
    return session.exec(query).all()


def get_todo(session: Session, todo_id: uuid.UUID) -> Optional[Todo]:
    query = select(Todo).where(Todo.id == todo_id).options(selectinload(Todo.subtasks))
    return session.exec(query).first()


def update_todo(session: Session, todo_id: uuid.UUID, todo_data: TodoUpdate) -> Todo:
    db_todo = session.get(Todo, todo_id)
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    todo_data_dict = todo_data.dict(exclude_unset=True)
    todo_data_dict = {k: v for k, v in todo_data_dict.items() if v is not None}

    if "person_id" in todo_data_dict:
        if not session.get(Person, todo_data_dict["person_id"]):
            raise HTTPException(status_code=404, detail="Person not found")

    for key, value in todo_data_dict.items():
        setattr(db_todo, key, value)

    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)
    _ = db_todo.subtasks
    return db_todo


def delete_todo(session: Session, todo_id: uuid.UUID) -> None:
    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    session.delete(todo)
    session.commit()


# --- Subtasks ---


def create_subtask(session: Session, subtask: SubtaskCreate) -> Subtask:
    if not session.get(Todo, subtask.todo_id):
        raise HTTPException(status_code=404, detail="Todo not found")
    db_subtask = Subtask.model_validate(subtask)
    session.add(db_subtask)
    session.commit()
    session.refresh(db_subtask)
    return db_subtask


def update_subtask(session: Session, subtask_id: uuid.UUID, completed: bool) -> Subtask:
    subtask = session.get(Subtask, subtask_id)
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    subtask.completed = completed
    session.add(subtask)
    session.commit()
    session.refresh(subtask)
    return subtask


def delete_subtask(session: Session, subtask_id: uuid.UUID) -> None:
    subtask = session.get(Subtask, subtask_id)
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    session.delete(subtask)
    session.commit()
