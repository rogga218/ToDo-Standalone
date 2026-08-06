import uuid
from typing import Any, Dict, List

from nicegui import run
from pydantic import ValidationError
from sqlmodel import Session

from src.config import logger
from src.database import engine
from src.models import Person, PersonCreate, TodoCreate, TodoRead, TodoUpdate
from src.services import ai_service, person_service, todo_service


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

            def _fetch(session):
                todos = todo_service.get_todos(session)
                return [TodoRead.model_validate(t) for t in todos]

            return await run_db(_fetch)  # type: ignore[no-any-return]
        except Exception as e:
            logger.error(f"Error fetching todos: {e}", exc_info=True)
            return []

    async def get_persons(self) -> List[Person]:
        try:
            persons = await run_db(person_service.get_persons)
            return persons  # type: ignore[no-any-return]
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

    async def update_todo(self, todo_id: str, update_data: TodoUpdate) -> Dict[str, Any]:
        try:
            tid = uuid.UUID(str(todo_id))
            await run_db(todo_service.update_todo, tid, update_data)
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

    async def export_backup(self, format: str = "json") -> Dict[str, Any]:
        try:
            import json

            from src.services.export_service import ExportService

            if format == "json":
                data = await run_db(ExportService.export_data_json)
                content = json.dumps(data, indent=2, ensure_ascii=False)
                return {"success": True, "content": content, "filename": "todo_backup.json"}
            else:
                content = await run_db(ExportService.export_data_csv)
                return {"success": True, "content": content, "filename": "todo_backup.csv"}
        except Exception as e:
            logger.error(f"Error exporting backup: {e}", exc_info=True)
            return {"success": False, "error": _format_error(e)}

    async def import_backup(self, content_bytes: bytes, filename: str) -> Dict[str, Any]:
        try:
            import json

            from src.services.export_service import ExportService

            filename_lower = filename.lower()
            if filename_lower.endswith(".json"):
                data = json.loads(content_bytes.decode("utf-8"))
                res = await run_db(ExportService.import_data_json, data)
            elif filename_lower.endswith(".csv"):
                text = content_bytes.decode("utf-8")
                res = await run_db(ExportService.import_data_csv, text)
            else:
                try:
                    data = json.loads(content_bytes.decode("utf-8"))
                    res = await run_db(ExportService.import_data_json, data)
                except Exception:
                    text = content_bytes.decode("utf-8")
                    res = await run_db(ExportService.import_data_csv, text)
            return res  # type: ignore[no-any-return]
        except Exception as e:
            logger.error(f"Error importing backup: {e}", exc_info=True)
            return {"success": False, "error": _format_error(e)}


# Singleton instance
api = ApiClient()
