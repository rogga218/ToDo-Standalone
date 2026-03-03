import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI

from src.backend_app import create_default_persons, lifespan
from src.config import Settings
from src.database import get_session


# -----------------
# 1. Config Tests
# -----------------
def test_config_frozen_path():
    settings = Settings()

    # Mock sys.frozen and sys.executable
    with (
        patch("sys.frozen", True, create=True),
        patch("sys.executable", "/fake/exec/path/app.exe"),
    ):
        db_url = settings.get_db_url()
        # Verify it resolves database to the executable's directory
        expected_path = os.path.join(
            "/fake/exec/path", settings.SQLITE_FILE_NAME
        ).replace("\\", "/")
        # Cross platform SQLite URL normalization
        assert expected_path in db_url.replace("\\", "/")


def test_config_frozen_assets():
    settings = Settings()

    # Mock sys.frozen and sys._MEIPASS
    with (
        patch("sys.frozen", True, create=True),
        patch("sys._MEIPASS", "/tmp/meipass_fake", create=True),
    ):
        assets_path = settings.get_assets_path()
        assert "meipass_fake" in assets_path
        assert assets_path.endswith("assets")


def test_config_frozen_env_fallback():
    # Simulate being frozen but the primary .env is missing.
    with (
        patch("sys.frozen", True, create=True),
        patch("os.path.exists", return_value=False),
        patch("os.path.join") as mock_join,
    ):
        settings = Settings()
        assert settings.get_db_url() is not None
        # It should have called os.path.join to find the fallback
        mock_join.assert_called()


# -----------------
# 2. Database Tests
# -----------------
def test_get_session_yields():
    # Test the raw generator function in database.py
    # We just want to ensure it iterates without crashing using a mock engine
    with patch("src.database.Session") as mock_session_class:
        mock_instance = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_instance

        gen = get_session()
        session = next(gen)

        assert session == mock_instance

        # Stop iteration gracefully
        try:
            next(gen)
        except StopIteration:
            pass

        mock_session_class.assert_called_once()


# -----------------
# 3. Backend App Tests
# -----------------
def test_create_default_persons():
    with patch("src.backend_app.Session") as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session

        # Simulate an empty database (no users found)
        mock_session.exec.return_value.first.return_value = None

        create_default_persons()

        # We expect 3 people to be created (Roger, Bosse, Kalle)
        assert mock_session.add.call_count == 3
        mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_backend_lifespan():
    dummy_app = FastAPI()

    # Patch the real DB and initializers so we don't nuke actual files
    with (
        patch("src.backend_app.create_db_and_tables") as mock_create_db,
        patch("src.backend_app.create_default_persons") as mock_create_users,
    ):
        # Execute the async context manager
        async with lifespan(dummy_app):
            pass

        # Verify it initialized the core dependencies
        mock_create_db.assert_called_once()
        mock_create_users.assert_called_once()
