import sys
from src.core.process import log_crash


def handle_fatal_error(e):
    """
    Shows a generic dialog or terminal trace upon fatal crash.
    """
    if isinstance(e, SystemExit) and e.code == 0:
        sys.exit(0)

    log_crash(e)

    if getattr(sys, "frozen", False):
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(
                0,
                f"Critical Error:\n{e}\n\nSee crash.log for details.",
                "ToDo App Failure",
                0x10 | 0x1000,
            )
        except Exception:
            pass
    else:
        print(f"CRITICAL ERROR: {e}")
        import traceback

        traceback.print_exc()
        if sys.stdin and sys.stdin.isatty():
            print("\nPress Enter to close this window...")
            input()

    sys.exit(1)
