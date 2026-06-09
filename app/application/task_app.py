from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

from app.application.commands import (
    AddTask,
    CheckReminders,
    CompleteTask,
    DeleteTask,
    MoveTask,
    ReopenTask,
    TaskCommand,
    UpdateTask,
)
from app.application.event_bus import EventBus
from app.application.events import ApplicationEvent, ReminderTriggered, TaskChanged
from app.application.results import CommandResult
from app.domain.task_rules import (
    archived_tasks,
    should_trigger_reminder,
    visible_inbox_tasks,
    visible_matrix_tasks,
)
from app.infrastructure.task_repository import TaskRepository
from app.models.task import Task


class TaskApplication:
    def __init__(self, repository: TaskRepository, event_bus: EventBus | None = None):
        self.repository = repository
        self.event_bus = event_bus or EventBus()
        self.tasks = self.repository.load_all()

    def dispatch(self, command: TaskCommand) -> CommandResult:
        try:
            result = self._dispatch(command)
        except OSError as exc:
            return CommandResult(ok=False, message=f"Persistence error: {exc}")

        self.event_bus.publish_many(result.events)
        return result

    def _dispatch(self, command: TaskCommand) -> CommandResult:
        if isinstance(command, AddTask):
            return self._add_task(command)
        if isinstance(command, UpdateTask):
            return self._update_task(command)
        if isinstance(command, DeleteTask):
            return self._delete_task(command)
        if isinstance(command, MoveTask):
            return self._move_task(command)
        if isinstance(command, CompleteTask):
            return self._complete_task(command)
        if isinstance(command, ReopenTask):
            return self._reopen_task(command)
        if isinstance(command, CheckReminders):
            return self._check_reminders(command)
        return CommandResult(ok=False, message=f"Unsupported command: {type(command).__name__}")

    def reload(self) -> None:
        self.tasks = self.repository.load_all()

    def save(self) -> None:
        self.repository.save_all(self.tasks)

    def get_task(self, task_id: str) -> Task | None:
        return self.tasks.get(task_id)

    def get_visible_inbox_tasks(self) -> list[Task]:
        return visible_inbox_tasks(self.tasks.values())

    def get_visible_matrix_tasks(self) -> list[Task]:
        return visible_matrix_tasks(self.tasks.values())

    def get_archived_tasks(self) -> list[Task]:
        return archived_tasks(self.tasks.values())

    def _add_task(self, command: AddTask) -> CommandResult:
        task = Task.create(
            title=command.title,
            description=command.description,
            due_date=command.due_date,
            has_time=command.has_time,
            reminder_minutes=command.reminder_minutes,
            quadrant=command.quadrant,
        )
        self.tasks[task.id] = task
        return self._changed_result("add", task.id, "Task added", {"task": asdict(task)})

    def _update_task(self, command: UpdateTask) -> CommandResult:
        task = self.tasks.get(command.task_id)
        if not task:
            return CommandResult(ok=False, message="Task not found", task_id=command.task_id)

        reminder_changed = (
            task.due_date != command.due_date
            or task.reminder_minutes != command.reminder_minutes
            or task.has_time != command.has_time
        )

        task.title = command.title
        task.description = command.description
        task.due_date = command.due_date
        task.has_time = command.has_time
        task.reminder_minutes = command.reminder_minutes
        if reminder_changed:
            task.reminder_sent = False

        return self._changed_result("update", task.id, "Task updated", {"task": asdict(task)})

    def _delete_task(self, command: DeleteTask) -> CommandResult:
        if command.task_id not in self.tasks:
            return CommandResult(ok=False, message="Task not found", task_id=command.task_id)

        del self.tasks[command.task_id]
        return self._changed_result("delete", command.task_id, "Task deleted")

    def _move_task(self, command: MoveTask) -> CommandResult:
        task = self.tasks.get(command.task_id)
        if not task:
            return CommandResult(ok=False, message="Task not found", task_id=command.task_id)
        if task.quadrant == command.new_quadrant:
            return CommandResult(ok=True, message="Task already in quadrant", task_id=task.id)

        task.quadrant = command.new_quadrant
        return self._changed_result("move", task.id, "Task moved", {"task": asdict(task)})

    def _complete_task(self, command: CompleteTask) -> CommandResult:
        task = self.tasks.get(command.task_id)
        if not task:
            return CommandResult(ok=False, message="Task not found", task_id=command.task_id)
        if task.completed:
            return CommandResult(ok=True, message="Task already completed", task_id=task.id)

        task.completed = True
        task.completed_at = command.completed_at or datetime.now().isoformat(timespec="seconds")
        task.reminder_sent = True
        return self._changed_result("complete", task.id, "Task completed", {"task": asdict(task)})

    def _reopen_task(self, command: ReopenTask) -> CommandResult:
        task = self.tasks.get(command.task_id)
        if not task:
            return CommandResult(ok=False, message="Task not found", task_id=command.task_id)
        if not task.completed:
            return CommandResult(ok=True, message="Task already open", task_id=task.id)

        task.completed = False
        task.completed_at = None
        return self._changed_result("reopen", task.id, "Task reopened", {"task": asdict(task)})

    def _check_reminders(self, command: CheckReminders) -> CommandResult:
        now = command.now or datetime.now()
        events: list[ApplicationEvent] = []
        triggered = []

        for task in self.tasks.values():
            if should_trigger_reminder(task, now=now):
                task.reminder_sent = True
                event = ReminderTriggered(task_id=task.id, title=task.title)
                events.append(event)
                triggered.append({"task_id": task.id, "title": task.title})

        if not events:
            return CommandResult(ok=True, message="No reminders triggered")

        events.append(TaskChanged(action="check_reminders"))
        self.repository.save_all(self.tasks)
        return CommandResult(
            ok=True,
            message="Reminders triggered",
            changed=True,
            data={"reminders": triggered},
            events=events,
        )

    def _changed_result(
        self,
        action: str,
        task_id: str,
        message: str,
        data: dict | None = None,
    ) -> CommandResult:
        event = TaskChanged(action=action, task_id=task_id)
        self.repository.save_all(self.tasks)
        return CommandResult(
            ok=True,
            message=message,
            changed=True,
            task_id=task_id,
            data=data or {},
            events=[event],
        )
