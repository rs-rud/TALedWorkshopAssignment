import pytest

from app import app, tasks


@pytest.fixture
def client():
    """Provide a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_tasks():
    """Restore the in-memory task records before each test."""
    tasks.clear()
    tasks.extend([
        {"id": 1, "title": "Project-1 Report"},
        {"id": 2, "title": "Project-2 MMFs"}
    ])


def test_index(client):
    """Render the task tracker page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Task Tracker" in response.data
    assert b"task-priority" in response.data


def test_get_tasks(client):
    """Return legacy tasks with a Medium priority."""
    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert all(task["priority"] == "Medium" for task in data)


@pytest.mark.parametrize("priority", ["Low", "Medium", "High"])
def test_add_task_supported_priorities(client, priority):
    """Store and return each supported task priority."""
    response = client.post(
        '/api/tasks',
        json={"title": "Prioritized task", "priority": priority}
    )

    assert response.status_code == 201
    assert response.get_json()["priority"] == priority
    stored_task = tasks[-1]
    assert stored_task["priority"] == priority


def test_add_task_defaults_missing_priority_to_medium(client):
    """Use Medium when priority is omitted."""
    response = client.post('/api/tasks', json={"title": "Default task"})

    assert response.status_code == 201
    assert response.get_json()["priority"] == "Medium"
    assert tasks[-1]["priority"] == "Medium"


def test_add_task_defaults_blank_priority_to_medium(client):
    """Use Medium when priority is blank or whitespace."""
    for priority in ["", "   "]:
        response = client.post(
            '/api/tasks',
            json={"title": "Blank priority task", "priority": priority}
        )

        assert response.status_code == 201
        assert response.get_json()["priority"] == "Medium"


def test_add_task_rejects_invalid_priority(client):
    """Reject unsupported priority values."""
    response = client.post(
        '/api/tasks',
        json={"title": "Invalid task", "priority": "Urgent"}
    )

    assert response.status_code == 400
    assert "error" in response.get_json()
    assert len(tasks) == 2


def test_serializes_legacy_task_with_medium_priority(client):
    """Return Medium for a stored task without a priority field."""
    tasks.append({"id": 3, "title": "Legacy task"})

    response = client.get('/api/tasks')

    assert response.status_code == 200
    legacy_task = response.get_json()[-1]
    assert legacy_task["title"] == "Legacy task"
    assert legacy_task["priority"] == "Medium"


def test_add_task_success(client):
    """Create a task while preserving the existing API behavior."""
    response = client.post('/api/tasks', json={"title": "Test new task"})
    assert response.status_code == 201
    assert response.get_json()['title'] == "Test new task"
    get_response = client.get('/api/tasks')
    assert len(get_response.get_json()) == 3


def test_add_task_missing_title(client):
    """Reject requests without a title."""
    response = client.post('/api/tasks', json={"wrong_key": "value"})
    assert response.status_code == 400
    assert "error" in response.get_json()

    response = client.post('/api/tasks', json={})
    assert response.status_code == 400


def test_delete_task(client):
    """Delete an existing task."""
    response = client.delete('/api/tasks/1')
    assert response.status_code == 200
    get_response = client.get('/api/tasks')
    data = get_response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == 2
