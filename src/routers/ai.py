import uuid

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.database import get_session
from src.models import TodoRead
from src.services import ai_service

router = APIRouter(tags=["AI"])


@router.post(
    "/todos/{todo_id}/generate-subtasks",
    response_model=TodoRead,
    responses={404: {"description": "Todo not found"}},
)
def generate_subtasks_ai(
    todo_id: uuid.UUID,
    session: Session = Depends(get_session),
):
    return ai_service.generate_subtasks(session, todo_id)
