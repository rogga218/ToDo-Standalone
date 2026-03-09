import os
import sys


def init_crash_logging():
    """
    Polyfill for PyInstaller --windowed mode where sys.stdout/stderr are None.
    This prevents Uvicorn logging from crashing on 'isatty' checks,
    and prevents multiprocessing spawn from failing with WinError 5 on sys.stdin.
    """
    if getattr(sys, "frozen", False):
        # We must use raw OS file descriptors so Windows DuplicateHandle doesn't crash Python
        # when multiprocessing spawn tries to inherit standard streams.
        null_fd = os.open(os.devnull, os.O_RDWR)

        if getattr(sys, "stdin", None) is None:
            sys.stdin = open(null_fd, "r", closefd=False)
        if getattr(sys, "stdout", None) is None:
            sys.stdout = open(null_fd, "w", closefd=False)
        if getattr(sys, "stderr", None) is None:
            sys.stderr = open(null_fd, "w", closefd=False)


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

        with open(log_path, "a") as f:
            import datetime
            import traceback

            f.write(f"\n--- Crash at {datetime.datetime.now()} in PID {os.getpid()} ---\n")
            traceback.print_exc(file=f)
            f.write(f"\nError: {e}\n")

        print(f"Crash log saved to: {log_path}")
    except Exception as log_err:
        print(f"Failed to write crash log: {log_err}")

    print("CRITICAL ERROR: Application failed to start.")
    import traceback

    traceback.print_exc()


_cleanup_done = False


def shutdown_cleanup(logger):
    """
    Kill the entire process tree to ensure no hanging processes after exit.
    Walks up the process tree to find the root ancestor with the same
    executable name (PyInstaller bootstrapper), then uses taskkill /F /T
    to forcefully terminate the entire tree.
    Guarded to only run once even if called from multiple shutdown hooks.
    """
    global _cleanup_done
    if _cleanup_done:
        return
    _cleanup_done = True

    import subprocess

    import psutil  # type: ignore

    try:
        logger.info("Performing shutdown cleanup...")
        current = psutil.Process()
        current_name = current.name().lower()

        # Walk up to find the root process of our app
        root = current
        try:
            parent = root.parent()
            while parent is not None and parent.pid > 0:
                if parent.name().lower() == current_name:
                    root = parent
                    parent = root.parent()
                else:
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        root_pid = root.pid
        logger.info(f"Root process: PID {root_pid} ({root.name()}). Killing entire process tree...")

        # taskkill /F /T kills the entire tree from the given PID (Windows)
        # CREATE_NO_WINDOW is Windows-only; use getattr for cross-platform safety
        subprocess.Popen(
            ["taskkill", "/F", "/T", "/PID", str(root_pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

        logger.info("Cleanup initiated.")
    except Exception as e:
        logger.error(f"Error during shutdown cleanup: {e}")
