import os
import sys

from src.core.errors import handle_fatal_error
from src.core.process import init_crash_logging, shutdown_cleanup

# Polyfill for PyInstaller --windowed mode where sys.stdout/stderr are None
init_crash_logging()

try:
    # 1. Critical for PyInstaller on Windows to prevent infinite process spawning
    # Must be called before importing nicegui or anything else that uses multiprocessing
    from multiprocessing import freeze_support

    if __name__ in {"__main__", "__mp_main__"}:
        freeze_support()

    from nicegui import app, ui
    from sqlmodel import Session, select

    from src.config import get_settings, logger
    from src.database import create_db_and_tables, engine
    from src.models import Person
    from src.routers import ai, persons, todos
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
        import atexit

        args["native"] = True
        args["reload"] = False  # Critical for frozen apps
        args["port"] = None  # type: ignore # Let NiceGUI pick a random free port

        @app.on_startup
        def setup_native_window():
            """Maximize window and start shutdown watchdog after startup."""
            import asyncio

            async def _do_maximize():
                await asyncio.sleep(0.5)
                try:
                    app.native.main_window.maximize()  # type: ignore[union-attr]
                except Exception:
                    pass

            asyncio.get_event_loop().create_task(_do_maximize())

            # Start a watchdog that monitors pywebview windows directly.
            # This is independent of NiceGUI's event system which can be
            # unreliable for on_shutdown in native mode.
            import threading
            import time

            def _shutdown_watchdog():
                try:
                    import webview  # pywebview's module

                    # Phase 1: Wait for window(s) to be created
                    timeout = 30  # Max wait for window creation
                    elapsed = 0.0
                    while not webview.windows and elapsed < timeout:
                        time.sleep(0.5)
                        elapsed += 0.5

                    if not webview.windows:
                        return  # No window was ever created, abort

                    # Phase 2: Wait for all windows to close
                    while webview.windows:
                        time.sleep(0.5)
                except Exception:
                    return

                # All pywebview windows are gone — force cleanup
                time.sleep(1)  # Brief grace period
                shutdown_cleanup(logger)
                os._exit(0)

            threading.Thread(target=_shutdown_watchdog, daemon=True, name="shutdown-watchdog").start()

        # Register atexit as safety net for process cleanup
        atexit.register(lambda: shutdown_cleanup(logger))

    # Only run the app if this is the main process
    if __name__ in {"__main__", "__mp_main__"}:
        ui.run(**args)

        # Ensure process terminates after UI closes
        if getattr(sys, "frozen", False):
            shutdown_cleanup(logger)
            os._exit(0)


except BaseException as e:
    handle_fatal_error(e)
