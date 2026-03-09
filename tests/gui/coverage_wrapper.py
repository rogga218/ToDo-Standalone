import os
import threading
import time

import coverage

cov_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".coverage.guiserver"))
cov = coverage.Coverage(data_file=cov_file, source=["src"])
cov.start()

try:
    # Set the testing environment flag so the graceful shutdown endpoint is available
    os.environ["ENABLE_TEST_SHUTDOWN"] = "1"

    # Add project root to path so 'src' can be imported when script is run directly
    import sys

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

    # Import the main application
    from src.main import app, args, ui

    # We redefine the internal shutdown endpoint to guarantee it hits
    # _thread.interrupt_main() properly from within this wrapper scope
    @app.get("/wrapper_shutdown")
    def force_shutdown():
        def _kill():
            time.sleep(0.5)
            cov.stop()
            cov.save()
            print("COVERAGE SAVED BEFORE KILL", flush=True)
            os._exit(0)

        threading.Thread(target=_kill, daemon=True).start()
        return {"status": "shutting down wrapper"}

    # Run the application
    ui.run(**args)
except KeyboardInterrupt:
    pass
finally:
    # Ensure coverage is saved no matter how the process exits
    cov.stop()
    cov.save()
    print("Coverage data explicitly saved by wrapper.")
