from datetime import datetime

from app.application.commands import (
    AddTask,
    CheckReminders,
    CompleteTask,
    DeleteTask,
    MoveTask,
    ReopenTask,
    UpdateTask,
)
from app.application.event_bus import EventBus
from app.application.events import ReminderTriggered, TaskChanged
from app.application.task_app import TaskApplication
from app.models.task import Task


class InMemoryTaskRepository:
    def __init__(self, tasks=None):
        self.loaded_tasks = tasks or {}
        self.saved_tasks = {}
        self.save_count = 0

    def load_all(self):
        return dict(self.loaded_tasks)

    def save_all(self, tasks):
        self.saved_tasks = dict(tasks)
        self.save_count += 1


def make_application(tasks=None):
    repository = InMemoryTaskRepository(tasks)
    event_bus = EventBus()
    events = []
    event_bus.subscribe(TaskChanged, events.append)
    event_bus.subscribe(ReminderTriggered, events.append)
    return TaskApplication(repository, event_bus), repository, events


def task_changed_events(events):
    return [event for event in events if isinstance(event, TaskChanged)]


def test_task_application_dispatches_task_lifecycle_commands():
    app, repository, events = make_application()

    add_result = app.dispatch(AddTask(title="Task", description="Desc"))
    task_id = add_result.task_id
    assert add_result.ok
    assert add_result.changed
    assert task_id
    assert app.get_task(task_id).title == "Task"

    update_result = app.dispatch(
        UpdateTask(
            task_id=task_id,
            title="Updated",
            description="New desc",
            due_date="2026-06-09T09:30",
            has_time=True,
            reminder_minutes=15,
        )
    )
    assert update_result.ok
    assert app.get_task(task_id).title == "Updated"
    assert app.get_task(task_id).reminder_minutes == 15

    move_result = app.dispatch(MoveTask(task_id=task_id, new_quadrant="q1"))
    assert move_result.ok
    assert app.get_task(task_id).quadrant == "q1"

    complete_result = app.dispatch(
        CompleteTask(task_id=task_id, completed_at="2026-06-08T10:00:00")
    )
    assert complete_result.ok
    assert app.get_task(task_id).completed
    assert app.get_task(task_id).completed_at == "2026-06-08T10:00:00"

    reopen_result = app.dispatch(ReopenTask(task_id=task_id))
    assert reopen_result.ok
    assert not app.get_task(task_id).completed
    assert app.get_task(task_id).completed_at is None

    delete_result = app.dispatch(DeleteTask(task_id=task_id))
    assert delete_result.ok
    assert app.get_task(task_id) is None

    assert repository.save_count == 6
    assert [event.action for event in task_changed_events(events)] == [
        "add",
        "update",
        "move",
        "complete",
        "reopen",
        "delete",
    ]


def test_task_application_check_reminders_triggers_events():
    task = Task.create(
        title="Reminder",
        due_date="2026-06-08T10:00:00",
        has_time=True,
        reminder_minutes=30,
    )
    app, repository, events = make_application({task.id: task})

    result = app.dispatch(CheckReminders(now=datetime(2026, 6, 8, 9, 30)))

    assert result.ok
    assert result.changed
    assert repository.save_count == 1
    assert app.get_task(task.id).reminder_sent
    assert any(
        isinstance(event, ReminderTriggered) and event.task_id == task.id for event in events
    )
    assert task_changed_events(events)[-1].action == "check_reminders"


def test_task_application_validates_title_and_quadrant():
    app, repository, events = make_application()

    empty_title = app.dispatch(AddTask(title="   "))
    invalid_quadrant = app.dispatch(AddTask(title="Task", quadrant="bad"))

    assert not empty_title.ok
    assert empty_title.message == "Task title is required"
    assert not invalid_quadrant.ok
    assert invalid_quadrant.message == "Invalid quadrant"
    assert repository.save_count == 0
    assert events == []
