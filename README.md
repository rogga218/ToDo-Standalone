# ToDo App (NiceGUI Standalone)

A modern, fast, and simple ToDo application built with **NiceGUI** and **SQLite**. Made with Google Antigravity and Gemini.

This project has been refactored to specificially focus on a single, native Python implementation, consolidating previous backend and frontend components into a unified structure.

## Features

-   **Native Python UI**: Built with [NiceGUI](https://nicegui.io).
-   **Integrated Backend**: Business logic runs directly within the application (no internal HTTP requests).
-   **SQLite Database**: Simple, file-based database for easy deployment.
-   **Localization**: Built-in support for multiple languages (English and Swedish).
-   **AI Subtasks**: Auto-generate subtasks using Google Gemini.
-   **Responsive Design**: Works on Desktop and Mobile.
-   **Dark Mode**: Enabled by default.

## Tech Stack

-   **Frontend/UI**: NiceGUI (Vue.js based)
-   **Backend**: FastAPI (Integrated)
-   **Database**: SQLite with SQLModel (ORM)
-   **AI**: Google Generative AI (Gemini)
-   **Build Tool**: PyInstaller

## Project Structure

```
├── .env                                  # Configuration file
├── .env.example                          # Configuration template
├── .gitignore                            # Git ignore file
├── build.py                              # Build script (PyInstaller)
├── docker-compose.yml                    # Orchestration
├── Dockerfile                            # Container definition
├── README.md                             # Project documentation
├── pyproject.toml                        # Project configuration
├── requirements.txt                      # Dependencies
├── scripts/                              # Utility scripts
│   └── generate_secret.py                # Secret generator utility
├── src/
│   ├── assets/                           # Static assets
│   │   ├── logo.ico                      # Windows icon
│   │   └── logo.svg                      # Scalable logo
│   ├── backend_app.py                    # Backend application
│   ├── config.py                         # Configuration
│   ├── core/                             # Core application utilities
│   │   ├── errors.py                     # Fatal error handling
│   │   └── process.py                    # Process & shutdown management
│   ├── database.py                       # Database setup
│   ├── main.py                           # Entry point
│   ├── models.py                         # Data models
│   ├── routers/                          # FastAPI routers
│   │   ├── __init__.py                   # Package initialization
│   │   ├── ai.py                         # AI endpoints
│   │   ├── persons.py                    # Person endpoints
│   │   └── todos.py                      # Todo endpoints
│   ├── seed_data.py                      # Test data generator
│   ├── services/                         # Business logic
│   │   ├── ai_service.py                 # AI service
│   │   ├── person_service.py             # Person service
│   │   └── todo_service.py               # Todo service
│   └── ui/                               # Frontend components and pages
│       ├── api_client.py                 # Internal API Client
│       ├── components/                   # Reusable UI components
│       │   └── dialogs.py                # UI Dialogs
│       ├── controller.py                 # UI Controller (Logic & State)
│       ├── layout.py                     # Main layout wrapper
│       ├── pages/                        # Page content
│       │   ├── board.py                  # Board page
│       │   └── history.py                # History page
│       ├── routes.py                     # UI Page definitions
│       ├── theme.py                      # Theme management
│       └── translations.py               # Localization (EN/SV)
└── tests/                                # Automated tests
    ├── conftest.py                       # Fixtures & Reporting
    ├── test_ai_service_mock.py           # AI Mock tests
    ├── test_api_client.py                # Integration tests
    ├── test_core.py                      # Core utilities & process tests
    ├── test_core_utils.py                # App Initialization & Config tests
    ├── test_person_service.py            # Person CRUD tests
    ├── test_routers.py                   # API router integration tests
    ├── test_seed_data.py                 # DB mock data generation tests
    ├── test_services.py                  # Basic Unit tests
    ├── test_todo_service_extended.py     # Advanced Todo tests
    ├── test_ui_controller.py             # UI Controller tests
    ├── test_ui_dialogs.py                # UI Dialog tests
    ├── test_ui_history_serialization.py  # UI Serialization tests
    └── test_validation.py                # Data Model Validation tests
```

## Getting Started

### Prerequisites

-   Python 3.12+
-   Podman or Docker - *Optional, for containerized run*

### Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv .venv
    .venv\Scripts\activate  # Windows
    # source .venv/bin/activate # Linux/Mac
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

Create a `.env` file in the root directory (use `.env.example` as a template).

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | Database connection string | `sqlite:///todo.db` |
| `GEMINI_API_KEY` | API Key for AI features | `None` |
| `STORAGE_SECRET` | Secret for session encryption | `random_secret_for_session_encryption` |
| `PORT` | Local dev port | `8080` |

> **Tip:** To generate a secure `STORAGE_SECRET`, run `python scripts/generate_secret.py` and copy the output.

## Running the App

### Run with Podman/Docker

Build and start the container:
```bash
podman-compose up --build -d
```
```bash
docker-compose up --build -d
```
The app will be available at [http://localhost:8080](http://localhost:8080).

### Building as Executable (.exe)

To package the application as a standalone `.exe` file (Windows):

1.  **Run the Build Script**:
    ```bash
    python build.py
    ```
    This script will install `pyinstaller` (if missing) and package the app into the `dist/` folder.

2.  **Run the Executable**:
    Locate `dist/ToDoApp.exe` and run it. The database `todo.db` will be created in the same folder.

### Development Mode

Run the application directly with Python:
```bash
python -m src.main
```
The app will be available at [http://localhost:8080](http://localhost:8080).

## Testing & Data

This section covers how to run automated tests and seed the database with test data.

### Running Tests

The test suite includes:
- **Unit Tests**: Services, Models, API Client (Mocked), UI Controller (Mocked), and Core Utilities.
- **Integration Tests**: FastAPI endpoint edge cases and routing against an in-memory database.
- **Coverage Enforcement**: The test suite mandates strict code coverage testing (`pytest-cov > 68%`).
*A timestamped test report is generated in `tests/testreport/` after each run.*

To run the automated test suite using `pytest`:

**With Podman/Docker:**
```bash
podman-compose run --rm app pytest
```
```bash
docker-compose run --rm app pytest
```

**Locally:**
```bash
# Ensure test dependencies are installed
pip install -r requirements.txt
pytest
```

### Seeding Test Data

You can populate the database with mock data (sample persons and todos) for testing purposes.

**With Podman/Docker:**
```bash
podman-compose run --rm app python -m src.seed_data
```
```bash
docker-compose run --rm app python -m src.seed_data
```

**Locally:**
```bash
python -m src.seed_data
```

## Quick Links

-   **App**: [http://localhost:8080](http://localhost:8080)
-   **API JSON**: [http://localhost:8080/openapi.json](http://localhost:8080/openapi.json)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
