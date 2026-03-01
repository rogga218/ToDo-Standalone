# Contributing to ToDo App

First off, thank you for considering contributing to the ToDo App! It's people like you that make such tools great.

## Development Setup

To set up your local development environment, please follow these steps:

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-username>/ToDo-Standalone.git
   cd ToDo-Standalone
   ```

2. **Create a virtual environment and activate it**
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # Linux/macOS
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Copy the example environment file and fill in your details (like the `GEMINI_API_KEY` if you plan to work on the AI features).
   ```bash
   cp .env.example .env
   ```

## Workflow

1. **Create a branch**: Branch off from `main` for your work. Use a descriptive name like `feature/add-dark-mode` or `fix/button-styling`.
2. **Make your changes**: Implement your shiny new feature or bug fix.
   - **Important**: This project adheres to a "Zero-Warning Policy" for IDE diagnostics. Please ensure your code doesn't introduce any new warnings.
   - We use Python type hints heavily, please include them in new functions.
3. **Run tests & linters**: Ensure you haven't broken anything.
   ```bash
   ruff format src
   ruff check src
   mypy src
   pytest
   ```
   *(Note: The project requires a minimum test coverage of 65% and 0 warnings.)*
4. **Commit your changes**: Write clear, descriptive commit messages.
5. **Push and open a PR**: Push your branch to GitHub and open a Pull Request against the `main` branch.

## Code Style & Standards

- **Language:** Code and comments should be in English. The UI is in Swedish.
- **Python Style:** Follow PEP 8 guidelines.
- **Architecture:** Maintain Separation of Concerns (SoC). UI logic goes in `src/ui`, business logic in `src/services`, data access in `src/database.py` and models in `src/models.py`.

## Getting Help

If you have questions, feel free to open a "Question" issue, or reach out to the maintainers directly.
