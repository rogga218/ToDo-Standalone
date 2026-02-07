from typing import Dict

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "sv": {
        # Navigation
        "dashboard": "Översikt",
        "history": "Historik",
        "new_task": "Ny Uppgift",
        "new_person": "Ny Person",
        "refresh": "Uppdatera",
        # Filters & Labels
        "filter_label": "FILTER",
        "all_persons": "Alla Personer",
        "all_priorities": "Alla Prioriteringar",
        "priority_label": "Prioritet",
        "person_label": "Person",
        "high": "Hög",
        "medium": "Medium",
        "low": "Låg",
        # Theme
        "theme_dark": "Mörkt",
        "theme_light": "Ljust",
        # Dialogs - Person
        "dialog_new_person": "Ny Person",
        "name_label": "Namn",
        "existing_persons": "Befintliga Personer:",
        "name_required": "Namn krävs",
        "person_created": "Person skapad!",
        "save": "Spara",
        # Dialogs - Todo
        "dialog_new_todo": "Ny Uppgift",
        "dialog_edit_todo": "Redigera Uppgift",
        "title_label": "Titel",
        "desc_label": "Beskrivning",
        "deadline_label": "Deadline",
        "title_person_required": "Titel och Person krävs",
        "updated": "Uppdaterad",
        "task_created": "Uppgift skapad!",
        # Common Errors
        "error_generic": "Ett fel uppstod",
        # Board
        "delayed": "Försenade",
        "today": "Idag",
        "no_date": "Odatum",
        "subtasks": "Deluppgifter",
        "ai_subtasks": "AI Deluppgifter",
        "subtasks_exist": "Deluppgifter finns redan",
        "edit": "Redigera",
        "undo": "Ångra",
        "done": "Klart",
        "delete": "Ta bort",
        # History
        "history_header": "Historik",
        "no_completed_tasks": "Inga avklarade uppgifter än.",
        "select_all": "Markera alla",
        "selected": "valda",
        "completed_by": "Slutförd av",
        "restore": "Återställ",
    },
    "en": {
        # Navigation
        "dashboard": "Dashboard",
        "history": "History",
        "new_task": "New Task",
        "new_person": "New Person",
        "refresh": "Refresh",
        # Filters & Labels
        "filter_label": "FILTERS",
        "all_persons": "All Persons",
        "all_priorities": "All Priorities",
        "priority_label": "Priority",
        "person_label": "Person",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
        # Theme
        "theme_dark": "Dark",
        "theme_light": "Light",
        # Dialogs - Person
        "dialog_new_person": "New Person",
        "name_label": "Name",
        "existing_persons": "Existing Persons:",
        "name_required": "Name is required",
        "person_created": "Person created!",
        "save": "Save",
        # Dialogs - Todo
        "dialog_new_todo": "New Task",
        "dialog_edit_todo": "Edit Task",
        "title_label": "Title",
        "desc_label": "Description",
        "deadline_label": "Deadline",
        "title_person_required": "Title and Person are required",
        "updated": "Updated",
        "task_created": "Task created!",
        # Common Errors
        "error_generic": "An error occurred",
        # Board
        "delayed": "Delayed",
        "today": "Today",
        "no_date": "No Date",
        "subtasks": "Subtasks",
        "ai_subtasks": "AI Subtasks",
        "subtasks_exist": "Subtasks already exist",
        "edit": "Edit",
        "undo": "Undo",
        "done": "Done",
        "delete": "Delete",
        # History
        "history_header": "History",
        "no_completed_tasks": "No completed tasks yet.",
        "select_all": "Select All",
        "selected": "selected",
        "completed_by": "Completed by",
        "restore": "Restore",
    },
}


def get_text(key: str, lang: str = "sv") -> str:
    """Retrieves translation for key and language."""
    return TRANSLATIONS.get(lang, TRANSLATIONS["sv"]).get(key, key)
