from unittest.mock import patch


def test_person_routes(client):
    # Create Person
    response = client.post("/persons/", json={"name": "Router Person"})
    assert response.status_code == 200
    person_id = response.json()["id"]

    # Get Persons
    response = client.get("/persons/")
    assert response.status_code == 200
    persons = response.json()
    assert len(persons) == 1
    assert persons[0]["name"] == "Router Person"

    # Delete Person
    response = client.delete(f"/persons/{person_id}")
    assert response.status_code == 204

    # Verify Delete
    response = client.get("/persons/")
    assert len(response.json()) == 0

    # Error: Delete non-existent
    response = client.delete("/persons/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404

    # Error: Unknown query param
    response = client.get("/persons/?invalid_param=true")
    assert response.status_code == 422

    # Error: Delete person with assigned tools
    # We must quickly create a person and a todo
    p_res = client.post("/persons/", json={"name": "Owner"})
    p_id = p_res.json()["id"]
    client.post("/todos/", json={"title": "Test", "description": "Desc", "person_id": p_id})
    del_res = client.delete(f"/persons/{p_id}")
    assert del_res.status_code == 400


def test_person_routes_exceptions(client):
    with patch("src.routers.persons.person_service.create_person") as mock_create:
        mock_create.side_effect = Exception("DB failure")
        response = client.post("/persons/", json={"name": "Fail"})
        assert response.status_code == 500

    with patch("src.routers.persons.person_service.delete_person") as mock_delete:
        mock_delete.side_effect = Exception("DB failure")
        response = client.delete("/persons/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 500


def test_todo_routes(client):
    # Setup Person
    p_res = client.post("/persons/", json={"name": "Todo Owner"})
    p_id = p_res.json()["id"]

    # Create Todo
    t_res = client.post(
        "/todos/",
        json={"title": "Test Todo", "description": "Test Desc", "person_id": p_id},
    )
    assert t_res.status_code == 200
    t_id = t_res.json()["id"]

    # Get Todos
    get_res = client.get("/todos/")
    assert get_res.status_code == 200
    assert len(get_res.json()) == 1

    # Get specific Todo
    get_t_res = client.get(f"/todos/{t_id}")
    assert get_t_res.status_code == 200
    assert get_t_res.json()["title"] == "Test Todo"

    # Update Todo
    u_res = client.patch(f"/todos/{t_id}", json={"completed": True})
    assert u_res.status_code == 200
    assert u_res.json()["completed"] is True

    # Delete Todo
    d_res = client.delete(f"/todos/{t_id}")
    assert d_res.status_code == 200

    # Error: Delete non-existent
    d_err = client.delete("/todos/00000000-0000-0000-0000-000000000000")
    assert d_err.status_code == 404

    # Error: Get non-existent
    g_err = client.get("/todos/00000000-0000-0000-0000-000000000000")
    assert g_err.status_code == 404

    # Error: Path non-existent
    p_err = client.patch("/todos/00000000-0000-0000-0000-000000000000", json={"completed": True})
    assert p_err.status_code == 404


def test_subtask_routes(client):
    # Setup
    p_res = client.post("/persons/", json={"name": "Subtask Owner"})
    p_id = p_res.json()["id"]
    t_res = client.post(
        "/todos/",
        json={"title": "T", "description": "D", "person_id": p_id},
    )
    t_id = t_res.json()["id"]

    # Create Subtask
    s_res = client.post("/subtasks/", json={"title": "Sub 1", "todo_id": t_id})
    assert s_res.status_code == 200
    s_id = s_res.json()["id"]

    # Update Subtask (completed is a query param in the router)
    u_res = client.patch(f"/subtasks/{s_id}?completed=true")
    assert u_res.status_code == 200
    assert u_res.json()["completed"] is True

    # Delete Subtask
    d_res = client.delete(f"/subtasks/{s_id}")
    assert d_res.status_code == 200

    # Error: Delete non-existent
    err_del = client.delete("/subtasks/00000000-0000-0000-0000-000000000000")
    assert err_del.status_code == 404

    # Error: Update non-existent
    err_upd = client.patch("/subtasks/00000000-0000-0000-0000-000000000000?completed=true")
    assert err_upd.status_code == 404


def test_ai_generate_subtasks(client):
    # Setup
    p_res = client.post("/persons/", json={"name": "AI Owner"})
    t_res = client.post(
        "/todos/",
        json={"title": "T", "description": "D", "person_id": p_res.json()["id"]},
    )
    t_id = t_res.json()["id"]

    # Test AI Route with mock to avoid actual API calls
    with patch("src.routers.ai.ai_service.generate_subtasks") as mock_generate:
        mock_generate.return_value = t_res.json()  # Mock successful return

        res = client.post(f"/todos/{t_id}/generate-subtasks")
        assert res.status_code == 200
        mock_generate.assert_called_once()
