from sqlmodel import Session

from src.models import PersonCreate, SubtaskCreate, TodoCreate
from src.services import person_service, todo_service


def test_get_todos_filtering(session: Session):
    # Setup
    p1 = person_service.create_person(session, PersonCreate(name="PersonOne"))
    p2 = person_service.create_person(session, PersonCreate(name="PersonTwo"))

    todo_service.create_todo(session, TodoCreate(title="T1", description="D1", person_id=p1.id, priority=1))
    todo_service.create_todo(session, TodoCreate(title="T2", description="D2", person_id=p1.id, priority=2))
    todo_service.create_todo(session, TodoCreate(title="T3", description="D3", person_id=p2.id, priority=1))

    # Filter by person
    todos_p1 = todo_service.get_todos(session, filter_person_id=p1.id)
    assert len(todos_p1) == 2

    # Filter by priority
    todos_prio1 = todo_service.get_todos(session, filter_priority=1)
    assert len(todos_prio1) == 2

    # Filter by both
    todos_combined = todo_service.get_todos(session, filter_person_id=p1.id, filter_priority=1)
    assert len(todos_combined) == 1
    assert todos_combined[0].title == "T1"


def test_subtask_lifecycle(session: Session):
    p = person_service.create_person(session, PersonCreate(name="SubtaskUser"))
    todo = todo_service.create_todo(session, TodoCreate(title="Parent", description="Desc", person_id=p.id))

    # Create Subtask
    st = todo_service.create_subtask(session, SubtaskCreate(title="Sub1", todo_id=todo.id))
    assert st.id is not None
    assert st.todo_id == todo.id
    assert st.completed is False

    # Verify linkage
    refreshed_todo = todo_service.get_todo(session, todo.id)
    assert refreshed_todo is not None
    assert len(refreshed_todo.subtasks) == 1
    assert refreshed_todo.subtasks[0].id == st.id

    # Update Subtask
    updated_st = todo_service.update_subtask(session, st.id, completed=True)
    assert updated_st.completed is True

    # Delete Subtask
    todo_service.delete_subtask(session, st.id)

    # Verify deletion
    refreshed_todo_2 = todo_service.get_todo(session, todo.id)
    assert refreshed_todo_2 is not None
    assert len(refreshed_todo_2.subtasks) == 0


def test_delete_todo_cascades_subtasks(session: Session):
    p = person_service.create_person(session, PersonCreate(name="CascadeUser"))
    todo = todo_service.create_todo(session, TodoCreate(title="Parent", description="Desc", person_id=p.id))
    st = todo_service.create_subtask(session, SubtaskCreate(title="Child", todo_id=todo.id))

    # Delete Todo
    todo_service.delete_todo(session, todo.id)

    # Verify Todo is gone
    assert todo_service.get_todo(session, todo.id) is None

    # Verify Subtask is gone (cascade) using direct session query as service doesn't have get_subtask
    from src.models import Subtask

    assert session.get(Subtask, st.id) is None
