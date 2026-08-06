from typing import Any, Callable, Dict, List

from nicegui import ui

from src.config import get_settings
from src.models import Person, TodoRead
from src.ui.api_client import api
from src.ui.translations import get_text


class BoardView:
    def __init__(
        self,
        todos: List[TodoRead],
        persons: List[Person],
        on_update: Callable[[TodoRead], Any],
        on_edit: Callable[[TodoRead], Any],
        on_delete: Callable[[TodoRead], Any],
        on_generate_subtasks: Callable[[TodoRead], Any],
        page: int = 0,
        language: str = "sv",
    ) -> None:
        self.todos = todos
        self.persons = persons
        self.on_update = on_update
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_generate_subtasks = on_generate_subtasks
        self.page = page
        self.language = language

    def t(self, key: str) -> str:
        return get_text(key, self.language)

    def render(self) -> None:
        from datetime import date

        today_date = date.today()

        # 1. Filter Todos
        # Show if: Not completed OR (Completed AND Deadline >= Today)
        active_todos: List[TodoRead] = []
        for t in self.todos:
            if not t.completed:
                active_todos.append(t)
            else:
                # If completed, check deadline
                deadline = t.deadline
                if deadline and deadline >= today_date:
                    active_todos.append(t)

        # 2. Sort Everyone (Prio Asc, then Title Asc)
        # Note: Priority 1=High, 3=Low. So Asc is correct.
        active_todos.sort(key=lambda t: (t.priority, t.title))

        # 3. Categorize
        overdue: List[TodoRead] = []
        today: List[TodoRead] = []
        future_map: Dict[str, List[TodoRead]] = {}  # date -> list

        for todo in active_todos:
            deadline = todo.deadline
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
                d_str = str(deadline)
                if d_str not in future_map:
                    future_map[d_str] = []
                future_map[d_str].append(todo)

        # 4. Build Columns List
        columns_data: List[Dict[str, Any]] = []

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
        total_pages = max(1, (len(columns_data) + page_size - 1) // page_size)
        current_page = max(0, min(self.page, total_pages - 1))

        start_idx = current_page * page_size
        end_idx = start_idx + page_size
        visible_columns = columns_data[start_idx:end_idx]

        with ui.row().classes("w-full h-full gap-4 overflow-x-auto no-wrap p-4 items-start"):
            for col in visible_columns:
                with ui.column().classes(f"min-w-[320px] flex-1 h-full rounded-xl p-4 {col['bg']} border"):
                    items: List[TodoRead] = col["items"]
                    all_completed = not items or all(t.completed for t in items)
                    indicator_color = "bg-green-500" if all_completed else "bg-red-500"

                    with ui.row().classes("items-center mb-4"):
                        ui.label().classes(f"w-3 h-3 rounded-full mr-2 {indicator_color}")
                        ui.label(f"{col['title']} ({len(items)})").classes(
                            "text-lg font-bold text-gray-900 dark:text-white"
                        )

                    with ui.scroll_area().classes("w-full h-full"):
                        with ui.column().classes("gap-3 w-full"):
                            for todo in items:
                                self.render_card(todo)

    def render_card(self, todo: TodoRead) -> None:
        prio_color_border = {
            1: "border-l-4 border-red-500",
            2: "border-l-4 border-yellow-500",
            3: "border-l-4 border-green-500",
        }.get(todo.priority, "border-l-4 border-gray-500")

        card_classes = f"w-full q-pa-sm hovered-scale border-solid {prio_color_border} dark:bg-slate-800"

        if todo.completed:
            card_classes += " opacity-60"

        with ui.card().classes(card_classes):
            # Header: Person
            person_name = next((p.name for p in self.persons if str(p.id) == str(todo.person_id)), "?")

            with ui.row().classes("w-full justify-between items-center text-xs opacity-70 mb-1"):
                ui.label(person_name).classes("font-bold")
                if todo.deadline:
                    ui.label(str(todo.deadline))

            # Title & Desc
            title_classes = "text-md font-bold mb-1 leading-tight block break-words"
            if todo.completed:
                title_classes += " line-through opacity-50"

            ui.label(todo.title).classes(title_classes)
            if todo.description:
                ui.label(todo.description).classes("text-xs opacity-80 mb-2 block break-words whitespace-pre-wrap")

            # Subtasks
            subtasks = todo.subtasks
            if subtasks:
                total_subs = len(subtasks)
                done_subs = sum(1 for s in subtasks if s.completed)
                pct = done_subs / total_subs if total_subs > 0 else 0.0

                expansion = (
                    ui.expansion()
                    .classes("w-full bg-gray-100 dark:bg-slate-900/50 rounded text-xs mb-2")
                    .props(f'dense icon="list" label="{self.t("subtasks")} ({done_subs}/{total_subs})"')
                )
                with expansion:
                    progress = (
                        ui.linear_progress(value=pct, show_value=False)
                        .classes("mb-2 h-1.5 rounded bg-gray-200 dark:bg-slate-700")
                        .props("color=positive" if pct == 1.0 else "color=primary")
                    )
                    for sub in subtasks:
                        with ui.row().classes("items-start gap-2 no-wrap w-full"):
                            lbl = ui.label(sub.title).classes(
                                "flex-1 break-words opacity-80" + (" line-through" if sub.completed else "")
                            )
                            ui.checkbox(
                                value=sub.completed,
                                # type: ignore[arg-type]
                                on_change=lambda e, t=todo, s=sub, exp=expansion, prog=progress, target_lbl=lbl: (
                                    self.toggle_subtask(t, s, e.value, exp, prog, target_lbl)
                                ),
                            ).props("dense")

            # Actions
            with ui.row().classes("w-full justify-end gap-2 mt-2"):
                icon_classes = "text-gray-600 dark:text-white"

                if get_settings().GEMINI_API_KEY:
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

                ui.button(icon="edit", on_click=lambda: self.on_edit(todo)).props("flat dense size=sm round").classes(
                    icon_classes
                ).tooltip(self.t("edit"))

                if todo.completed:
                    ui.button(icon="replay", on_click=lambda: self.toggle_complete(todo)).props(
                        "flat dense size=sm round"
                    ).classes("text-gray-500 dark:text-gray-400").tooltip(self.t("undo"))
                else:
                    ui.button(icon="check", on_click=lambda: self.toggle_complete(todo)).props(
                        "flat dense size=sm round"
                    ).classes("text-green-600 dark:text-green-400").tooltip(self.t("done"))

                ui.button(icon="delete", on_click=lambda: self.on_delete(todo)).props(
                    "flat dense size=sm round"
                ).classes("text-red-600 dark:text-red-400").tooltip(self.t("delete"))

    async def toggle_complete(self, todo: TodoRead) -> None:
        todo.completed = not todo.completed
        await self.on_update(todo)

    async def toggle_subtask(
        self,
        todo: TodoRead,
        subtask: Any,
        completed: bool,
        expansion: ui.expansion | None = None,
        progress: ui.linear_progress | None = None,
        label: ui.label | None = None,
    ) -> None:
        subtask.completed = completed
        if label:
            if completed:
                label.classes(add="line-through")
            else:
                label.classes(remove="line-through")

        if expansion and progress and todo.subtasks:
            total_subs = len(todo.subtasks)
            done_subs = sum(1 for s in todo.subtasks if s.completed)
            pct = done_subs / total_subs if total_subs > 0 else 0.0

            progress.set_value(pct)
            progress.props(f"color={'positive' if pct == 1.0 else 'primary'}")
            expansion.props(f'label="{self.t("subtasks")} ({done_subs}/{total_subs})"')

        await api.toggle_subtask(str(subtask.id), completed)
