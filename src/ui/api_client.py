import uuid
from typing import List, Dict, Any
from nicegui import run
from sqlmodel import Session
from src.database import engine
from src.models import PersonCreate, TodoCreate, TodoUpdate, Person, TodoRead
from src.services import person_service, todo_service, ai_service
from pydantic import ValidationError
from src.config import logger


def _format_error(e: Exception) -> str:
    if isinstance(e, ValidationError):
        # Extract the human-readable messages from Pydantic
        return "\n".join([err.get("msg", str(err)) for err in e.errors()])
    if hasattr(e, "detail"):
        return str(e.detail)
    return str(e)


# Helper to run sync DB function in threadpool and manage session
async def run_db(func, *args, **kwargs):
    def wrapper():
        with Session(engine) as session:
            return func(session, *args, **kwargs)

    return await run.io_bound(wrapper)


class ApiClient:
    async def get_todos(self) -> List[TodoRead]:
        try:
            todos = await run_db(todo_service.get_todos)
            return [TodoRead.model_validate(t) for t in todos]
        except Exception as e:
            logger.error(f"Error fetching todos: {e}", exc_info=True)
            return []

    async def get_persons(self) -> List[Person]:
        try:
            persons = await run_db(person_service.get_persons)
            return persons
        except Exception as e:
            logger.error(f"Error fetching persons: {e}", exc_info=True)
            return []

    async def create_person(self, name: str) -> Dict[str, Any]:
        try:
            res = await run_db(person_service.create_person, PersonCreate(name=name))
            return {"success": True, "data": res.model_dump()}
        except Exception as e:
            logger.error(f"Error creating person: {e}", exc_info=True)
            err_msg = _format_error(e)
            return {"success": False, "error": err_msg}

    async def delete_person(self, person_id: str) -> Dict[str, Any]:
        try:
            pid = uuid.UUID(str(person_id))
            await run_db(person_service.delete_person, pid)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error deleting person: {e}", exc_info=True)
            err_msg = _format_error(e)
            return {"success": False, "error": err_msg}

    async def create_todo(self, todo: Dict[str, Any]) -> Dict[str, Any]:
        try:
            t_create = TodoCreate(**todo)
            await run_db(todo_service.create_todo, t_create)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error creating todo: {e}", exc_info=True)
            err_msg = _format_error(e)
            return {"success": False, "error": err_msg}

    async def delete_todo(self, todo_id: str) -> Dict[str, Any]:
        try:
            tid = uuid.UUID(str(todo_id))
            await run_db(todo_service.delete_todo, tid)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error deleting todo: {e}", exc_info=True)
            err_msg = _format_error(e)
            return {"success": False, "error": err_msg}

    async def update_todo(self, todo: Dict[str, Any]) -> Dict[str, Any]:
        try:
            tid = uuid.UUID(str(todo["id"]))
            allowed_fields = {
                "title",
                "description",
                "completed",
                "priority",
                "deadline",
                "person_id",
            }
            filtered_data = {k: v for k, v in todo.items() if k in allowed_fields}
            t_update = TodoUpdate(**filtered_data)
            await run_db(todo_service.update_todo, tid, t_update)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error updating todo: {e}", exc_info=True)
            err_msg = _format_error(e)
            return {"success": False, "error": err_msg}

    async def generate_subtasks(self, todo_id: str) -> Dict[str, Any]:
        try:
            tid = uuid.UUID(str(todo_id))
            res = await run_db(ai_service.generate_subtasks, tid)
            return {"success": True, "data": res.model_dump()}
        except Exception as e:
            logger.error(f"Error generating subtasks: {e}", exc_info=True)
            err_msg = _format_error(e)
            return {"success": False, "error": err_msg}

    async def toggle_subtask(self, subtask_id: str, completed: bool) -> Dict[str, Any]:
        try:
            sid = uuid.UUID(str(subtask_id))
            await run_db(todo_service.update_subtask, sid, completed)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error toggling subtask: {e}", exc_info=True)
            err_msg = _format_error(e)
            return {"success": False, "error": err_msg}

    async def delete_subtask(self, subtask_id: str) -> Dict[str, Any]:
        try:
            sid = uuid.UUID(str(subtask_id))
            await run_db(todo_service.delete_subtask, sid)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error deleting subtask: {e}", exc_info=True)
            err_msg = getattr(e, "detail", str(e))
            return {"success": False, "error": err_msg}


# Singleton instance
api = ApiClient()
