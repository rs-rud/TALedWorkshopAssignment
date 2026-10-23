from pathlib import Path

import pytest

from app import app, tasks


@pytest.fixture
def client():
    """Provide a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_tasks():
    """Reset the in-memory task list before each test."""
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


def test_get_tasks(client):
    """Return all tasks with a default priority for legacy tasks."""
    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert all(task['priority'] == 'Medium' for task in data)


def test_get_tasks_preserves_stored_priorities(client):
    """Return stored priorities without changing them."""
    tasks.append({"id": 3, "title": "Urgent task", "priority": "High"})

    response = client.get('/api/tasks')

    assert response.status_code == 200
    data = response.get_json()
    assert data[-1]['priority'] == 'High'


@pytest.mark.parametrize('priority', ['Low', 'Medium', 'High'])
def test_add_task_accepts_supported_priorities(client, priority):
    """Create a task with each supported priority."""
    response = client.post(
        '/api/tasks',
        json={"title": f"{priority} task", "priority": priority}
    )

    assert response.status_code == 201
    assert response.get_json()['priority'] == priority


def test_add_task_defaults_missing_priority_to_medium(client):
    """Default a task without a priority to Medium."""
    response = client.post('/api/tasks', json={"title": "Default task"})

    assert response.status_code == 201
    assert response.get_json()['priority'] == 'Medium'


@pytest.mark.parametrize('priority', ['', 'Urgent', None, 1])
def test_add_task_defaults_invalid_priority_to_medium(client, priority):
    """Default invalid priority values to Medium."""
    response = client.post(
        '/api/tasks',
        json={"title": "Invalid priority task", "priority": priority}
    )

    assert response.status_code == 201
    assert response.get_json()['priority'] == 'Medium'


def test_add_task_success(client):
    """Create a task while preserving existing task behavior."""
    response = client.post('/api/tasks', json={"title": "Test new task"})
    assert response.status_code == 201
    assert response.get_json()['title'] == "Test new task"
    get_response = client.get('/api/tasks')
    assert len(get_response.get_json()) == 3


def test_add_task_missing_title(client):
    """Reject task creation requests without a title."""
    response = client.post('/api/tasks', json={"wrong_key": "value"})
    assert response.status_code == 400
    assert "error" in response.get_json()
    response2 = client.post('/api/tasks', json={})
    assert response2.status_code == 400


def test_frontend_supports_priority_selection_and_display():
    """Verify the frontend sends and renders task priorities."""
    template = Path('templates/index.html').read_text()
    script = Path('static/app.js').read_text()

    assert 'id="task-priority"' in template
    assert 'value="Low"' in template
    assert 'value="Medium"' in template
    assert 'value="High"' in template
    assert 'const priorityInput = document.getElementById' in script
    assert 'JSON.stringify({ title, priority })' in script
    assert 'priorityLabel.textContent = priority' in script


def test_delete_task(client):
    """Delete an existing task."""
    response = client.delete('/api/tasks/1')
    assert response.status_code == 200
    get_response = client.get('/api/tasks')
    data = get_response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == 2
