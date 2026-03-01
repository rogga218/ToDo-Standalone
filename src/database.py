from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from src.config import get_settings, logger

settings = get_settings()

# Database Setup
database_url = settings.get_db_url()
logger.info(f"Database URL: {database_url}")

connect_args = {"check_same_thread": False} if "sqlite" in database_url else {}
engine = create_engine(database_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependency for getting a database session."""
    with Session(engine) as session:
        yield session
