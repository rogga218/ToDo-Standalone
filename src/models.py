import uuid
from datetime import date, timedelta, datetime, timezone
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, DateTime
from pydantic import field_validator, ConfigDict


def get_default_deadline():
    return date.today() + timedelta(days=7)


# --- Person Models ---


class PersonBase(SQLModel):
    # Regex: No digits allowd (\D matchar icke-siffror), min length 2
    # Vi kan inte fånga allt med regex (t.ex. strip), men detta hjälper API-docs och tester.
    name: str = Field(
        index=True,
        unique=True,
        min_length=2,
        max_length=50,
        # Regex: Whitelist - Start with letter, No trailing space
        schema_extra={
            "pattern": r"^[a-zA-Z\u00C0-\u00FF][a-zA-Z\u00C0-\u00FF \-\']*[a-zA-Z\u00C0-\u00FF]$"
        },
    )

    model_config = ConfigDict(extra="forbid")


class Person(PersonBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    todos: List["Todo"] = Relationship(back_populates="person")


class PersonCreate(PersonBase):
    @field_validator("name", mode="before")
    def validate_name_clean(cls, v):
        if not isinstance(v, str):
            raise ValueError("Namnet måste vara en textsträng")

        # 1. Strip whitespace
        v = v.strip()

        # 2. Length check (minimum 2 chars)
        if len(v) < 2:
            raise ValueError("Namnet måste vara minst 2 tecken långt")

        # 3. Whitelist check (Strict)
        # Allows: Letters, Spaces, Hyphens, Apostrophes.
        # Must start with a letter.
        # \u00C0-\u00FF covers common accented characters (Latin-1 Supplement)
        import re

        pattern = r"^[a-zA-Z\u00C0-\u00FF][a-zA-Z\u00C0-\u00FF \-\']+$"

        if not re.match(pattern, v):
            raise ValueError(
                "Namnet innehåller ogiltiga tecken (Tillåtna: bokstäver, mellanslag, bindestreck, apostrofer)"
            )

        return v


class PersonRead(PersonBase):
    id: uuid.UUID


# --- Todo Models ---


# --- Subtask Models ---


class SubtaskBase(SQLModel):
    title: str
    completed: bool = False


class Subtask(SubtaskBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    todo_id: uuid.UUID = Field(foreign_key="todo.id")
    todo: "Todo" = Relationship(back_populates="subtasks")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )


class SubtaskCreate(SubtaskBase):
    todo_id: uuid.UUID


class SubtaskRead(SubtaskBase):
    id: uuid.UUID
    todo_id: uuid.UUID
    created_at: datetime


# --- Todo Models ---


# Bas-modell med gemensamma fält
class TodoBase(SQLModel):
    title: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=500)  # Obligatorisk nu
    completed: bool = False
    priority: int = Field(default=2, ge=1, le=3)  # 1=High, 2=Medium, 3=Low
    deadline: date = Field(default_factory=get_default_deadline)
    person_id: uuid.UUID = Field(foreign_key="person.id")  # Foreign Key

    model_config = ConfigDict(extra="forbid")


# Tabell-modell (inkluderar ID)
class Todo(TodoBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    person: Optional[Person] = Relationship(back_populates="todos")
    subtasks: List["Subtask"] = Relationship(back_populates="todo", cascade_delete=True)


# Modell för att skapa
class TodoCreate(TodoBase):
    @field_validator("title", mode="before")
    def validate_title_type(cls, v):
        if not isinstance(v, str):
            raise ValueError("Titeln måste vara en textsträng")
        return v

    @field_validator("deadline", mode="before")
    def validate_deadline_type(cls, v):
        if v is not None and not isinstance(v, (str, date)):
            raise ValueError("Deadline måste vara en textsträng eller ett datum")
        return v


# Modell för att läsa (inkluderar ID)
class TodoRead(TodoBase):
    id: uuid.UUID
    subtasks: List[SubtaskRead] = []


# Modell för uppdatering (alla fält valfria)
class TodoUpdate(SQLModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, min_length=1, max_length=500)
    completed: Optional[bool] = None
    person_id: Optional[uuid.UUID] = None
    priority: Optional[int] = Field(default=None, ge=1, le=3)
    deadline: Optional[date] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("deadline", mode="before")
    def validate_deadline_type(cls, v):
        # v can be None here if strictly passing null, but we'll filter it out later
        if v is not None and not isinstance(v, (str, date)):
            raise ValueError("Deadline måste vara en textsträng eller ett datum")
        return v

    @field_validator("priority")
    def validate_priority(cls, v):
        if v is not None and (v < 1 or v > 3):
            raise ValueError("Prioritet måste vara mellan 1 och 3")
        return v
