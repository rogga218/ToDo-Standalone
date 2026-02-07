import pytest
import pytest_asyncio
from sqlmodel import SQLModel, Session, create_engine
from typing import Generator
import os
from datetime import datetime

# Use an in-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest_asyncio.fixture(loop_scope="function")
async def async_client():
    # Since we don't have a full FastAPI app running in tests usually,
    # we might test services directly or use TestClient if we had a factory.
    # For this standalone app, we mainly test services and the ApiClient wrapper.
    pass


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Generate a timestamped test report file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = os.path.join("tests", "testreport")
    os.makedirs(report_dir, exist_ok=True)
    report_file = os.path.join(report_dir, f"test_report_{timestamp}.txt")

    # In a container, we want to write to a mounted volume if to be persistent.
    # The current working directory is /app, which might be ephemeral or mounted.
    # We'll write to the current directory.

    try:
        with open(report_file, "w") as f:
            f.write(f"Test Report - {timestamp}\n")
            f.write("=" * 30 + "\n")
            f.write(f"Exit Status: {exitstatus}\n")

            stats = terminalreporter.stats
            passed = len(stats.get("passed", []))
            failed = len(stats.get("failed", []))
            skipped = len(stats.get("skipped", []))
            error = len(stats.get("error", []))

            f.write(f"Passed: {passed}\n")
            f.write(f"Failed: {failed}\n")
            f.write(f"Skipped: {skipped}\n")
            f.write(f"Errors: {error}\n")
            f.write("=" * 30 + "\n")

            # List failed tests
            if failed > 0:
                f.write("\nFailures:\n")
                for report in stats.get("failed", []):
                    f.write(f"- {report.nodeid}\n")
                    # Optionally add failure message if available
                    if hasattr(report, "longreprtext"):
                        f.write(f"  {report.longreprtext}\n")

            # List errors
            if error > 0:
                f.write("\nErrors:\n")
                for report in stats.get("error", []):
                    f.write(f"- {report.nodeid}\n")
                    if hasattr(report, "longreprtext"):
                        f.write(f"  {report.longreprtext}\n")

            # List warnings
            warnings = stats.get("warnings", [])
            if warnings:
                f.write("\nWarnings:\n")
                for warning in warnings:
                    # Warning report object structure might vary, strictly print message
                    msg = getattr(warning, "message", str(warning))
                    f.write(f"- {msg}\n")
                    # Optionally add location if available
                    if hasattr(warning, "fslocation"):
                        f.write(f"  Location: {warning.fslocation}\n")

        print(f"\nTest report generated: {report_file}")
    except Exception as e:
        print(f"\nFailed to generate test report: {e}")
