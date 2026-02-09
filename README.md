# ToDo App (NiceGUI Standalone)

A modern, fast, and simple ToDo application built with **NiceGUI** and **SQLite**.

This project has been refactored to specificially focus on a single, native Python implementation, consolidating previous backend and frontend components into a unified structure.

## Features

-   **Native Python UI**: Built with [NiceGUI](https://nicegui.io).
-   **Integrated Backend**: Business logic runs directly within the application (no internal HTTP requests).
-   **SQLite Database**: Simple, file-based database for easy deployment.
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
├── src/
│   ├── main.py            # Entry point
│   ├── config.py          # Configuration
│   ├── database.py        # Database setup
│   ├── models.py          # Data models
│   ├── seed_data.py       # Test data generator
│   ├── services/          # Business logic (Person, Todo, AI)
│   ├── routers/           # FastAPI routers
│   └── ui/                # Frontend components and pages
│       ├── controller.py  # UI Controller (Logic & State)
│       ├── layout.py      # Main layout wrapper
│       ├── theme.py       # Theme management
│       ├── translations.py# Localization (EN/SV)
│       ├── api_client.py  # Internal API Client
│       ├── components/    # Reusable UI components (Dialogs, etc.)
│       └── pages/         # Page content (Board, History)
├── tests/                 # Automated tests
│   ├── conftest.py        # Fixtures & Reporting
│   ├── test_services.py   # Basic Unit tests
│   ├── test_person_service.py # Person CRUD tests
│   ├── test_todo_service_extended.py # Advanced Todo tests
│   ├── test_ai_service_mock.py # AI Mock tests
│   ├── test_api_client.py # Integration tests
│   └── test_validation.py # Data Model Validation tests
├── Dockerfile             # Container definition
├── docker-compose.yml     # Orchestration
├── requirements.txt       # Dependencies
├── build.py               # Build script (PyInstaller)
├── generate_secret.py     # Secret generator utility
└── .env                   # Configuration file
```

## Getting Started

### Prerequisites

-   Python 3.12+
-   Podman (or Docker) - *Optional, for containerized run*

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

> **Tip:** To generate a secure `STORAGE_SECRET`, run `python generate_secret.py` and copy the output.

## Running the App

### Development Mode

Run the application directly with Python:
```bash
python -m src.main
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

### Run with Podman/Docker

Build and start the container:
```bash
podman-compose up --build -d
```

## Testing & Data

This section covers how to run automated tests and seed the database with test data.

### Running Tests

To run the automated test suite using `pytest`:

**Locally:**
```bash
# Ensure test dependencies are installed
pip install -r requirements.txt
pytest
```

**With Podman:**
```bash
podman-compose run --rm app pytest
```
*A timestamped test report is generated in `tests/testreport/` after each run.*

### Seeding Test Data

You can populate the database with mock data (sample persons and todos) for testing purposes.

**Locally:**
```bash
python -m src.seed_data
```

**With Podman:**
```bash
podman-compose run --rm app python -m src.seed_data
```

## Quick Links

-   **App**: [http://localhost:8080](http://localhost:8080)
-   **API JSON**: [http://localhost:8080/openapi.json](http://localhost:8080/openapi.json)
