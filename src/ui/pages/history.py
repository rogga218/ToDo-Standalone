from nicegui import ui
from typing import List, Callable, Optional
from src.models import Person, TodoRead

from src.ui.translations import get_text


class HistoryView:
    def __init__(
        self,
        todos: List[TodoRead],
        persons: List[Person],
        on_delete: Callable,
        on_restore: Callable,
        on_bulk_delete: Optional[Callable] = None,
        language: str = "sv",
    ):
        self.todos = todos
        self.persons = persons
        self.on_delete = on_delete
        self.on_restore = on_restore
        self.on_bulk_delete = on_bulk_delete
        self.language = language

    def t(self, key):
        return get_text(key, self.language)

    def render(self):
        # Filter completed
        completed_todos = [t for t in self.todos if t.completed]

        # Prepare Rows
        rows = []
        for t in completed_todos:
            # Use p.id and p.name
            person_name = next(
                (p.name for p in self.persons if str(p.id) == str(t.person_id)), "?"
            )
            rows.append(
                {
                    "id": str(t.id),
                    "title": t.title,
                    "description": t.description or "",
                    "person": person_name,
                    "deadline": str(t.deadline) if t.deadline else "",
                    "priority": t.priority,
                    "_raw": t.model_dump(),  # Keep full object (as dict) for actions
                }
            )

        # Columns
        columns = [
            {
                "name": "title",
                "label": self.t("title_label"),
                "field": "title",
                "sortable": True,
                "align": "left",
            },
            {
                "name": "person",
                "label": self.t("person_label"),
                "field": "person",
                "sortable": True,
                "align": "left",
            },
            {
                "name": "description",
                "label": self.t("description_label"),
                "field": "description",
                "sortable": True,
                "align": "left",
            },
            {
                "name": "deadline",
                "label": self.t("deadline_label"),
                "field": "deadline",
                "sortable": True,
                "align": "left",
            },
            {
                "name": "priority",
                "label": self.t("priority_label"),
                "field": "priority",
                "sortable": True,
                "align": "center",
            },
            {
                "name": "actions",
                "label": "",
                "field": "actions",
                "align": "center",
            },
        ]

        # Main Container with Scroll
        # Full width as requested: removed max-w-6xl and mx-auto
        with ui.column().classes("w-full h-full p-4 overflow-y-auto"):
            # Header Row
            with ui.row().classes("w-full justify-between items-center mb-4"):
                ui.label(self.t("history")).classes(
                    "text-2xl font-bold !text-black dark:!text-white"
                )
                # Placeholder for Bulk Action Button (will be moved here)
                bulk_action_container = ui.row()

            if not rows:
                ui.label(self.t("no_completed_tasks")).classes(
                    "text-gray-600 dark:text-gray-400 italic"
                )
                return

            # Table
            # "Native" styling: rely on NiceGUI/Quasar to handle dark mode via ui.dark_mode()
            # Pagination: rowsPerPage 0 means "All" (infinite scroll)
            table = (
                ui.table(
                    columns=columns,
                    rows=rows,
                    selection="multiple",
                    row_key="id",
                    pagination={"rowsPerPage": 0},
                )
                .classes("w-full")
                .props("flat bordered")
            )

            # Register event listeners
            def restore_row(e):
                row_id = e.args
                # t.id is UUID, row_id is string from table
                todo = next((t for t in self.todos if str(t.id) == str(row_id)), None)
                if todo:
                    self.on_restore(todo)

            def delete_row(e):
                row_id = e.args
                todo = next((t for t in self.todos if str(t.id) == str(row_id)), None)
                if todo:
                    self.on_delete(todo)

            table.on("restore", restore_row)
            table.on("delete", delete_row)

            # Bulk Actions Logic
            async def delete_selected():
                selected_rows = table.selected
                if not selected_rows:
                    return

                ids = {str(r["id"]) for r in selected_rows}  # r is dict from table row
                to_delete = [t for t in self.todos if str(t.id) in ids]

                if self.on_bulk_delete:
                    await self.on_bulk_delete(to_delete)
                else:
                    for t in to_delete:
                        await self.on_delete(t)

            # Create Button and Move to Header
            with bulk_action_container:
                ui.button(
                    self.t("delete"), icon="delete", on_click=delete_selected
                ).props("color=red").bind_visibility_from(
                    table, "selected", backward=lambda s: len(s) > 0
                )

            # Slots for Actions Column
            with table.add_slot("body-cell-actions"):
                # Using ui.row to ensure buttons are side-by-side
                with ui.row().classes("items-center justify-center no-wrap gap-1"):
                    ui.button(icon="restore").props(
                        "flat dense round color=primary"
                    ).on("click", js_handler="() => $emit('restore', props.row.id)")
                    ui.button(icon="delete").props(
                        "flat dense round color=negative"
                    ).on("click", js_handler="() => $emit('delete', props.row.id)")
