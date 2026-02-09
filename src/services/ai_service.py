import uuid
import json
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from src.models import Todo, Subtask
from src.config import get_settings


def generate_subtasks(session: Session, todo_id: uuid.UUID) -> Todo:
    settings = get_settings()
    api_key = settings.GEMINI_API_KEY
    if not api_key or api_key == "XXXX":
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    # Call Gemini
    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""
        Bryt ner följande uppgift i 3-5 konkreta deluppgifter på Svenska.
        Uppgift: {todo.title}
        Beskrivning: {todo.description}
        
        Returnera ENDAST en giltig JSON-array av strängar. Exempel: ["Köpa färg", "Måla vägg"]
        """,
        )

        # SDK 2.0 response parsing might differ
        response_text = response.text
        if not response_text:
            raise ValueError("Empty response from AI")

        # Clean up markdown code blocks if present (Gemini loves ```json)
        if "```" in response_text:
            response_text = response_text.replace("```json", "").replace("```", "")

        subtasks_titles = json.loads(response_text)

        # Filter and create subtasks
        for title in subtasks_titles:
            clean_title = title.strip()
            if clean_title:
                subtask = Subtask(title=clean_title, todo_id=todo.id)
                session.add(subtask)

        session.commit()

        # Refresh with subtasks loaded
        query = (
            # type: ignore[arg-type]
            select(Todo).where(Todo.id == todo_id).options(selectinload(Todo.subtasks))
        )
        todo = session.exec(query).first()
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found after update")
        return todo

    except Exception as e:
        print(f"AI Error: {e}")
        raise HTTPException(status_code=500, detail=f"AI Generation Failed: {str(e)}")
