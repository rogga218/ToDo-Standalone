import sys
import os

# Polyfill for PyInstaller --windowed mode where sys.stdout/stderr are None
# This prevents Uvicorn logging from crashing on 'isatty' checks.
if getattr(sys, "frozen", False):
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")


# Crash Logger
def log_crash(e):
    try:
        # Write to app directory (dist/ when frozen)
        if getattr(sys, "frozen", False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        log_path = os.path.join(base_path, "crash.log")

        with open(log_path, "w") as f:
            import traceback

            traceback.print_exc(file=f)
            f.write(f"\nError: {e}")

        print(f"Crash log saved to: {log_path}")
    except Exception as log_err:
        print(f"Failed to write crash log: {log_err}")

    # Always print to console and pause
    print("CRITICAL ERROR: Application failed to start.")
    import traceback

    traceback.print_exc()
    print("\nPress Enter to close this window...")
    input()


try:
    from nicegui import ui, app
    from src.database import create_db_and_tables, engine
    from src.routers import persons, todos, ai
    from src.models import Person
    from src.config import get_settings
    from src.ui.controller import ToDoController
    from src.ui.theme import inject_dark_mode_script
    from sqlmodel import Session, select

    # --- Backend Setup ---

    # Include Routers (API)
    app.include_router(persons.router)
    app.include_router(todos.router)
    app.include_router(ai.router)

    def create_default_persons():
        with Session(engine) as session:
            if not session.exec(select(Person)).first():
                session.add(Person(name="Roger"))
                session.add(Person(name="Bosse"))
                session.add(Person(name="Kalle"))
                session.commit()

    @app.on_startup
    def on_startup():
        create_db_and_tables()
        create_default_persons()

    # -- UI Logic --

    @ui.page("/")
    def index():
        inject_dark_mode_script()
        ui.navigate.to("/board")

    @ui.page("/board")
    async def board_page(page: int = 0):
        try:
            inject_dark_mode_script()
            # Initialize data if empty (first load) or just refresh?
            # Ideally controller manages its life cycle.
            # We call initialize to ensure data is fresh on page load.
            controller = ToDoController()
            await controller.initialize()
            await controller.render_layout("board", page)
        except Exception as e:
            ui.label(f"Error loading page: {e}").classes("text-red-500")
            print(f"Error: {e}")

    @ui.page("/history")
    async def history_page():
        try:
            inject_dark_mode_script()
            inject_dark_mode_script()
            controller = ToDoController()
            await controller.initialize()
            await controller.render_layout("history")
        except Exception as e:
            ui.label(f"Error loading page: {e}").classes("text-red-500")
            print(f"Error: {e}")

    settings = get_settings()
    app.add_static_files("/assets", settings.get_assets_path())

    # Run Configuration
    args = {
        "title": settings.APP_NAME,
        "port": settings.PORT,
        "dark": True,
        "storage_secret": settings.STORAGE_SECRET,
    }

    # Native Mode settings for Executable
    if getattr(sys, "frozen", False):
        args["native"] = True
        args["reload"] = False  # Critical for frozen apps
        args["window_size"] = (1200, 800)
        args["fullscreen"] = False
        args["port"] = None  # Let NiceGUI pick a random free port

    ui.run(**args)

except BaseException as e:
    # Catch SystemExit and others to ensure we see what happened
    if isinstance(e, SystemExit) and e.code == 0:
        # Normal exit, don't log as crash
        sys.exit(0)

    log_crash(e)

    # In windowed mode (frozen), show a popup box because there starts no console
    if getattr(sys, "frozen", False):
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(
                0,
                f"Critical Error:\n{e}\n\nSee crash.log for details.",
                "ToDo App Failure",
                0x10 | 0x1000,  # MB_ICONHAND | MB_SYSTEMMODAL (force to top)
            )
        except Exception:
            pass
    else:
        print(f"CRITICAL ERROR: {e}")
        import traceback

        traceback.print_exc()
        # Only pause if not running in IDE/Service
        if sys.stdin and sys.stdin.isatty():
            print("\nPress Enter to close this window...")
            input()

    sys.exit(1)
