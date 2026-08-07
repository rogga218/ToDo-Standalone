# Agent Directives: ToDo Standalone

## 1. Quick Verification Commands
Always run these commands before concluding code tasks:
- **Linting & Formatting:** `ruff check src` & `ruff format src`
- **Type Checking:** `mypy src`
- **Unit & Integration Tests:** `pytest -v`
- **E2E Browser Tests:** `npx playwright test`
- **Dependency Audit:** `pip-audit -r requirements.txt`

## 2. Architecture & Path Map
Maintain strict Separation of Concerns (SoC):
- **UI Components & Pages:** `src/ui/` (NiceGUI pages, dialogs, theme, i18n in `translations.py`)
- **Business Logic Services:** `src/services/` (`todo_service.py`, `person_service.py`, `ai_service.py`)
- **FastAPI Endpoints:** `src/routers/` (`todos.py`, `persons.py`, `ai.py`)
- **Data Models:** `src/models.py` (SQLModel / Pydantic V2)
- **Database & Config:** `src/database.py` (SQLite & sessions), `src/config.py` (loads `.env`)

## 3. Key Patterns & Gotchas
- **DB Sessions:** Services accept an explicit `Session` (`session: Session`). Do not create global unclosed sessions.
- **UI & Controller Separation:** Keep `src/ui/pages/` declarative. Route state & data logic through `src/ui/controller.py`.
- **SQLModel Relationships:** Eager-load nested models (`Todo.subtasks`) within active session contexts before UI rendering.
- **Dual Requirements:** Runtime dependencies stay in `requirements.txt`; EXE packaging tools (`PyInstaller`, `PySide6`) stay in `requirements-build.txt`.
- **Test Markers:** Fast unit & integration tests run via `pytest`. E2E browser tests run via `npx playwright test`.

## 4. Mandatory Constraints & Environment
- **Terminal:** Operating in Windows — use **PowerShell** syntax exclusively for terminal commands.
- **Containers:** Prefer `podman-compose` (or `docker-compose`) for container commands (e.g. `podman-compose up --build -d`).
- **Environment & Config:** Runtime variables (`DATABASE_URL`, `GEMINI_API_KEY`, `STORAGE_SECRET`, `PORT`) are driven by `.env` (templated in `.env.example`).
- **Zero Warnings:** Fix all LSP errors, lint warnings, and type errors before concluding tasks.
- **Language Policy:** Write all code, docstrings, and comments in **English**.
- **Test Coverage:** Maintain >65% test coverage requirement (`pytest-cov`).

## 5. Execution Workflow
1. **Inspect:** Read relevant source files and schemas before making edits.
2. **Implement:** Write modular code following Separation of Concerns.
3. **Verify:** Run `ruff check src`, `mypy src`, and `pytest -v`.
4. **Document:** Keep `README.md` and documentation up to date when adding features or changing configs.
