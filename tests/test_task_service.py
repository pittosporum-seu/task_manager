import json

from app.services.task_service import TaskService


def make_service(tmp_path):
    return TaskService(filename=str(tmp_path / "tasks.json"), enable_timer=False)


def test_task_service_crud_and_persistence(tmp_path, qapp):
    service = make_service(tmp_path)
    changed = []
    service.data_changed.connect(lambda: changed.append(True))

    assert service.timer is None

    task = service.add_task("Title", "Desc", "2026-06-09T09:30", True, 5)
    assert service.get_task(task.id) is not None
    assert changed

    service.update_task(task.id, "New title", "New desc", None, False, None)
    assert service.get_task(task.id).title == "New title"
    assert service.get_task(task.id).due_date is None

    service.move_task(task.id, "q1")
    assert service.get_task(task.id).quadrant == "q1"

    service.toggle_complete(task.id, True)
    assert service.get_task(task.id).completed
    assert service.get_task(task.id).completed_at is not None

    reloaded = make_service(tmp_path)
    assert reloaded.get_task(task.id).title == "New title"
    assert reloaded.get_task(task.id).quadrant == "q1"
    assert reloaded.get_task(task.id).completed

    reloaded.delete_task(task.id)
    assert reloaded.get_task(task.id) is None
    assert (tmp_path / "audit.log.jsonl").exists()


def test_task_service_queries_use_domain_rules(tmp_path, qapp):
    service = make_service(tmp_path)
    inbox_task = service.add_task("Inbox")
    matrix_task = service.add_task("Matrix", quadrant="q1", due_date="2026-06-09T09:30")
    service.toggle_complete(matrix_task.id, True)
    historical_task = service.add_task("Historical", quadrant="q2")
    service.toggle_complete(historical_task.id, True, completed_at="2026-06-07T10:00:00")

    assert [task.id for task in service.get_visible_inbox_tasks()] == [inbox_task.id]
    assert [task.id for task in service.get_visible_matrix_tasks()] == [matrix_task.id]
    assert [task.id for task in service.get_archived_tasks()] == [historical_task.id]


def test_task_service_reminder_signal(tmp_path, qapp):
    service = make_service(tmp_path)
    task = service.add_task(
        "Reminder", due_date="2000-01-01T10:00:00", has_time=True, reminder_minutes=0
    )
    reminders = []
    service.reminder_triggered.connect(lambda title, task_id: reminders.append((title, task_id)))

    service.check_reminders()

    assert reminders == [("Reminder", task.id)]
    assert service.get_task(task.id).reminder_sent


def test_task_service_loads_legacy_payload_without_id(tmp_path, qapp):
    data_file = tmp_path / "tasks.json"
    data_file.write_text(
        json.dumps(
            {
                "legacy-id": {
                    "title": "Legacy task",
                    "quadrant": "q1",
                    "created_at": "2026-06-08T08:00:00",
                }
            }
        ),
        encoding="utf-8",
    )

    service = make_service(tmp_path)

    assert service.get_task("legacy-id").id == "legacy-id"
    assert service.get_task("legacy-id").title == "Legacy task"
