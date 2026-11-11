import json
import uuid

from fastapi import HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from src.config import get_settings
from src.models import Subtask, Todo


def generate_subtasks(session: Session, todo_id: uuid.UUID) -> Todo:
    settings = get_settings()
    api_key = settings.GEMINI_API_KEY
    if not api_key or api_key in ("XXXX", "your_key_here"):
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    todo = session.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    # Call Gemini
    try:
        from typing import Any

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        prompt = f"""
        Break down the following task into 3-5 concrete subtasks. Match the language of the task title and description.
        Task / Uppgift: {todo.title}
        Description / Beskrivning: {todo.description}

        Return ONLY a valid JSON array of strings. Example: ["Subtask 1", "Subtask 2"]
        """

        call_kwargs: dict[str, Any] = {
            "model": settings.GEMINI_MODEL,
            "contents": prompt,
        }

        # Configure thinking effort / budget if set
        thinking_level = settings.GEMINI_THINKING_LEVEL
        thinking_budget = settings.GEMINI_THINKING_BUDGET
        if isinstance(thinking_level, str) or isinstance(thinking_budget, int):
            thinking_kwargs: dict[str, Any] = {}
            if isinstance(thinking_level, str):
                thinking_kwargs["thinking_level"] = thinking_level
            if isinstance(thinking_budget, int):
                thinking_kwargs["thinking_budget"] = thinking_budget
            call_kwargs["config"] = types.GenerateContentConfig(thinking_config=types.ThinkingConfig(**thinking_kwargs))

        response = client.models.generate_content(**call_kwargs)

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
            select(Todo).where(Todo.id == todo_id).options(selectinload(Todo.subtasks))  # type: ignore[arg-type]
        )
        todo = session.exec(query).first()
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found after update")
        return todo

    except Exception as e:
        print(f"AI Error: {e}")
        raise HTTPException(status_code=500, detail=f"AI Generation Failed: {str(e)}")
