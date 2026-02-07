from nicegui import ui
from typing import Callable, List, Dict, Optional
from src.ui.api_client import api


from src.ui.translations import get_text


class PersonDialog:
    def __init__(self, persons: List[Dict], on_success: Callable, language: str = "sv"):
        self.persons = persons
        self.on_success = on_success
        self.language = language

    def t(self, key):
        return get_text(key, self.language)

    def open(self):
        with ui.dialog() as dialog, ui.card().classes("min-w-[300px]"):
            ui.label(self.t("dialog_new_person")).classes("text-xl font-bold")
            name_input = ui.input(self.t("name_label")).classes("w-full")

            ui.label(self.t("existing_persons")).classes("text-sm text-gray-400")
            with ui.scroll_area().classes(
                "h-32 w-full border border-gray-700 rounded p-2"
            ):
                for p in self.persons:
                    ui.label(p["name"]).classes("text-sm")

            async def save():
                if not name_input.value:
                    ui.notify(self.t("name_required"), type="negative")
                    return
                res = await api.create_person(name_input.value)
                if res["success"]:
                    ui.notify(self.t("person_created"))
                    dialog.close()
                    await self.on_success()
                else:
                    ui.notify(res["error"], type="negative")

            ui.button(self.t("save"), on_click=save).classes("w-full bg-green-600")
        dialog.open()


class TodoDialog:
    def __init__(self, persons: List[Dict], on_success: Callable, language: str = "sv"):
        self.persons = persons
        self.on_success = on_success
        self.language = language

    def t(self, key):
        return get_text(key, self.language)

    def create(self):
        self._render_dialog(self.t("dialog_new_todo"))

    def edit(self, todo: Dict):
        self._render_dialog(self.t("dialog_edit_todo"), todo)

    def _render_dialog(self, title_text: str, todo: Optional[Dict] = None):
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label(title_text).classes("text-xl font-bold")

            initial_title = todo["title"] if todo else ""
            initial_desc = todo.get("description", "") if todo else ""
            initial_person = todo.get("person_id") if todo else None
            initial_prio = todo.get("priority", 2) if todo else 2
            initial_deadline = todo.get("deadline") if todo else None

            title_input = ui.input(self.t("title_label"), value=initial_title).classes(
                "w-full"
            )
            desc_input = ui.textarea(self.t("desc_label"), value=initial_desc).classes(
                "w-full"
            )

            # Person Select
            p_options = {p["id"]: p["name"] for p in self.persons}
            # Ensure safe value if person deleted or invalid?
            if initial_person and initial_person not in p_options:
                initial_person = None

            person_select = ui.select(
                p_options, label=self.t("person_label"), value=initial_person
            ).classes("w-full")

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
                value=initial_deadline,
            ).classes("w-full")
            with deadline_input.add_slot("append"):
                ui.icon("event").on("click", lambda: date_picker.open()).classes(
                    "cursor-pointer"
                )

            with ui.dialog() as date_picker, ui.card():
                ui.date(
                    on_change=lambda e: (
                        deadline_input.set_value(e.value),
                        date_picker.close(),
                    )
                )

            async def save():
                if not title_input.value or not person_select.value:
                    ui.notify(self.t("title_person_required"), type="negative")
                    return

                payload = {
                    "title": title_input.value,
                    "description": desc_input.value,
                    "person_id": person_select.value,
                    "priority": priority_select.value,
                    "deadline": deadline_input.value or None,
                }

                if todo:
                    # Update
                    full_payload = todo.copy()
                    full_payload.update(payload)
                    res = await api.update_todo(full_payload)
                else:
                    # Create
                    payload["completed"] = False
                    res = await api.create_todo(payload)

                if res["success"]:
                    msg = self.t("updated") if todo else self.t("task_created")
                    ui.notify(msg, type="positive")
                    dialog.close()
                    await self.on_success()
                else:
                    ui.notify(res["error"], type="negative")

            ui.button(self.t("save"), on_click=save).classes("w-full bg-indigo-600")
        dialog.open()
