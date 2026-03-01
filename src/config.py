import logging
import sys
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# Create a logger for the application
logger = logging.getLogger("todo_app")


class Settings(BaseSettings):
    """
    Application Settings
    Reads from environment variables or .env file.
    """

    # App Config
    APP_NAME: str = "ToDo App"
    DEBUG: bool = False

    # Database
    DATABASE_URL: Optional[str] = None
    SQLITE_FILE_NAME: str = "todo.db"

    # AI Config
    GEMINI_API_KEY: Optional[str] = None

    # Security & Network
    STORAGE_SECRET: str = "antigravity_secret"
    PORT: int = 8080

    # Pydantic Settings Config
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore")

    def get_db_url(self) -> str:
        """
        Returns the database URL.
        If running as a frozen executable (PyInstaller), places the DB in the user's data directory.
        Otherwise uses the configured DATABASE_URL or defaults to local sqlite file.
        """
        if getattr(sys, "frozen", False):
            # Running as PyInstaller Bundle
            import os

            # Portable Mode: Database in the same directory as the executable
            base_path = os.path.dirname(sys.executable)
            db_path = os.path.join(base_path, self.SQLITE_FILE_NAME)
            return f"sqlite:///{db_path}"

        # Development / Docker
        return self.DATABASE_URL or f"sqlite:///{self.SQLITE_FILE_NAME}"

    def get_assets_path(self) -> str:
        """
        Returns the absolute path to the assets directory.
        Handles PyInstaller's sys._MEIPASS temporary directory.
        """
        import os

        if getattr(sys, "frozen", False):
            # PyInstaller unpacks data to sys._MEIPASS
            base_path = getattr(sys, "_MEIPASS", os.getcwd())
        else:
            # Normal python execution
            base_path = os.getcwd()

        return os.path.join(base_path, "src", "assets")


@lru_cache
def get_settings():
    """
    Cached settings getter.
    """
    return Settings()


# --- Logging Setup ---
# Load settings to determine log level
settings = get_settings()
log_level = logging.DEBUG if settings.DEBUG else logging.INFO

# Configure standard logging format
# Configure standard logging format
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
