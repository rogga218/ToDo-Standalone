from nicegui import ui
from typing import List, Dict, Callable
from src.ui.api_client import api


from src.ui.translations import get_text


class BoardView:
    def __init__(
        self,
        todos: List[Dict],
        persons: List[Dict],
        on_update: Callable,
        on_edit: Callable,
        on_delete: Callable,
        on_generate_subtasks: Callable,
        page: int = 0,
        language: str = "sv",
    ):
        self.todos = todos
        self.persons = persons
        self.on_update = on_update
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_generate_subtasks = on_generate_subtasks
        self.page = page
        self.language = language

    def t(self, key):
        return get_text(key, self.language)

    def render(self):
        from datetime import date

        today_date = date.today()

        # 1. Filter Todos
        # Show if: Not completed OR (Completed AND Deadline >= Today)
        active_todos = []
        for t in self.todos:
            if not t["completed"]:
                active_todos.append(t)
            else:
                # If completed, check deadline
                deadline = t.get("deadline")
                if deadline and deadline >= today_date:
                    active_todos.append(t)

        # 2. Sort Everyone (Prio Asc, then Title Asc)
        # Note: Priority 1=High, 3=Low. So Asc is correct.
        active_todos.sort(key=lambda t: (t["priority"], t["title"]))

        # 3. Categorize
        overdue = []
        today = []
        future_map = {}  # date -> list

        for todo in active_todos:
            deadline = todo.get("deadline")
            if not deadline:
                key = self.t("no_date")
                if key not in future_map:
                    future_map[key] = []
                future_map[key].append(todo)
                continue

            if deadline < today_date:
                overdue.append(todo)
            elif deadline == today_date:
                today.append(todo)
            else:
                if deadline not in future_map:
                    future_map[deadline] = []
                future_map[deadline].append(todo)

        # 4. Build Columns List
        columns_data = []

        # Overdue allowed if exists
        if overdue:
            columns_data.append(
                {
                    "title": self.t("delayed"),
                    "bg": "bg-red-100 dark:bg-red-500/10 border-red-200 dark:border-red-500/20",
                    "items": overdue,
                }
            )

        # Today
        columns_data.append(
            {
                "title": self.t("today"),
                "bg": "bg-blue-100 dark:bg-blue-500/10 border-blue-200 dark:border-blue-500/20",
                "items": today,
            }
        )

        # Future Dates
        sorted_dates = sorted([k for k in future_map.keys() if k != self.t("no_date")])
        # Add Future dates
        for d in sorted_dates:
            columns_data.append(
                {
                    "title": d,
                    "bg": "bg-gray-100 dark:bg-slate-500/10 border-gray-200 dark:border-slate-500/20",
                    "items": future_map[d],
                }
            )

        # Add No Date last
        if self.t("no_date") in future_map:
            columns_data.append(
                {
                    "title": self.t("no_date"),
                    "bg": "bg-gray-100 dark:bg-slate-500/10 border-gray-200 dark:border-slate-500/20",
                    "items": future_map[self.t("no_date")],
                }
            )

        # Pagination
        page_size = 4
        # Calculate safe page
        total_pages = max(1, (len(columns_data) + page_size - 1) // page_size)
        current_page = max(0, min(self.page, total_pages - 1))

        start_idx = current_page * page_size
        end_idx = start_idx + page_size
        visible_columns = columns_data[start_idx:end_idx]

        with ui.row().classes(
            "w-full h-full gap-4 overflow-x-auto no-wrap p-4 items-start"
        ):
            for col in visible_columns:
                with ui.column().classes(
                    f"min-w-[320px] flex-1 h-full rounded-xl p-4 {col['bg']} border"
                ):
                    ui.label(f"{col['title']} ({len(col['items'])})").classes(
                        "text-lg font-bold mb-4 text-gray-900 dark:text-white"
                    )

                    with ui.scroll_area().classes("w-full h-full"):
                        with ui.column().classes("gap-3 w-full"):
                            for todo in col["items"]:
                                self.render_card(todo)

    def render_card(self, todo):
        # Card Styling: "P1, P2" removal, colored relief
        prio_color_border = {
            1: "border-l-4 border-red-500",
            2: "border-l-4 border-yellow-500",
            3: "border-l-4 border-green-500",
        }.get(todo["priority"], "border-l-4 border-gray-500")

        # Styling for completed
        # Remove explicit bg-white/text-black to let Quasar handle defaults,
        # but add dark:bg-slate-800 for custom dark shade if properly triggered.
        # Fallback: bg-white for light (implicitly via Quasar? No q-card is white).
        # We explicitly set bg-white for Light, and bg-slate-800 for Dark.
        # But if 'dark:' fails, we get default (which might be transparent or white).
        # Safe bet: "bg-white dark:bg-slate-800" SHOULD work if Tailwind is aware.
        # If user saw white cards in dark mode, 'dark:' failed or bg-white won.
        # Let's try: "bg-white text-black dark:bg-slate-800 dark:text-white"
        # AND add 'q-card--dark' manually? No.

        # Simplified: Use Quasar default classes where possible, or specific gray scale.
        # Quasar q-card is white by default.
        # In dark mode, it becomes dark IF q-card--dark is set OR if we override.
        # We want slate-800 in dark mode.
        # We REMOVE bg-white so it defaults to white (or transparent if flat).
        # We keep dark:bg-slate-800.
        card_classes = f"w-full q-pa-sm hovered-scale border-solid {prio_color_border} dark:bg-slate-800"

        if todo["completed"]:
            card_classes += " opacity-60"

        with ui.card().classes(card_classes):
            # Header: Person
            person_name = next(
                (p["name"] for p in self.persons if p["id"] == todo["person_id"]), "?"
            )

            with ui.row().classes(
                "w-full justify-between items-center text-xs opacity-70 mb-1"
            ):
                ui.label(person_name).classes("font-bold")
                if todo.get("deadline"):
                    ui.label(todo["deadline"])

            # Title & Desc ("visar hela texten")
            # Remove text-black. Inherit color.
            title_classes = "text-md font-bold mb-1 leading-tight block break-words"
            if todo["completed"]:
                title_classes += " line-through opacity-50"

            ui.label(todo["title"]).classes(title_classes)
            if todo.get("description"):
                ui.label(todo["description"]).classes(
                    "text-xs opacity-80 mb-2 block break-words whitespace-pre-wrap"
                )

            # Subtasks
            subtasks = todo.get("subtasks", [])
            if subtasks:
                with (
                    ui.expansion()
                    .classes(
                        "w-full bg-gray-100 dark:bg-slate-900/50 rounded text-xs mb-2"
                    )
                    .props(f'dense icon="list" label="{self.t("subtasks")}"')
                ):
                    for sub in subtasks:
                        with ui.row().classes("items-start gap-2 no-wrap w-full"):
                            ui.checkbox(
                                value=sub["completed"],
                                on_change=lambda e, s=sub: self.toggle_subtask(
                                    todo, s, e.value
                                ),
                            ).props("dense")
                            ui.label(sub["title"]).classes(
                                "flex-1 break-words opacity-80"
                                + (" line-through" if sub["completed"] else "")
                            )

            # Actions
            with ui.row().classes("w-full justify-end gap-2 mt-2"):
                # Explicitly set colors for icons to handle dark mode
                icon_classes = "text-gray-600 dark:text-white"

                ai_btn = (
                    ui.button(
                        icon="smart_toy",
                        on_click=lambda: self.on_generate_subtasks(todo),
                    )
                    .props("flat dense size=sm round")
                    .classes(icon_classes)
                    .tooltip(self.t("ai_subtasks"))
                )
                if subtasks:
                    ai_btn.disable()
                    ai_btn.tooltip(self.t("subtasks_exist"))

                ui.button(icon="edit", on_click=lambda: self.on_edit(todo)).props(
                    "flat dense size=sm round"
                ).classes(icon_classes).tooltip(self.t("edit"))

                if todo["completed"]:
                    ui.button(
                        icon="replay", on_click=lambda: self.toggle_complete(todo)
                    ).props("flat dense size=sm round").classes(
                        "text-gray-500 dark:text-gray-400"
                    ).tooltip(self.t("undo"))
                else:
                    ui.button(
                        icon="check", on_click=lambda: self.toggle_complete(todo)
                    ).props("flat dense size=sm round").classes(
                        "text-green-600 dark:text-green-400"
                    ).tooltip(self.t("done"))

                ui.button(icon="delete", on_click=lambda: self.on_delete(todo)).props(
                    "flat dense size=sm round"
                ).classes("text-red-600 dark:text-red-400").tooltip(self.t("delete"))

    async def toggle_complete(self, todo):
        todo["completed"] = not todo["completed"]
        await self.on_update(todo)

    async def toggle_subtask(self, todo, subtask, completed):
        await api.toggle_subtask(subtask["id"], completed)
        # Refresh logic should be handled by parent re-render or explicit refresh
        # But for now we rely on the parent refreshing the data
        # To make it snappy we might want optimistic updates but let's stick to refresh for MVP
        # Actually Layout handles "on_refresh", maybe we just call it?
        # Ideally we pass a callback that triggers data fetch.
        pass  # The checkbox change triggers this, but we also want to update UI.
        # For now, let's assume the user manually refreshes or we trigger a global refresh.
        # Better: invalidating the data in main.
