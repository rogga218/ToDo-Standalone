# ToDo Standalone Project Backlog & Refactoring Roadmap

This document tracks identified code quality improvements, architectural refactoring targets, container/dependency updates, and feature enhancements for the **ToDo Standalone** project.

---

## 📊 Summary of Effort Estimations

- **Low Effort (< 20 mins):** Quick configuration, dependency cleanup, PRAGMA adjustments, or single-file documentation updates.
- **Medium Effort (20 - 45 mins):** Architectural refactoring, thread safety improvements, UI progress components, and unit test expansion.
- **High Effort (1 - 2 hours):** Multi-component features such as import/export utilities or extensive UI flow rewires.

---

## 🛠️ Tasks & Findings Roadmap

### Phase 1: Critical Fixes & Cleanup (Low / Medium Effort)

- [x] **Task 1: Fix Production `Dockerfile` & Enable Health Check**
  - **Category:** Docker / Deployment
  - **Effort:** 🟢 Low (~15 mins)
  - **Description:** Uncomment `COPY src ./src` and the `HEALTHCHECK` directive in `Dockerfile`. Currently, building a container directly (`docker build -t todov2 .`) without Docker Compose volume mounts fails with `ModuleNotFoundError`.
  - **Files Involved:** [`Dockerfile`](Dockerfile)
  - **Verification:** Run `podman build -t test-todo .` and test running the image standalone without mounting source volumes.

- [x] **Task 2: Keep Dependency `httpx2` (User Directive)**
  - **Category:** Maintenance / Dependencies
  - **Effort:** 🟢 Low (0 mins)
  - **Description:** Explicitly retain `httpx2>=2.9.1` in `requirements.txt` per user directive.
  - **Files Involved:** [`requirements.txt`](requirements.txt)
  - **Verification:** Retained in `requirements.txt`.

- [x] **Task 3: Replace Hardcoded Absolute Paths with Relative/Dynamic Paths**
  - **Category:** Portability & Build Configuration
  - **Effort:** 🟢 Low (~15 mins)
  - **Description:** `TodoApp.spec` contains hardcoded absolute Windows paths (`C:\path\to\project\...`). Replace these with relative paths (or dynamic paths derived via `SPECPATH` / `Path(__file__)`) and audit all scripts/tests for any other hardcoded path strings to ensure project portability across different machines and environments.
  - **Files Involved:**
    - [`TodoApp.spec`](TodoApp.spec)
    - [`build.py`](build.py)
  - **Verification:** Run `python build.py` on a clean directory environment and verify `TodoApp.spec` generates dynamic/relative paths.

- [x] **Task 4: Consolidate Redundant Backend Setup (`backend_app.py`)**
  - **Category:** Architecture & Refactoring
  - **Effort:** 🟡 Medium (~30 mins)
  - **Description:** `src/backend_app.py` is dead code in runtime (`main.py` creates its own NiceGUI app setup and seeds "TestPerson1/2/3" while `backend_app.py` seeds "Roger/Bosse/Kalle"). Remove `backend_app.py` and consolidate database initialization & default seeding into `src/database.py`.
  - **Files Involved:** 
    - `src/backend_app.py` *(Delete)*
    - [`src/main.py`](src/main.py)
    - [`src/database.py`](src/database.py)
    - [`tests/test_core_utils.py`](tests/test_core_utils.py)
  - **Verification:** Run `pytest -m "not gui"`, `mypy src`, and `ruff check src`.

---

### Phase 2: Performance & Safety Hardening (Medium Effort)

- [x] **Task 5: Thread-Safe DTO Validation in `ApiClient`**
  - **Category:** Code Safety & Threading
  - **Effort:** 🟡 Medium (~20 mins)
  - **Description:** In `src/ui/api_client.py`, model validation (`TodoRead.model_validate(t)`) occurs outside the database session threadpool boundary. Move validation inside `run_db` so ORM instances are never passed across thread boundaries unvalidated.
  - **Files Involved:** [`src/ui/api_client.py`](src/ui/api_client.py)
  - **Verification:** Run `pytest -m "not gui"` and test UI data loading.

- [x] **Task 6: Enable SQLite WAL Mode & Foreign Key Enforcement**
  - **Category:** Database Performance
  - **Effort:** 🟢 Low (~15 mins)
  - **Description:** Configure SQLAlchemy event listeners for SQLite connections in `src/database.py` to execute `PRAGMA journal_mode=WAL` and `PRAGMA foreign_keys=ON` for improved read/write concurrency.
  - **Files Involved:** [`src/database.py`](src/database.py)
  - **Verification:** Run unit test suite and verify WAL mode operation.

- [x] **Task 7: Update Documentation (`README.md` & `CONTRIBUTING.md`)**
  - **Category:** Documentation
  - **Effort:** 🟢 Low (~15 mins)
  - **Description:** Update `README.md` project tree structure diagram (remove deleted `backend_app.py`), ensure default seeded person descriptions match implementation ("TestPerson1/2/3"), and keep primary testing emphasis on unit/integration tests (`pytest -m "not gui"`).
  - **Files Involved:** 
    - [`README.md`](README.md)
    - [`CONTRIBUTING.md`](CONTRIBUTING.md)
  - **Verification:** Markdown review and link validation.

---

### Phase 3: UI/UX & Coverage Enhancements (Medium / High Effort)

- [x] **Task 8: Visual Subtask Progress Bar on ToDo Cards**
  - **Category:** UI / UX Enhancement
  - **Effort:** 🟡 Medium (~30 mins)
  - **Description:** Add visual progress indicators (e.g. `ui.linear_progress` or badge counters) to ToDo cards on the Board view to show subtask completion status (e.g. `2 / 5 completed`).
  - **Files Involved:** [`src/ui/pages/board.py`](src/ui/pages/board.py)
  - **Verification:** Run `npx playwright test` and visually inspect board UI.

- [x] **Task 9: Enhanced Form Input Validation Feedback**
  - **Category:** UI / UX Enhancement
  - **Effort:** 🟡 Medium (~30 mins)
  - **Description:** Render explicit validation messages directly under input fields in dialog modals (e.g., when entering a duplicate person name or an invalid deadline) instead of generic toast error messages.
  - **Files Involved:** 
    - [`src/ui/components/dialogs.py`](src/ui/components/dialogs.py)
    - [`src/ui/controller.py`](src/ui/controller.py)
  - **Verification:** Manual UI testing and Playwright E2E assertion tests.

- [x] **Task 10: Expand UI Unit Test Coverage (>80%)**
  - **Category:** Testing & Quality Assurance
  - **Effort:** 🟡 Medium (~45 mins)
  - **Description:** Write targeted unit tests for `src/ui/pages/board.py` (currently 79%), `src/ui/layout.py` (100%), `src/ui/components/dialogs.py`, and `src/core/errors.py` (93%) to bring overall codebase coverage above 80%.
  - **Files Involved:** `tests/test_ui_pages.py`, `tests/test_ui_dialogs.py`, `tests/test_core.py`
  - **Verification:** Run `pytest --cov=src` and check coverage report.

- [x] **Task 11: JSON/CSV Backup & Import Utility**
  - **Category:** Feature Addition
  - **Effort:** 🔴 High (~1 hour)
  - **Description:** Implement a backup export and import service allowing users to download or upload ToDo items and Person lists in JSON/CSV formats.
  - **Files Involved:**
    - [`src/services/export_service.py`](src/services/export_service.py)
    - [`src/routers/backup.py`](src/routers/backup.py)
    - [`src/ui/pages/history.py`](src/ui/pages/history.py)
  - **Verification:** Unit tests for export/import logic and UI button testing.


---

*Last Updated: 2026-11-11 (Dependencies modernized to NiceGUI 4.0 / GenAI 3.2, AI thinking configuration added, and docs synchronized)*
