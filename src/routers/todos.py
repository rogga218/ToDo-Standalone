import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session

from src.database import get_session
from src.models import (
    SubtaskCreate,
    SubtaskRead,
    TodoCreate,
    TodoRead,
    TodoUpdate,
)
from src.services import todo_service

router = APIRouter(tags=["Todos"])


# --- Todo Endpoints ---


@router.post(
    "/todos/",
    response_model=TodoRead,
    responses={
        404: {
            "description": "Person not found",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"detail": {"type": "string"}},
                    }
                }
            },
        },
        400: {"description": "Bad Request"},
    },
)
def create_todo(todo: TodoCreate, session: Session = Depends(get_session)):
    """Skapa en ny uppgift (ID genereras automatiskt)"""
    return todo_service.create_todo(session, todo)


@router.get(
    "/todos/",
    response_model=List[TodoRead],
    responses={404: {"description": "Not Found"}},
)
def read_todos(
    request: Request,
    offset: int = Query(default=0, ge=0, le=1000000),
    limit: int = Query(default=1000, le=1000, ge=0),
    session: Session = Depends(get_session),
):
    """Hämta alla uppgifter"""
    allowed_params = {"offset", "limit"}
    extra_params = [key for key in request.query_params.keys() if key not in allowed_params]

    if extra_params:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["query", key],
                    "msg": "Unknown query parameter",
                    "type": "value_error.extra",
                }
                for key in extra_params
            ],
        )

    return todo_service.get_todos(session, offset, limit)


@router.get(
    "/todos/{todo_id:uuid}",
    response_model=TodoRead,
    responses={404: {"description": "Todo not found"}},
)
def read_todo(todo_id: uuid.UUID, session: Session = Depends(get_session)):
    """Hämta en specifik uppgift baserat på UUID"""
    todo = todo_service.get_todo(session, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.patch(
    "/todos/{todo_id:uuid}",
    response_model=TodoRead,
    responses={
        201: {"description": "Todo updated"},
        404: {"description": "Todo not found"},
        400: {"description": "Bad Request"},
    },
)
def update_todo(todo_id: uuid.UUID, todo_data: TodoUpdate, session: Session = Depends(get_session)):
    """Uppdatera en uppgift (partiell uppdatering)"""
    return todo_service.update_todo(session, todo_id, todo_data)


@router.delete("/todos/{todo_id:uuid}", responses={404: {"description": "Todo not found"}})
def delete_todo(todo_id: uuid.UUID, session: Session = Depends(get_session)):
    """Ta bort en uppgift"""
    todo_service.delete_todo(session, todo_id)
    return {"ok": True}


# --- Subtask Endpoints ---


@router.post(
    "/subtasks/",
    response_model=SubtaskRead,
    responses={
        404: {"description": "Todo not found"},
        400: {"description": "Bad Request"},
    },
)
def create_subtask(subtask: SubtaskCreate, session: Session = Depends(get_session)):
    return todo_service.create_subtask(session, subtask)


@router.patch(
    "/subtasks/{subtask_id}",
    response_model=SubtaskRead,
    responses={
        404: {"description": "Subtask not found"},
        400: {"description": "Bad Request"},
    },
)
def update_subtask(subtask_id: uuid.UUID, completed: bool, session: Session = Depends(get_session)):
    return todo_service.update_subtask(session, subtask_id, completed)


@router.delete("/subtasks/{subtask_id}", responses={404: {"description": "Subtask not found"}})
def delete_subtask(subtask_id: uuid.UUID, session: Session = Depends(get_session)):
    todo_service.delete_subtask(session, subtask_id)
    return {"ok": True}
