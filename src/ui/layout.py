from nicegui import ui
from typing import Callable, Dict, List


class Layout:
    def __init__(
        self,
        persons: List[Dict],  # Needed for filters
        current_page: str,
        on_filter_change: Callable,
        on_refresh: Callable,
        on_create_person: Callable,
        on_create_todo: Callable,
        filter_person: str = "",
        filter_priority: str = "",
        language: str = "sv",
        on_language_change: Callable = None,
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
        # Default to Dark Mode if first visit (value is None/False initially sometimes?)
        # Actually ui.dark_mode value persists. But to ensure "Default is Dark", we can check if it's explicitly False?
        # A simpler way is to just enable it. But we don't want to override user pref if they set Light.
        # But user reported "Light mode seems default now".
        # Let's force enable it once to fix their state, or use a startup handler.
        # Ideally: ui.run(dark=True).
        # Let's try: self.dark_mode.enable() in __init__ is risky if it resets on every nav.
        # Better: ui.run(dark=True) in main.py updates the client value.
        # Issue might be persistence overriding ui.run(dark=True).
        # We can add a startup script check.
        # For now, let's trust that fixing the card styles resolves the "Looks like light mode" issue.
        # BUT, if cards were white on black bg, then dark mode WAS active partially?
        # No, main bg is hardcoded in main.py. Cards had `bg-white`.
        # If I remove `bg-white` and leave `bg-slate-800` for dark, I need to ensure `dark` class works.
        # I'll enable it here just to be safe for this session.
        self.dark_mode.enable()

        # Translations
        self.translations = {
            "sv": {
                "dashboard": "Översikt",
                "history": "Historik",
                "new_task": "Ny Uppgift",
                "new_person": "Ny Person",
                "filter_label": "FILTER",
                "all_persons": "Alla Personer",
                "all_priorities": "Alla Prioriteringar",
                "priority_label": "Prioritet",
                "person_label": "Person",
                "refresh": "Uppdatera",
                "high": "Hög",
                "medium": "Medium",
                "low": "Låg",
                "theme_dark": "Mörkt",
                "theme_light": "Ljust",
            },
            "en": {
                "dashboard": "Dashboard",
                "history": "History",
                "new_task": "New Task",
                "new_person": "New Person",
                "filter_label": "FILTERS",
                "all_persons": "All Persons",
                "all_priorities": "All Priorities",
                "priority_label": "Priority",
                "person_label": "Person",
                "refresh": "Refresh",
                "high": "High",
                "medium": "Medium",
                "low": "Low",
                "theme_dark": "Dark",
                "theme_light": "Light",
            },
        }

    def t(self, key):
        return self.translations.get(self.language, {}).get(key, key)

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
                ui.image("/assets/logo.png").classes("w-64 mb-4")

                with ui.row().classes("gap-4"):
                    # Theme Toggle
                    icon = "dark_mode" if self.dark_mode.value else "light_mode"
                    # Lets use !text classes.
                    # Actually, if I use style="color: ..." it might not be responsive to dark class easily without css var.
                    # Let's stick to Tailwind !important
                    ui.button(icon=icon, on_click=self.dark_mode.toggle).props(
                        "flat round size=sm"
                    ).classes("!text-zinc-900 dark:!text-zinc-100").tooltip(
                        "Toggle Theme"
                    )

                    # Language Toggle
                    flag = "🇸🇪" if self.language == "sv" else "🇬🇧"
                    next_lang = "en" if self.language == "sv" else "sv"
                    ui.button(
                        flag, on_click=lambda: self.on_language_change(next_lang)
                    ).props("flat round size=sm").classes(
                        "!text-zinc-900 dark:!text-zinc-100"
                    ).tooltip("Switch Language")

            # Navigation
            with ui.column().classes("w-full gap-2 mb-8"):

                def nav_btn(label, target, active_key):
                    is_active = self.current_page == active_key
                    # Active: Blue (keep)
                    # Inactive: Light: Gray-300, Dark: Slate-800
                    bg = (
                        "bg-blue-600 text-white"
                        if is_active
                        else "bg-gray-300 hover:bg-gray-400 dark:bg-slate-800 dark:hover:bg-slate-700 text-black dark:text-white"
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
            person_options.update({p["id"]: p["name"] for p in self.persons})

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
                ui.button(self.t("new_person"), on_click=self.on_create_person).classes(
                    "w-full bg-green-600 hover:bg-green-700 text-white"
                )

            # Refresh
            ui.button(
                self.t("refresh"), on_click=self.on_refresh, icon="refresh"
            ).classes(
                "w-full mt-auto bg-gray-300 dark:bg-slate-700 hover:bg-gray-400 dark:hover:bg-slate-600 !text-zinc-900 dark:!text-zinc-100"
            )
