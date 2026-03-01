from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session

from src.config import logger
from src.database import get_session
from src.models import PersonCreate, PersonRead
from src.services import person_service

router = APIRouter(prefix="/persons", tags=["Persons"])


@router.post(
    "/",
    response_model=PersonRead,
    responses={
        409: {"description": "Person already exists"},
        400: {"description": "Bad Request"},
        404: {"description": "Not Found"},
    },
)
def create_person(person: PersonCreate, session: Session = Depends(get_session)):
    """Lägg till en ny person"""
    try:
        return person_service.create_person(session, person)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating person: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[PersonRead])
def read_persons(request: Request, session: Session = Depends(get_session)):
    """Hämta alla personer"""
    if request.query_params:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["query", key],
                    "msg": "Unknown query parameter",
                    "type": "value_error.extra",
                }
                for key in request.query_params.keys()
            ],
        )
    return person_service.get_persons(session)


@router.delete(
    "/{person_id}",
    status_code=204,
    responses={
        404: {"description": "Person not found"},
        400: {"description": "Person has assigned todos"},
    },
)
def delete_person(person_id: str, session: Session = Depends(get_session)):
    """Ta bort en person (om den inte har några uppgifter)"""
    try:
        person_service.delete_person(session, person_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting person: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
