from nicegui import ui, app
from typing import Callable, List, Optional
from src.ui.translations import get_text
from src.models import Person


class Layout:
    def __init__(
        self,
        persons: List[Person],  # Needed for filters
        current_page: str,
        on_filter_change: Callable,
        on_refresh: Callable,
        on_create_person: Callable,
        on_create_todo: Callable,
        filter_person: str = "",
        filter_priority: str = "",
        language: str = "sv",
        on_language_change: Optional[Callable] = None,
    ):
        self.persons = persons
        self.current_page = current_page
        self.on_filter_change = on_filter_change
        self.on_refresh = on_refresh
        self.on_create_person = on_create_person
        self.on_create_todo = on_create_todo
        self.filter_person = filter_person
        self.filter_priority = filter_priority
        self.language = language
        self.on_language_change = on_language_change

        self.dark_mode = ui.dark_mode()
        # Initialize dark mode from storage (default to True if not set)
        stored_dark = app.storage.user.get("dark_mode", True)
        self.dark_mode.value = stored_dark

    def toggle_dark_mode(self):
        print(f"Toggling dark mode. Current: {self.dark_mode.value}")
        self.dark_mode.toggle()
        print(f"New value: {self.dark_mode.value}")
        app.storage.user["dark_mode"] = self.dark_mode.value

    def t(self, key):
        return get_text(key, self.language)

    def render_sidebar(self):
        with (
            ui.left_drawer()
            .classes("bg-gray-100 dark:bg-slate-900 text-black dark:text-white q-pa-md")
            .props("width=300 breakpoint=0")
        ):
            # Logo & Toggles
            with ui.column().classes("w-full items-center mb-6"):
                # In light mode, might want a different logo or just same?
                # Assuming logo works on both or we might need opacity.
                # Logo (Inline SVG for Dark Mode support)
                with (
                    ui.element("svg")
                    .props('viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"')
                    .classes("w-32 mb-4")
                ):
                    # Outline Rect
                    ui.element("rect").props(
                        'x="15" y="15" width="70" height="70" rx="10" stroke-width="6" fill="none"'
                    ).classes("stroke-zinc-800 dark:stroke-zinc-100")
                    # Line 1
                    ui.element("path").props(
                        'd="M30 40 L70 40" stroke-width="6" stroke-linecap="round"'
                    ).classes("stroke-zinc-800 dark:stroke-zinc-100")
                    # Line 2
                    ui.element("path").props(
                        'd="M30 60 L60 60" stroke-width="6" stroke-linecap="round"'
                    ).classes("stroke-zinc-800 dark:stroke-zinc-100")
                    # Circle
                    ui.element("circle").props('cx="75" cy="75" r="12"').classes(
                        "fill-amber-400 dark:fill-amber-300"
                    )

                with ui.row().classes("gap-4"):
                    # Theme Toggle
                    icon = "dark_mode" if self.dark_mode.value else "light_mode"
                    # Lets use !text classes.
                    # Actually, if I use style="color: ..." it might not be responsive to dark class easily without css var.
                    # Let's stick to Tailwind !important
                    ui.button(icon=icon, on_click=self.toggle_dark_mode).props(
                        "flat round size=sm"
                    ).classes("!text-zinc-900 dark:!text-zinc-100").tooltip(
                        "Toggle Theme"
                    )

                    # Language Toggle
                    flag = "🇸🇪" if self.language == "sv" else "🇬🇧"
                    next_lang = "en" if self.language == "sv" else "sv"
                    ui.button(
                        flag,
                        on_click=lambda: (
                            self.on_language_change(next_lang)
                            if self.on_language_change
                            else None
                        ),
                    ).props("flat round size=sm").classes(
                        "!text-zinc-900 dark:!text-zinc-100"
                    ).tooltip("Switch Language")

            # Navigation
            with ui.column().classes("w-full gap-2 mb-8"):

                def nav_btn(label, target, active_key):
                    is_active = self.current_page == active_key
                    # Active: Blue (keep)
                    # Inactive Request: "svart i dark-mode och vit i light-mode" (Black text in Dark, White in Light)
                    # This implies we need high contrast backgrounds:
                    # Light Mode: Dark Background (e.g., Slate-700) -> White Text
                    # Dark Mode: Light Background (e.g., Gray-200) -> Black Text
                    bg = (
                        "bg-blue-600 text-white"
                        if is_active
                        else "bg-slate-700 hover:bg-slate-600 text-white dark:bg-gray-200 dark:hover:bg-gray-300 dark:text-black"
                    )
                    ui.button(label, on_click=lambda: ui.navigate.to(target)).classes(
                        f"w-full {bg}"
                    )

                nav_btn(self.t("dashboard"), "/board", "board")
                nav_btn(self.t("history"), "/history", "history")

            # Ny Uppgift
            ui.button(self.t("new_task"), on_click=self.on_create_todo).classes(
                "w-full bg-indigo-600 hover:bg-indigo-700 text-white mb-6"
            )

            # Filters
            ui.label(self.t("filter_label")).classes(
                "text-xs font-bold text-gray-500 dark:text-slate-400 mb-2"
            )

            # Person Filter
            person_options = {"": self.t("all_persons")}
            # Access Person attributes
            person_options.update({str(p.id): p.name for p in self.persons})

            ui.select(
                options=person_options,
                value=self.filter_person,
                on_change=lambda e: self.on_filter_change("person", e.value),
                label=self.t("person_label"),
            ).classes("w-full mb-4 bg-gray-200 dark:bg-slate-800 rounded")

            # Priority Filter
            priority_options = {
                "": self.t("all_priorities"),
                "1": f"{self.t('high')} (1)",
                "2": f"{self.t('medium')} (2)",
                "3": f"{self.t('low')} (3)",
            }
            ui.select(
                options=priority_options,
                value=str(self.filter_priority),
                on_change=lambda e: self.on_filter_change("priority", e.value),
                label=self.t("priority_label"),
            ).classes("w-full mb-6 bg-gray-200 dark:bg-slate-800 rounded")

            # Actions
            with ui.column().classes("w-full gap-2"):
                ui.button(
                    self.t("manage_persons"), on_click=self.on_create_person
                ).classes("w-full bg-green-600 hover:bg-green-700 text-white")

            # Refresh
            ui.button(
                self.t("refresh"), on_click=self.on_refresh, icon="refresh"
            ).classes(
                "w-full mt-auto bg-slate-700 hover:bg-slate-600 text-white dark:bg-gray-200 dark:hover:bg-gray-300 dark:text-black"
            )
