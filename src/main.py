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

    if os.environ.get("ENABLE_TEST_SHUTDOWN") == "1":

        @app.get("/internal/shutdown")
        def shutdown_test_server():
            import _thread
            import threading
            import time

            def _kill():
                time.sleep(0.5)
                # Terminate main thread properly so coverage 'atexit' triggers
                _thread.interrupt_main()

            threading.Thread(target=_kill, daemon=True).start()
            return {"status": "shutting down"}

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
        import socket
        import threading

        # Find an open port dynamically
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()

        args["native"] = False  # DO NOT use pywebview to avoid Python 3.14 crashes
        args["reload"] = False  # Critical for frozen apps
        args["port"] = port
        args["show"] = False  # PySide6 will handle window creation

        # Register atexit as safety net for process cleanup
        atexit.register(lambda: shutdown_cleanup(logger))

    # Only run the app if this is the main process
    if __name__ in {"__main__", "__mp_main__"}:
        if getattr(sys, "frozen", False):
            # Run NiceGUI/FastAPI in a background thread
            threading.Thread(target=ui.run, kwargs=args, daemon=True).start()

            # Initialize PySide6 UI on the main thread
            from PySide6.QtCore import QUrl
            from PySide6.QtWebEngineWidgets import QWebEngineView
            from PySide6.QtWidgets import QApplication, QMainWindow

            qt_app = QApplication(sys.argv)
            window = QMainWindow()
            window.setWindowTitle(settings.APP_NAME)

            web_view = QWebEngineView()
            web_view.load(QUrl(f"http://127.0.0.1:{args['port']}"))
            window.setCentralWidget(web_view)

            window.showMaximized()
            qt_app.exec()  # Block here until the user closes the PyQt Window

            # Ensure process terminates cleanly after UI closes
            shutdown_cleanup(logger)
            os._exit(0)
        else:
            ui.run(**args)

except KeyboardInterrupt:
    # Graceful exit for coverage and manual stops
    sys.exit(0)
except BaseException as e:
    handle_fatal_error(e)
