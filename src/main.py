import sys
import os

from src.core.process import init_crash_logging, shutdown_cleanup
from src.core.errors import handle_fatal_error

# Polyfill for PyInstaller --windowed mode where sys.stdout/stderr are None
init_crash_logging()

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
    from sqlmodel import Session, select

    from src.ui.routes import setup_routes

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

    @app.on_shutdown
    def on_shutdown():
        # Only cleanup if running as an executable
        if getattr(sys, "frozen", False):
            logger.info("Shutting down Application...")
            shutdown_cleanup(logger)
            # Force exit to ensure no lingering threads keep the process alive
            os._exit(0)

    # -- UI Logic --
    setup_routes()

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
            shutdown_cleanup(logger)
            os._exit(0)


except BaseException as e:
    handle_fatal_error(e)
