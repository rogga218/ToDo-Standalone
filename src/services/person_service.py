from typing import List
import uuid
from sqlmodel import Session, select
from fastapi import HTTPException
from src.models import Person, PersonCreate, Todo
from src.config import logger


def create_person(session: Session, person: PersonCreate) -> Person:
    """Creates a new person."""
    # Check if exists
    existing = session.exec(select(Person).where(Person.name == person.name)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Person already exists")

    db_person = Person.model_validate(person)
    session.add(db_person)
    session.commit()
    session.refresh(db_person)
    logger.info(f"Created person: {db_person.name}")
    return db_person


def get_persons(session: Session) -> List[Person]:
    """Retrieves all persons."""
    return list(session.exec(select(Person).order_by(Person.name)).all())


def delete_person(session: Session, person_id: str) -> None:
    """Deletes a person if they have no todos."""
    # person_id comes as UUID from api_client, or str from somewhere else.
    # If it's already UUID, use it. If str, convert.
    if isinstance(person_id, uuid.UUID):
        pid = person_id
    else:
        try:
            pid = uuid.UUID(str(person_id))
        except ValueError:
            raise HTTPException(status_code=404, detail="Person not found")

    person = session.get(Person, pid)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    # Check for associated todos
    existing_todos = session.exec(
        select(Todo).where(Todo.person_id == person.id)
    ).first()
    if existing_todos:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete person with assigned todos. Please reassign or delete the todos first.",
        )

    session.delete(person)
    session.commit()
