import json

from app.infrastructure.json_task_repository import JsonTaskRepository
from app.models.task import Task


def test_json_task_repository_saves_and_loads_tasks(tmp_path):
    data_file = tmp_path / "tasks.json"
    repository = JsonTaskRepository(data_file)
    task = Task.create(
        title="Persisted task",
        description="Saved through repository",
        quadrant="q1",
        due_date="2026-06-09T09:30",
        has_time=True,
        reminder_minutes=5,
    )

    repository.save_all({task.id: task})
    loaded = repository.load_all()

    assert loaded[task.id].title == "Persisted task"
    assert loaded[task.id].quadrant == "q1"
    assert loaded[task.id].reminder_minutes == 5


def test_json_task_repository_uses_outer_key_for_legacy_payload_without_id(tmp_path):
    data_file = tmp_path / "tasks.json"
    data_file.write_text(
        json.dumps(
            {
                "legacy-id": {
                    "title": "Legacy task",
                    "quadrant": "q2",
                    "created_at": "2026-06-08T08:00:00",
                }
            }
        ),
        encoding="utf-8",
    )
    repository = JsonTaskRepository(data_file)

    loaded = repository.load_all()

    assert "legacy-id" in loaded
    assert loaded["legacy-id"].id == "legacy-id"
    assert loaded["legacy-id"].title == "Legacy task"
