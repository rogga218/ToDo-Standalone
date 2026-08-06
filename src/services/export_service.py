import csv
import io
from datetime import date, datetime, timezone
from typing import Any, Dict

from sqlmodel import Session, select

from src.models import Person, Subtask, Todo
from src.services import person_service, todo_service


class ExportService:
    @staticmethod
    def export_data_json(session: Session) -> Dict[str, Any]:
        """Export all Persons, ToDos, and Subtasks to a JSON-serializable dictionary."""
        persons = session.exec(select(Person)).all()
        todos = todo_service.get_todos(session)

        persons_data = [{"id": str(p.id), "name": p.name} for p in persons]

        todos_data = []
        for t in todos:
            subtasks_data = [
                {
                    "id": str(s.id),
                    "title": s.title,
                    "completed": s.completed,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
                for s in t.subtasks
            ]
            todos_data.append(
                {
                    "id": str(t.id),
                    "title": t.title,
                    "description": t.description,
                    "completed": t.completed,
                    "priority": t.priority,
                    "deadline": t.deadline.isoformat() if isinstance(t.deadline, date) else str(t.deadline),
                    "person_id": str(t.person_id),
                    "subtasks": subtasks_data,
                }
            )

        return {
            "version": 1,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "persons": persons_data,
            "todos": todos_data,
        }

    @staticmethod
    def export_data_csv(session: Session) -> str:
        """Export all ToDos and Subtasks to a CSV formatted string."""
        persons = person_service.get_persons(session)
        person_map = {str(p.id): p.name for p in persons}
        todos = todo_service.get_todos(session)

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["Title", "Description", "Person", "Priority", "Deadline", "Completed", "Subtasks"])

        for t in todos:
            person_name = person_map.get(str(t.person_id), "")
            subtasks_str = "; ".join(f"[{'X' if s.completed else ' '}] {s.title}" for s in t.subtasks)
            deadline_str = t.deadline.isoformat() if isinstance(t.deadline, date) else str(t.deadline)

            writer.writerow(
                [
                    t.title,
                    t.description or "",
                    person_name,
                    t.priority,
                    deadline_str,
                    "Yes" if t.completed else "No",
                    subtasks_str,
                ]
            )

        return output.getvalue()

    @staticmethod
    def import_data_json(session: Session, data: Dict[str, Any]) -> Dict[str, Any]:
        """Import Persons, ToDos, and Subtasks from JSON dictionary into session."""
        if not isinstance(data, dict) or "todos" not in data:
            raise ValueError("Invalid JSON backup structure: missing 'todos'")

        existing_persons = person_service.get_persons(session)
        person_name_map = {p.name.lower(): p for p in existing_persons}
        person_id_map = {str(p.id): p for p in existing_persons}

        imported_persons_count = 0
        imported_todos_count = 0

        # 1. Process Persons in payload
        for p_data in data.get("persons", []):
            name = (p_data.get("name") or "").strip()
            p_id_str = str(p_data.get("id", ""))
            if not name:
                continue

            if name.lower() not in person_name_map:
                new_person = Person(name=name)
                session.add(new_person)
                session.flush()
                session.refresh(new_person)
                person_name_map[name.lower()] = new_person
                person_id_map[str(new_person.id)] = new_person
                if p_id_str:
                    person_id_map[p_id_str] = new_person
                imported_persons_count += 1

        default_person = next(iter(person_name_map.values()), None)

        # 2. Process ToDos in payload
        for t_data in data.get("todos", []):
            try:
                title = (t_data.get("title") or "").strip()
                if not title:
                    continue

                description = (t_data.get("description") or title or "No description").strip()

                # Resolve person
                pid = str(t_data.get("person_id", ""))
                assigned_person = person_id_map.get(pid, default_person)
                if not assigned_person:
                    continue

                deadline_val = t_data.get("deadline")
                d_parsed = date.today()
                if deadline_val:
                    try:
                        d_parsed = date.fromisoformat(str(deadline_val))
                    except ValueError:
                        d_parsed = date.today()

                new_todo = Todo(
                    title=title,
                    description=description,
                    completed=bool(t_data.get("completed", False)),
                    priority=int(t_data.get("priority", 2)),
                    deadline=d_parsed,
                    person_id=assigned_person.id,
                )
                session.add(new_todo)
                session.flush()
                session.refresh(new_todo)

                # Insert subtasks
                for s_data in t_data.get("subtasks", []):
                    s_title = (s_data.get("title") or "").strip()
                    if s_title:
                        new_subtask = Subtask(
                            todo_id=new_todo.id,
                            title=s_title,
                            completed=bool(s_data.get("completed", False)),
                        )
                        session.add(new_subtask)

                imported_todos_count += 1
            except Exception:
                continue

        session.commit()
        return {
            "success": True,
            "imported_todos": imported_todos_count,
            "imported_persons": imported_persons_count,
        }

    @staticmethod
    def import_data_csv(session: Session, csv_content: str) -> Dict[str, Any]:
        """Import ToDos from CSV text string into session."""
        f = io.StringIO(csv_content.strip())
        reader = csv.DictReader(f)

        existing_persons = person_service.get_persons(session)
        person_name_map = {p.name.lower(): p for p in existing_persons}

        imported_persons_count = 0
        imported_todos_count = 0

        default_person = next(iter(person_name_map.values()), None)

        for row in reader:
            try:
                title = (row.get("Title") or row.get("title") or "").strip()
                if not title:
                    continue

                raw_desc = (row.get("Description") or row.get("description") or "").strip()
                description = raw_desc if raw_desc else (title or "No description")

                person_name = (row.get("Person") or row.get("person") or "").strip()

                assigned_person = None
                if person_name:
                    if person_name.lower() in person_name_map:
                        assigned_person = person_name_map[person_name.lower()]
                    else:
                        try:
                            # Clean name to pass Person validation
                            cleaned_name = "".join(c for c in person_name if c.isalpha() or c in " -'").strip()
                            if len(cleaned_name) >= 2:
                                new_person = Person(name=cleaned_name)
                                session.add(new_person)
                                session.flush()
                                session.refresh(new_person)
                                person_name_map[cleaned_name.lower()] = new_person
                                assigned_person = new_person
                                imported_persons_count += 1
                            else:
                                assigned_person = default_person
                        except Exception:
                            assigned_person = default_person

                if not assigned_person:
                    assigned_person = default_person

                if not assigned_person:
                    continue

                deadline_val = row.get("Deadline") or row.get("deadline")
                d_parsed = date.today()
                if deadline_val:
                    try:
                        d_parsed = date.fromisoformat(str(deadline_val).strip())
                    except ValueError:
                        d_parsed = date.today()

                prio_val = 2
                try:
                    prio_val = int(row.get("Priority") or row.get("priority") or 2)
                except ValueError:
                    prio_val = 2

                completed_raw = str(row.get("Completed") or row.get("completed") or "").lower()
                completed_val = completed_raw in ("yes", "true", "1")

                new_todo = Todo(
                    title=title,
                    description=description,
                    completed=completed_val,
                    priority=prio_val,
                    deadline=d_parsed,
                    person_id=assigned_person.id,
                )
                session.add(new_todo)
                session.flush()
                session.refresh(new_todo)

                subtasks_raw = (row.get("Subtasks") or row.get("subtasks") or "").strip()
                if subtasks_raw:
                    for sub_item in subtasks_raw.split(";"):
                        item_str = sub_item.strip()
                        if not item_str:
                            continue
                        sub_completed = item_str.startswith("[X]") or item_str.startswith("[x]")
                        sub_title = item_str.replace("[X]", "").replace("[x]", "").replace("[ ]", "").strip()
                        if sub_title:
                            new_sub = Subtask(
                                todo_id=new_todo.id,
                                title=sub_title,
                                completed=sub_completed,
                            )
                            session.add(new_sub)

                imported_todos_count += 1
            except Exception:
                continue

        session.commit()
        return {
            "success": True,
            "imported_todos": imported_todos_count,
            "imported_persons": imported_persons_count,
        }
