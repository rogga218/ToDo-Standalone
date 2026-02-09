import asyncio
from typing import List
from nicegui import ui, app

from src.models import Person, TodoRead
from src.ui.api_client import api
from src.ui.components.dialogs import PersonDialog, TodoDialog
from src.ui.pages.board import BoardView
from src.ui.pages.history import HistoryView
from src.ui.layout import Layout


class ToDoController:
    def __init__(self):
        self.todos: List[TodoRead] = []
        self.persons: List[Person] = []
        self.content_container = None
        self.layout_component = None
        self.language = "sv"

    async def initialize(self):
        """Initial data fetch."""
        self.todos, self.persons = await asyncio.gather(
            api.get_todos(), api.get_persons()
        )

    async def refresh(self):
        """Soft Refresh: Fetch new data and re-render content."""
        await self.initialize()
        await self.render_content(self.current_page_name, self.current_page_page_idx)
        # Verify if layout sidebar needs update (if persons changed)
        # For now, we don't re-render sidebar on every refresh to avoid flicker,
        # but in a real reactive app we might want to.

    async def render_layout(self, current_page: str, page_idx: int = 0):
        """Renders the main layout and sidebar."""
        self.current_page_name = current_page
        self.current_page_page_idx = page_idx

        # Ensure language is up to date from storage
        self.language = app.storage.user.get("language", "sv")

        # Filters
        filter_person = ""
        filter_priority = ""
        try:
            filter_person = app.storage.user.get("filter_person", "")
            filter_priority = app.storage.user.get("filter_priority", "")
        except RuntimeError:
            pass

        async def handle_filter_change(key, value):
            app.storage.user[f"filter_{key}"] = value
            # Just re-render content, no need to fetch
            await self.render_content(
                self.current_page_name, self.current_page_page_idx
            )

        async def handle_language_change(new_lang):
            app.storage.user["language"] = new_lang
            ui.navigate.reload()

        async def handle_create_person(e):
            d = PersonDialog(
                self.persons,
                self.todos,  # Pass todos to check for assignment
                on_success=self.refresh,
                language=self.language,
            )
            d.open()

        async def handle_create_todo(e):
            d = TodoDialog(
                self.persons, on_success=self.refresh, language=self.language
            )
            d.create()

        self.layout_component = Layout(
            persons=self.persons,
            current_page=current_page,
            on_filter_change=handle_filter_change,
            on_refresh=self.refresh,
            on_create_person=handle_create_person,
            on_create_todo=handle_create_todo,
            filter_person=filter_person,
            filter_priority=filter_priority,
            language=self.language,
            on_language_change=handle_language_change,
        )
        self.layout_component.render_sidebar()

        # Main Content Area
        with ui.column().classes(
            "w-full h-screen bg-gray-50 dark:bg-slate-900 text-black dark:text-white overflow-hidden"
        ):
            # Explicit Remove Padding
            ui.context.client.content.classes("p-0 gap-0")

            # Content Container
            self.content_container = ui.column().classes("w-full h-full p-0 gap-0")
            await self.render_content(current_page, page_idx)

    async def render_content(self, current_page: str, page_idx: int = 0):
        if not self.content_container:
            return

        self.content_container.clear()

        # Filter Logic
        filter_person = ""
        filter_priority = ""
        try:
            filter_person = app.storage.user.get("filter_person", "")
            filter_priority = app.storage.user.get("filter_priority", "")
        except RuntimeError:
            pass

        filtered_todos = self.todos
        if filter_person:
            filtered_todos = [
                t for t in filtered_todos if str(t.person_id) == str(filter_person)
            ]
        if filter_priority:
            filtered_todos = [
                t for t in filtered_todos if str(t.priority) == str(filter_priority)
            ]

        with self.content_container:
            # Action Handlers
            async def on_update(todo: TodoRead):
                # UI sends TodoRead object, but API expects dict for update_todo (for now)
                # ApiClient.update_todo takes Dict. We can pass model_dump().
                # But wait, ApiClient.update_todo logic: "todo['id']" -> UUID.
                # If we pass object, we should update ApiClient or convert here.
                # Let's convert here to minimize ApiClient perturbation for now,
                # OR better: update ApiClient to accept TodoUpdate or similar.
                # For quick fix: todo is TodoRead object.
                payload = todo.model_dump()
                res = await api.update_todo(payload)
                if res["success"]:
                    ui.notify("Uppdaterad", type="positive")
                    await self.refresh()
                else:
                    ui.notify(res["error"], type="negative")

            def on_edit(todo: TodoRead):
                d = TodoDialog(
                    self.persons, on_success=self.refresh, language=self.language
                )
                # Dialog expects Dict currently? check Dialogs.
                # TodoDialog.edit takes props. We should verify TodoDialog.
                # For now, pass dict to Dialog to be safe or update Dialog.
                # Let's update Dialog to accept TodoRead!
                # But I haven't updated Dialog fully yet.
                # To be safe and compliant with "Fix Warnings":
                # I will convert to dict for the Dialog for now, or update Dialog.
                # Updating Dialog is better.
                d.edit(todo.model_dump())

            async def on_delete(todo: TodoRead):
                res = await api.delete_todo(str(todo.id))
                if res["success"]:
                    ui.notify("Borttagen", type="positive")
                    await self.refresh()
                else:
                    ui.notify(res["error"], type="negative")

            async def on_restore(todo: TodoRead):
                # toggle completed
                # todo is object.
                # We need to construct payload for update.
                payload = todo.model_dump()
                payload["completed"] = False
                res = await api.update_todo(payload)
                if res["success"]:
                    ui.notify("Uppdaterad", type="positive")
                    await self.refresh()
                else:
                    ui.notify(res["error"], type="negative")

            async def on_generate_subtasks(todo: TodoRead):
                ui.notify("Genererar...", type="info")
                res = await api.generate_subtasks(str(todo.id))
                if res["success"]:
                    ui.notify("Klar!", type="positive")
                    await self.refresh()
                else:
                    ui.notify(res["error"], type="negative")

            async def on_bulk_delete(todos: List[TodoRead]):
                ui.notify(f"Raderar {len(todos)} uppgifter...", type="info")
                for todo in todos:
                    await api.delete_todo(str(todo.id))
                ui.notify("Klar!", type="positive")
                await self.refresh()

            # Render Specific View
            if current_page == "board":
                BoardView(
                    filtered_todos,
                    self.persons,
                    on_update=on_update,
                    on_edit=on_edit,
                    on_delete=on_delete,
                    on_generate_subtasks=on_generate_subtasks,
                    page=page_idx,
                    language=self.language,
                ).render()

                # Pagination Controls
                with ui.row().classes(
                    "absolute bottom-4 left-1/2 transform -translate-x-1/2 "
                    "bg-white dark:bg-slate-800 p-2 rounded-full shadow-lg "
                    "border border-gray-200 dark:border-gray-700 gap-4 items-center"
                ):
                    ui.button(
                        icon="chevron_left",
                        on_click=lambda: ui.navigate.to(
                            f"/board?page={max(0, page_idx - 1)}"
                        ),
                    ).props("flat dense round").classes("text-black dark:text-white")

                    ui.label(
                        f"{self.layout_component.t('page') if self.layout_component else 'Page'} {page_idx + 1}"
                    ).classes("text-sm font-bold text-black dark:text-white")

                    ui.button(
                        icon="chevron_right",
                        on_click=lambda: ui.navigate.to(f"/board?page={page_idx + 1}"),
                    ).props("flat dense round").classes("text-black dark:text-white")

            elif current_page == "history":
                HistoryView(
                    filtered_todos,
                    self.persons,
                    on_delete=on_delete,
                    on_restore=on_restore,
                    on_bulk_delete=on_bulk_delete,
                    language=self.language,
                ).render()
