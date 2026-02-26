import os
import sys


def init_crash_logging():
    """
    Polyfill for PyInstaller --windowed mode where sys.stdout/stderr are None.
    This prevents Uvicorn logging from crashing on 'isatty' checks.
    """
    if getattr(sys, "frozen", False):
        if sys.stdout is None:
            sys.stdout = open(os.devnull, "w")
        if sys.stderr is None:
            sys.stderr = open(os.devnull, "w")


def log_crash(e):
    """
    A unified crash logger that writes to a file when frozen as an executable,
    and displays a console message (or message box).
    """
    try:
        if getattr(sys, "frozen", False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        log_path = os.path.join(base_path, "crash.log")

        with open(log_path, "w") as f:
            import traceback

            traceback.print_exc(file=f)
            f.write(f"\nError: {e}")

        print(f"Crash log saved to: {log_path}")
    except Exception as log_err:
        print(f"Failed to write crash log: {log_err}")

    print("CRITICAL ERROR: Application failed to start.")
    import traceback

    traceback.print_exc()


def shutdown_cleanup(logger):
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
                logger.info(f"Terminating child process: {child.pid} ({child.name()})")
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
