from nicegui import ui
from typing import List, Dict, Callable


from src.ui.translations import get_text


class HistoryView:
    def __init__(
        self,
        todos: List[Dict],
        persons: List[Dict],
        on_delete: Callable,
        on_restore: Callable,
        on_bulk_delete: Callable = None,
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

    def toggle_select_all(self, *args):
        # ... logic unchanged ...
        completed_todos = [t for t in self.todos if t["completed"]]
        all_ids = {t["id"] for t in completed_todos}
        if self.selected_ids.issuperset(all_ids):
            self.selected_ids.clear()
        else:
            self.selected_ids.update(all_ids)
        self.refresh_ui()

    def render(self):
        # Filter completed
        completed_todos = [t for t in self.todos if t["completed"]]

        # Sort by deadline desc
        completed_todos.sort(key=lambda x: x.get("deadline") or "", reverse=True)

        # Selection state (using a set of IDs)
        if not hasattr(self, "selected_ids"):
            self.selected_ids = set()

        # We actually need to pass toggle_select_all to render_content
        with ui.column().classes("w-full p-8 max-w-4xl mx-auto") as container:
            self.container = container  # store for refresh
            self.render_content(
                completed_todos,
                self.toggle_selection,
                self.delete_selected,
                self.toggle_select_all,
            )

    def refresh_ui(self):
        self.container.clear()
        # Re-fetch or re-filter? locally re-filter
        completed_todos = [t for t in self.todos if t["completed"]]
        completed_todos.sort(key=lambda x: x.get("deadline") or "", reverse=True)

        with self.container:
            self.render_content(
                completed_todos,
                lambda tid: self.toggle_selection(tid),
                self.delete_selected,
                self.toggle_select_all,
            )

    def toggle_selection(self, todo_id):
        if todo_id in self.selected_ids:
            self.selected_ids.remove(todo_id)
        else:
            self.selected_ids.add(todo_id)
        self.refresh_ui()

    async def delete_selected(self, *args):
        to_delete = [t for t in self.todos if t["id"] in self.selected_ids]

        if self.on_bulk_delete:
            await self.on_bulk_delete(to_delete)
        else:
            for t in to_delete:
                await self.on_delete(t)

        self.selected_ids.clear()

    def render_content(self, completed_todos, toggle_fn, delete_fn, toggle_all_fn):
        ui.label(self.t("history_header")).classes(
            "text-3xl font-bold text-black dark:text-white mb-8"
        )

        if not completed_todos:
            ui.label(self.t("no_completed_tasks")).classes(
                "text-gray-600 dark:text-gray-400 italic"
            )
            return

        with ui.row().classes("w-full items-center justify-between mb-4"):
            ui.button(
                self.t("select_all"), icon="select_all", on_click=toggle_all_fn
            ).props("flat color=blue")

            # Bulk Actions
            if self.selected_ids:
                with ui.row().classes(
                    "items-center bg-gray-200 dark:bg-slate-800 p-2 rounded"
                ):
                    ui.label(f"{len(self.selected_ids)} {self.t('selected')}").classes(
                        "text-black dark:text-white font-bold mr-4"
                    )
                    ui.button(
                        f"{self.t('delete')} ({len(self.selected_ids)})",
                        icon="delete",
                        on_click=delete_fn,
                    ).props("flat color=red")

        # List
        for todo in completed_todos:
            is_selected = todo["id"] in self.selected_ids
            # Styles
            # Remove bg-white (default). Keep dark overrides.
            base_bg = "dark:bg-slate-800"
            selected_bg = "bg-blue-50 dark:bg-slate-700"

            card_class = f"w-full {base_bg} border-l-4 border-green-500 mb-2 p-4"
            if is_selected:
                card_class = f"w-full {selected_bg} border-l-4 border-red-500 mb-2 p-4"

            with ui.card().classes(card_class):
                with ui.row().classes("w-full items-center gap-4"):
                    # Checkbox
                    ui.checkbox(
                        value=is_selected,
                        on_change=lambda e, tid=todo["id"]: toggle_fn(tid),
                    )

                    # Content (Flexible)
                    with ui.column().classes("gap-1 flex-1"):
                        ui.label(todo["title"]).classes(
                            "text-lg font-bold line-through decoration-gray-500"
                        )
                        if todo.get("description"):
                            ui.label(todo.get("description")).classes(
                                "text-sm opacity-70"
                            )

                        person_name = next(
                            (
                                p["name"]
                                for p in self.persons
                                if p["id"] == todo["person_id"]
                            ),
                            "?",
                        )
                        ui.label(
                            f"{self.t('completed_by')}: {person_name} | {self.t('deadline_label')}: {todo.get('deadline')}"
                        ).classes("text-xs opacity-60")

                    # Individual Actions
                    with ui.row().classes("gap-2"):
                        ui.button(
                            icon="undo",
                            on_click=lambda t=todo: self.on_restore(t),
                        ).props("flat dense round").classes(
                            "text-gray-600 dark:text-white"
                        ).tooltip(self.t("restore"))
                        ui.button(
                            icon="delete",
                            on_click=lambda t=todo: self.on_delete(t),
                        ).props("flat dense round").classes(
                            "text-red-600 dark:text-red-400"
                        ).tooltip(self.t("delete"))
