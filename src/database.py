from typing import Generator

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine, select

from src.config import get_settings, logger
from src.models import Person

settings = get_settings()

# Database Setup
database_url = settings.get_db_url()
logger.info(f"Database URL: {database_url}")

connect_args = {"check_same_thread": False} if "sqlite" in database_url else {}
engine = create_engine(database_url, connect_args=connect_args)

if "sqlite" in database_url:

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def create_default_persons():
    with Session(engine) as session:
        if not session.exec(select(Person)).first():
            logger.info("Seeding default persons...")
            session.add(Person(name="TestPerson1"))
            session.add(Person(name="TestPerson2"))
            session.add(Person(name="TestPerson3"))
            session.commit()


def get_session() -> Generator[Session, None, None]:
    """Dependency for getting a database session."""
    with Session(engine) as session:
        yield session
