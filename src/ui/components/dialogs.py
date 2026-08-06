from datetime import date, timedelta
from typing import Callable, List, Optional

from nicegui import ui

from src.models import Person, TodoRead, TodoUpdate
from src.ui.api_client import api
from src.ui.translations import get_text


class PersonDialog:
    def __init__(
        self,
        persons: List[Person],
        todos: List[TodoRead],  # Passed to check for assignments
        on_success: Callable,
        language: str = "sv",
    ):
        self.persons = persons
        self.todos = todos
        self.on_success = on_success
        self.language = language

    def t(self, key):
        return get_text(key, self.language)

    def open(self):
        with ui.dialog() as dialog, ui.card().classes("min-w-[400px]"):
            ui.label(self.t("manage_persons")).classes("text-xl font-bold mb-4")

            # 1. Create New Person
            with ui.row().classes("w-full items-center gap-2 mb-4"):
                name_input = ui.input(self.t("name_label"), value="").classes("flex-grow").props("maxlength=50")

                async def create_new():
                    name_input.error = None
                    val = (name_input.value or "").strip()
                    if not val:
                        name_input.error = self.t("name_required")
                        return
                    if len(val) < 2:
                        name_input.error = self.t("name_too_short")
                        return

                    res = await api.create_person(val)
                    if res["success"]:
                        ui.notify(self.t("person_created"), type="positive")
                        name_input.value = ""  # Clear input
                        name_input.error = None
                        await self.refresh_list()  # Refresh Local List
                        await self.on_success()  # Refresh Background App
                    else:
                        err = str(res["error"])
                        if "Value error, " in err:  # Pydantic V2 prefixes custom errors with "Value error, "
                            err = err.replace("Value error, ", "")

                        # Split by newline (if multiple errors) and translate each
                        err = "\n".join(self.t(line.strip()) for line in err.split("\n"))

                        # Fallback for generic untranslated exceptions
                        if "Person already exists" in err:
                            err = self.t("person_exists")

                        name_input.error = err

                ui.button(icon="add", on_click=lambda e: create_new()).props("round flat color=green")

            # 2. List Existing Persons
            ui.label(self.t("existing_persons")).classes("text-sm text-gray-500 font-bold mb-2")

            with ui.scroll_area().classes("h-64 w-full border border-gray-200 dark:border-gray-700 rounded p-2"):
                # Container for the list - Must be created INSIDE the scroll area
                self.list_container = ui.column().classes("w-full")
                with self.list_container:
                    self.render_list_items()

            ui.button(self.t("done"), on_click=dialog.close).classes("w-full mt-4")
        dialog.open()

    async def refresh_list(self):
        # Fetch fresh data
        self.persons = await api.get_persons()
        self.list_container.clear()
        with self.list_container:
            self.render_list_items()

    def render_list_items(self):
        if not self.persons:
            ui.label("...").classes("text-gray-400 italic")

        for p in self.persons:
            has_todos = any(str(t.person_id) == str(p.id) for t in self.todos)

            with ui.row().classes(
                "w-full items-center justify-between mb-1 hover:bg-gray-100 dark:hover:bg-gray-800 p-1 rounded"
            ):
                ui.label(p.name).classes("text-base")

                if has_todos:
                    # Disabled delete button with tooltip
                    ui.button(icon="delete_forever").props("flat round dense color=grey").tooltip(
                        self.t("cannot_delete_has_todos")
                    ).classes("cursor-not-allowed")
                else:

                    def create_delete_handler(person_id):
                        async def delete_handler(*_):
                            res = await api.delete_person(str(person_id))
                            if res["success"]:
                                ui.notify(self.t("person_deleted"), type="positive")
                                await self.refresh_list()
                                await self.on_success()
                            else:
                                ui.notify(res["error"], type="negative")

                        return delete_handler

                    ui.button(
                        icon="delete",
                        on_click=create_delete_handler(p.id),
                    ).props("flat round dense color=red")


class TodoDialog:
    def __init__(self, persons: List[Person], on_success: Callable, language: str = "sv"):
        self.persons = persons
        self.on_success = on_success
        self.language = language

    def t(self, key):
        return get_text(key, self.language)

    def create(self):
        self._render_dialog(self.t("dialog_new_todo"))

    def edit(self, todo: TodoRead):
        self._render_dialog(self.t("dialog_edit_todo"), todo)

    def _render_dialog(self, title_text: str, todo: Optional[TodoRead] = None):
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label(title_text).classes("text-xl font-bold")

            initial_title = todo.title if todo else ""
            initial_desc = todo.description if todo else ""
            initial_person = todo.person_id if todo else None
            initial_prio = todo.priority if todo else 2

            if todo and todo.deadline:
                deadline_str = todo.deadline.isoformat() if isinstance(todo.deadline, date) else str(todo.deadline)
            else:
                # Default to tomorrow
                deadline_str = (date.today() + timedelta(days=1)).isoformat()

            title_input = ui.input(self.t("title_label"), value=initial_title).classes("w-full").props("maxlength=50")
            desc_input = ui.textarea(self.t("desc_label"), value=initial_desc).classes("w-full").props("maxlength=500")

            p_options = {p.id: p.name for p in self.persons}
            if initial_person and initial_person not in p_options:
                initial_person = None

            person_select = ui.select(p_options, label=self.t("person_label"), value=initial_person).classes("w-full")

            priority_select = ui.select(
                {
                    1: f"{self.t('high')} (1)",
                    2: f"{self.t('medium')} (2)",
                    3: f"{self.t('low')} (3)",
                },
                label=self.t("priority_label"),
                value=initial_prio,
            ).classes("w-full")

            deadline_input = ui.input(
                self.t("deadline_label"),
                placeholder="YYYY-MM-DD",
                value=deadline_str,
            ).classes("w-full")
            with ui.dialog() as date_picker, ui.card():

                def on_date_change(e):
                    deadline_input.set_value(e.value)
                    deadline_input.error = None
                    date_picker.close()

                ui.date(on_change=on_date_change)

            with deadline_input.add_slot("append"):
                ui.icon("event").on("click", date_picker.open).classes("cursor-pointer")

            async def save():
                title_input.error = None
                desc_input.error = None
                person_select.error = None
                deadline_input.error = None

                has_error = False
                if not (title_input.value or "").strip():
                    title_input.error = self.t("title_required")
                    has_error = True

                if not person_select.value:
                    person_select.error = self.t("person_required")
                    has_error = True

                desc_val = (desc_input.value or "").strip()
                if not desc_val:
                    desc_input.error = self.t("desc_required")
                    has_error = True

                d_parsed = None
                if deadline_input.value:
                    try:
                        d_parsed = date.fromisoformat(deadline_input.value)
                    except ValueError:
                        deadline_input.error = self.t("invalid_date_format")
                        has_error = True

                if has_error:
                    return

                if todo:
                    update_data = TodoUpdate(
                        title=title_input.value,
                        description=desc_input.value,
                        person_id=person_select.value,
                        priority=priority_select.value,
                        deadline=d_parsed,
                    )
                    res = await api.update_todo(str(todo.id), update_data)
                else:
                    payload = {
                        "title": title_input.value,
                        "description": desc_input.value,
                        "person_id": person_select.value,
                        "priority": priority_select.value,
                        "deadline": d_parsed or date.today(),
                        "completed": False,
                    }
                    res = await api.create_todo(payload)

                if res["success"]:
                    msg = self.t("updated") if todo else self.t("task_created")
                    ui.notify(msg, type="positive")
                    dialog.close()
                    await self.on_success()
                else:
                    err = str(res["error"])
                    if "title" in err.lower():
                        title_input.error = err
                    elif "description" in err.lower():
                        desc_input.error = err
                    elif "deadline" in err.lower():
                        deadline_input.error = err
                    else:
                        ui.notify(err, type="negative")

            ui.button(self.t("save"), on_click=save).classes("w-full bg-indigo-600")
        dialog.open()
