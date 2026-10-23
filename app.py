from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

SUPPORTED_PRIORITIES = {"Low", "Medium", "High"}
DEFAULT_PRIORITY = "Medium"

tasks = [
    {"id": 1, "title": "Project-1 Report"},
    {"id": 2, "title": "Project-2 MMFs"}
]
next_id = 3


def normalize_priority(priority):
    """Return a canonical priority or raise ValueError if invalid."""
    if priority is None:
        return DEFAULT_PRIORITY

    if not isinstance(priority, str):
        raise ValueError("Priority must be Low, Medium, or High")

    normalized_priority = priority.strip().capitalize()
    if not normalized_priority:
        return DEFAULT_PRIORITY

    if normalized_priority not in SUPPORTED_PRIORITIES:
        raise ValueError("Priority must be Low, Medium, or High")

    return normalized_priority


def serialize_task(task):
    """Return a task response with a compatible default priority."""
    serialized_task = dict(task)
    serialized_task["priority"] = normalize_priority(
        serialized_task.get("priority")
    )
    return serialized_task


@app.route('/')
def index():
    """Render the task tracker page."""
    return render_template('index.html')


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Return all tasks with normalized priorities."""
    return jsonify([serialize_task(task) for task in tasks])


@app.route('/api/tasks', methods=['POST'])
def add_task():
    """Validate and create a task with a normalized priority."""
    global next_id
    data = request.get_json()

    if not isinstance(data, dict) or not data.get('title'):
        return jsonify({"error": "Title is required"}), 400

    try:
        priority = normalize_priority(data.get("priority"))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    new_task = {
        "id": next_id,
        "title": data['title'],
        "priority": priority
    }
    tasks.append(new_task)
    next_id += 1

    return jsonify(serialize_task(new_task)), 201


@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task by ID."""
    global tasks
    tasks = [task for task in tasks if task['id'] != task_id]
    return jsonify({"result": "success"}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)
