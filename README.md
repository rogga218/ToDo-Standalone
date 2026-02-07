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

## Quick Links

-   **App**: [http://localhost:8080](http://localhost:8080)
-   **API JSON**: [http://localhost:8080/openapi.json](http://localhost:8080/openapi.json)

## Project Structure

```
├── src/
│   ├── main.py            # Entry point
│   ├── config.py          # Configuration
│   ├── database.py        # Database setup
│   ├── models.py          # Data models
│   ├── services/          # Business logic (Person, Todo, AI)
│   ├── routers/           # FastAPI routers
│   └── ui/                # Frontend components and pages
│       ├── controller.py  # UI Controller (Logic & State)
│       └── theme.py       # Theme management
├── tests/                 # Automated tests
│   ├── conftest.py        # Fixtures
│   ├── test_services.py   # Unit tests
│   └── test_api_client.py # Integration tests
├── Dockerfile             # Container definition
├── docker-compose.yml     # Orchestration
├── requirements.txt       # Dependencies
└── .env                   # Configuration file
```

## Getting Started

### Prerequisites

-   Podman (or Docker)
-   Optional: Python 3.12+ for local development

### Run with Podman (or Docker)

1.  Build and start the container:
    ```bash
    podman-compose up --build -d
    ```

### Run Locally

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Run the application:
    ```bash
    python -m src.main
    ```
    
### Building as Executable (.exe)

To package the application as a standalone `.exe` file (Windows):

1.  **Run the Build Script**:
    ```bash
    python build.py
    ```
    This script will:
    -   Install `pyinstaller` (if missing).
    -   Package the application, dependencies, and assets.
    -   Use `src/assets/logo.png` as the icon (if present).

2.  **Locate the Executable**:
    The finished file will be in the `dist/` folder:
    ```
    dist/ToDoApp.exe
    ```

3.  **Distribute (Portable Mode)**:
    -   You can move `ToDoApp.exe` anywhere (USB stick, another folder, etc.).
    -   The database `todo.db` will be created **in the same folder** as the `.exe`.
    -   To back up your data, just copy `todo.db`.

**Note**: The first run might take a few seconds to extract temporary files.

## Configuration

Configuration is handled via `.env` file (or environment variables).

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | Database connection string | `sqlite:///todo.db` |
| `GEMINI_API_KEY` | API Key for AI features | `None` |
| `STORAGE_SECRET` | Secret for session encryption | `random_secret_for_session_encryption` |
| `PORT` | Local dev port | `8080` |

#### Generating a Secure Secret
To generate a secure `STORAGE_SECRET`, run the included helper script:
```bash
python generate_secret.py
```
Copy the output and paste it into your `.env` file.

## Testing

To run the automated tests, you can use `pytest`.

### Running with Podman
```bash
podman-compose run --rm app pytest
```
*Note: A timestamped test report (e.g., `tests/testreport/test_report_20240207_120000.txt`) will be generated after each run.*

### Running Locally
Ensure you have the test dependencies installed (`pytest`, `pytest-asyncio`, `httpx`).
```bash
pip install -r requirements.txt
pytest
```
