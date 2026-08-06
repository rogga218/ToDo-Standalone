import json
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlmodel import Session

from src.database import get_session
from src.services.export_service import ExportService

router = APIRouter(prefix="/api/backup", tags=["backup"])


@router.get("/export")
def export_backup(
    format: str = Query(default="json", pattern="^(json|csv)$"),
    session: Session = Depends(get_session),
) -> Response:
    """Export database items as downloadable JSON or CSV file."""
    if format == "json":
        data = ExportService.export_data_json(session)
        content = json.dumps(data, indent=2, ensure_ascii=False)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="todo_backup.json"'},
        )
    elif format == "csv":
        content = ExportService.export_data_csv(session)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="todo_backup.csv"'},
        )

    raise HTTPException(status_code=400, detail="Invalid format specified")


@router.post("/import")
async def import_backup(
    file: UploadFile,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """Import backup file (JSON or CSV) into database."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    raw_bytes = await file.read()
    filename_lower = file.filename.lower()

    try:
        if filename_lower.endswith(".json"):
            data = json.loads(raw_bytes.decode("utf-8"))
            return ExportService.import_data_json(session, data)
        elif filename_lower.endswith(".csv"):
            text = raw_bytes.decode("utf-8")
            return ExportService.import_data_csv(session, text)
        else:
            # Try parsing as JSON first, fallback to CSV
            try:
                data = json.loads(raw_bytes.decode("utf-8"))
                return ExportService.import_data_json(session, data)
            except Exception:
                text = raw_bytes.decode("utf-8")
                return ExportService.import_data_csv(session, text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")
