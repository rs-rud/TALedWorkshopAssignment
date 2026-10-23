import pytest

from app import app, tasks


@pytest.fixture
def client():
    """Provide a Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_tasks():
    """Reset the in-memory task list before each test."""
    tasks.clear()
    tasks.extend(
        [
            {"id": 1, "title": "Project-1 Report"},
            {"id": 2, "title": "Project-2 MMFs"},
        ]
    )


def test_index(client):
    """Render the task tracker page."""
    response = client.get("/")

    assert response.status_code == 200
    assert b"Task Tracker" in response.data


def test_get_tasks(client):
    """Return all tasks with a default priority when it is missing."""
    response = client.get("/api/tasks")

    assert response.status_code == 200
    assert response.get_json() == [
        {
            "id": 1,
            "title": "Project-1 Report",
            "priority": "Medium",
        },
        {
            "id": 2,
            "title": "Project-2 MMFs",
            "priority": "Medium",
        },
    ]


@pytest.mark.parametrize("priority", ["Low", "Medium", "High"])
def test_add_task_with_each_priority(client, priority):
    """Create a task with each supported priority value."""
    response = client.post(
        "/api/tasks",
        json={"title": "Prioritized task", "priority": priority},
    )

    assert response.status_code == 201
    assert response.get_json()["priority"] == priority

    tasks_response = client.get("/api/tasks")
    created_task = tasks_response.get_json()[-1]
    assert created_task["title"] == "Prioritized task"
    assert created_task["priority"] == priority


def test_add_task_defaults_to_medium_priority(client):
    """Default a new task to Medium when priority is omitted."""
    response = client.post(
        "/api/tasks",
        json={"title": "Task without priority"},
    )

    assert response.status_code == 201
    assert response.get_json()["priority"] == "Medium"

    tasks_response = client.get("/api/tasks")
    assert tasks_response.get_json()[-1]["priority"] == "Medium"


def test_add_task_rejects_invalid_priority(client):
    """Reject a task whose priority is not supported."""
    response = client.post(
        "/api/tasks",
        json={"title": "Invalid priority task", "priority": "Urgent"},
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "Priority must be Low, Medium, or High"
    }


def test_add_task_success(client):
    """Create a task without changing existing title behavior."""
    response = client.post("/api/tasks", json={"title": "Test new task"})

    assert response.status_code == 201
    assert response.get_json()["title"] == "Test new task"
    assert response.get_json()["priority"] == "Medium"

    get_response = client.get("/api/tasks")
    assert len(get_response.get_json()) == 3


def test_add_task_missing_title(client):
    """Reject requests that do not include a task title."""
    response = client.post("/api/tasks", json={"wrong_key": "value"})

    assert response.status_code == 400
    assert "error" in response.get_json()

    response_without_data = client.post("/api/tasks", json={})
    assert response_without_data.status_code == 400


def test_delete_task(client):
    """Delete an existing task."""
    response = client.delete("/api/tasks/1")

    assert response.status_code == 200

    get_response = client.get("/api/tasks")
    data = get_response.get_json()
    assert len(data) == 1
    assert data[0]["id"] == 2
