import os
import subprocess
import sys
import time
from typing import Generator

import httpx
import pytest
from sqlmodel import SQLModel, create_engine

db_path = "test_gui_todo.db"
TEST_DATABASE_URL = f"sqlite:///{db_path}"


@pytest.fixture(scope="session", autouse=True)
def gui_app_server() -> Generator[str, None, None]:
    """Start the NiceGUI app in a subprocess for GUI testing."""

    # 1. Setup Database
    engine = create_engine(TEST_DATABASE_URL)
    SQLModel.metadata.create_all(engine)

    port = 8081
    host = "127.0.0.1"
    base_url = f"http://{host}:{port}"

    # 2. Start the server in a clean subprocess
    env = os.environ.copy()
    # Strip pytest variables so NiceGUI doesn't try to use its custom testing implementation
    for k in list(env.keys()):
        if k.startswith("PYTEST_"):
            del env[k]

    env["DATABASE_URL"] = TEST_DATABASE_URL
    env["PORT"] = str(port)
    env["DEBUG"] = "False"  # Ensure no auto-reload in tests

    env["ENABLE_TEST_SHUTDOWN"] = "1"

    # We use a dedicated wrapper script to guarantee coverage is tracked and saved
    cmd = [sys.executable, os.path.join("tests", "gui", "coverage_wrapper.py")]

    # We use subprocess instead of multiprocessing to avoid Windows spawn bombs with pytest
    process = subprocess.Popen(cmd, env=env, stdin=subprocess.PIPE, text=True)

    # 3. Wait for the server to be ready
    max_retries = 50
    for _ in range(max_retries):
        try:
            response = httpx.get(f"{base_url}/health", timeout=1.0)
            if response.status_code == 200:
                break
        except Exception:
            pass

        if process.poll() is not None:
            # Process crashed
            out, _ = process.communicate()
            raise RuntimeError(f"Server subprocess crashed before readiness:\n{out}")

        time.sleep(0.2)
    else:
        process.terminate()
        process.wait()
        raise RuntimeError("Failed to start the test server process (timeout)")

    # 4. Yield the base URL to the tests
    yield base_url

    # 5. Teardown
    try:
        httpx.get(f"{base_url}/wrapper_shutdown", timeout=2.0)
    except Exception:
        pass

    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()

    SQLModel.metadata.drop_all(engine)
    engine.dispose()

    # Clean up the test database file
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass
