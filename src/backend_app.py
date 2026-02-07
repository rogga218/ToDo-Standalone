from fastapi import FastAPI
from sqlmodel import Session, select
from fastapi.middleware.cors import CORSMiddleware

from src.database import engine, create_db_and_tables
from src.models import Person
from src.config import logger, get_settings

# Import routers
from src.routers import persons, todos, ai


def create_default_persons():
    with Session(engine) as session:
        # Check if we have persons, if not add defaults
        if not session.exec(select(Person)).first():
            session.add(Person(name="Roger"))
            session.add(Person(name="Bosse"))
            session.add(Person(name="Kalle"))
            session.commit()


# --- App Setup ---

app = FastAPI(title=get_settings().APP_NAME, debug=get_settings().DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev (Streamlit, React, etc.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    logger.info("--- LOADING REFACTORED APP (DI + CONFIG) ---")
    create_db_and_tables()
    create_default_persons()


# --- Include Routers ---
app.include_router(persons.router)
app.include_router(todos.router)
app.include_router(ai.router)
