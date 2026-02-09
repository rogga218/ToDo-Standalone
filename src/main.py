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
    # 1. Critical for PyInstaller on Windows to prevent infinite process spawning
    # Must be called before importing nicegui or anything else that uses multiprocessing
    from multiprocessing import freeze_support

    if __name__ in {"__main__", "__mp_main__"}:
        freeze_support()

    from nicegui import ui, app
    from src.database import create_db_and_tables, engine
    from src.routers import persons, todos, ai
    from src.models import Person
    from src.config import get_settings, logger
    from src.ui.controller import ToDoController
    from src.ui.theme import inject_dark_mode_script
    from sqlmodel import Session, select

    # --- Backend Setup ---

    # Include Routers (API)
    app.include_router(persons.router)
    app.include_router(todos.router)
    app.include_router(ai.router)

    # Health Check
    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    def create_default_persons():
        with Session(engine) as session:
            if not session.exec(select(Person)).first():
                logger.info("Seeding default persons...")
                session.add(Person(name="TestPerson1"))
                session.add(Person(name="TestPerson2"))
                session.add(Person(name="TestPerson3"))
                session.commit()

    @app.on_startup
    def on_startup():
        logger.info("Starting ToDo App...")
        create_db_and_tables()
        create_default_persons()

    def shutdown_cleanup():
        """
        Kill all child processes to ensure no hanging processes after exit.
        """
        import psutil  # type: ignore

        try:
            logger.info("Performing shutdown cleanup...")
            current_process = psutil.Process()
            children = current_process.children(recursive=True)

            for child in children:
                try:
                    logger.info(
                        f"Terminating child process: {child.pid} ({child.name()})"
                    )
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass

            # Wait for termination
            _, alive = psutil.wait_procs(children, timeout=3)

            for p in alive:
                try:
                    logger.warning(f"Killing stubborn process: {p.pid} ({p.name()})")
                    p.kill()
                except psutil.NoSuchProcess:
                    pass

            logger.info("Cleanup complete.")
        except Exception as e:
            logger.error(f"Error during shutdown cleanup: {e}")

    @app.on_shutdown
    def on_shutdown():
        # Only cleanup if running as an executable
        if getattr(sys, "frozen", False):
            logger.info("Shutting down Application...")
            shutdown_cleanup()
            # Force exit to ensure no lingering threads keep the process alive
            os._exit(0)

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
            logger.error(f"Error loading board page: {e}")
            ui.label(f"Error loading page: {e}").classes("text-red-500")

    @ui.page("/history")
    async def history_page():
        try:
            inject_dark_mode_script()
            controller = ToDoController()
            await controller.initialize()
            await controller.render_layout("history")
        except Exception as e:
            logger.error(f"Error loading history page: {e}")
            ui.label(f"Error loading page: {e}").classes("text-red-500")

    settings = get_settings()
    app.add_static_files("/assets", settings.get_assets_path())

    # Run Configuration
    args = {
        "host": "0.0.0.0",  # Bind to all interfaces for Docker compatibility
        "port": settings.PORT,
        "title": settings.APP_NAME,
        "dark": True,
        "storage_secret": settings.STORAGE_SECRET,
        "reload": settings.DEBUG,  # Enable auto-reload in debug mode
        "show": False,  # Don't try to open browser in container
    }

    # Native Mode settings for Executable
    if getattr(sys, "frozen", False):
        args["native"] = True
        args["reload"] = False  # Critical for frozen apps
        args["window_size"] = (1200, 800)  # type: ignore
        args["fullscreen"] = False
        args["port"] = None  # type: ignore # Let NiceGUI pick a random free port

    # Only run the app if this is the main process
    if __name__ in {"__main__", "__mp_main__"}:
        ui.run(**args)

        # Ensure process terminates after UI closes
        if getattr(sys, "frozen", False):
            shutdown_cleanup()
            os._exit(0)


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
