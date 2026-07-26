from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any

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
from app.application.context import CommandContext
from app.application.event_bus import EventBus
from app.application.events import ApplicationEvent, ReminderTriggered, TaskChanged
from app.application.results import CommandResult
from app.application.serializers import (
    command_result_to_dict,
    command_to_dict,
    context_to_dict,
    event_to_dict,
)
from app.domain.task_rules import (
    archived_tasks,
    is_valid_quadrant,
    parse_datetime,
    should_trigger_reminder,
    visible_inbox_tasks,
    visible_matrix_tasks,
)
from app.infrastructure.task_repository import TaskRepository
from app.models.task import Task


TITLE_MAX_LENGTH = 120
DESCRIPTION_MAX_LENGTH = 2_000
FUTURE_AI_SOURCE = "future_ai"


class TaskApplication:
    def __init__(
        self,
        repository: TaskRepository,
        event_bus: EventBus | None = None,
        audit_log=None,
    ):
        self.repository = repository
        self.event_bus = event_bus or EventBus()
        self.audit_log = audit_log
        self.tasks = self.repository.load_all()
        self.normalize_sort_orders()

    def dispatch(
        self,
        command: TaskCommand,
        context: CommandContext | None = None,
    ) -> CommandResult:
        context = context or CommandContext()
        try:
            if self._requires_dry_run(command, context):
                result = CommandResult(
                    ok=False,
                    message="future_ai delete requires dry-run",
                    task_id=self._task_id_from_command(command),
                )
            elif context.dry_run:
                result = self._preview(command)
            else:
                result = self._dispatch(command)
        except OSError as exc:
            result = CommandResult(ok=False, message=f"Persistence error: {exc}")

        self._write_audit(command, context, result)
        if not context.dry_run:
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
        self.normalize_sort_orders()

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
        validation = self._validate_task_values(
            title=command.title,
            description=command.description,
            due_date=command.due_date,
            has_time=command.has_time,
            reminder_minutes=command.reminder_minutes,
        )
        if validation:
            return validation
        if not is_valid_quadrant(command.quadrant):
            return CommandResult(ok=False, message="Invalid quadrant")

        task = Task.create(
            title=command.title.strip(),
            description=command.description,
            due_date=command.due_date,
            has_time=command.has_time,
            reminder_minutes=command.reminder_minutes,
            quadrant=command.quadrant,
            tags=self._normalize_tags(command.tags),
        )
        task.sort_order = self.next_sort_order(command.quadrant)
        self.tasks[task.id] = task
        return self._changed_result("add", task.id, "Task added", {"task": asdict(task)})

    def _update_task(self, command: UpdateTask) -> CommandResult:
        task = self.tasks.get(command.task_id)
        if not task:
            return CommandResult(ok=False, message="Task not found", task_id=command.task_id)

        validation = self._validate_task_values(
            title=command.title,
            description=command.description,
            due_date=command.due_date,
            has_time=command.has_time,
            reminder_minutes=command.reminder_minutes,
            task_id=task.id,
        )
        if validation:
            return validation

        reminder_changed = (
            task.due_date != command.due_date
            or task.reminder_minutes != command.reminder_minutes
            or task.has_time != command.has_time
        )

        task.title = command.title.strip()
        task.description = command.description
        task.due_date = command.due_date
        task.has_time = command.has_time
        task.reminder_minutes = command.reminder_minutes
        if command.tags is not None:
            task.tags = self._normalize_tags(command.tags)
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
        if not is_valid_quadrant(command.new_quadrant):
            return CommandResult(ok=False, message="Invalid quadrant", task_id=task.id)
        old_quadrant = task.quadrant
        old_index = self.visible_index(task.id, old_quadrant)
        insert_index = command.insert_index
        if (
            old_quadrant == command.new_quadrant
            and command.insert_index is not None
            and old_index is not None
        ):
            insert_index = (
                command.insert_index - 1 if command.insert_index > old_index else command.insert_index
            )
            if insert_index == old_index:
                return CommandResult(ok=True, message="Task already in position", task_id=task.id)
        elif task.quadrant == command.new_quadrant:
            return CommandResult(ok=True, message="Task already in quadrant", task_id=task.id)

        task.quadrant = command.new_quadrant
        if command.insert_index is None:
            task.sort_order = self.next_sort_order(command.new_quadrant)
        else:
            self.reorder_visible_tasks(command.new_quadrant, task.id, insert_index)
        return self._changed_result("move", task.id, "Task moved", {"task": asdict(task)})

    def _complete_task(self, command: CompleteTask) -> CommandResult:
        task = self.tasks.get(command.task_id)
        if not task:
            return CommandResult(ok=False, message="Task not found", task_id=command.task_id)
        validation = self._validate_completed_at(command.completed_at, task.id)
        if validation:
            return validation
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

    def _preview(self, command: TaskCommand) -> CommandResult:
        if isinstance(command, AddTask):
            return self._preview_add(command)
        if isinstance(command, UpdateTask):
            return self._preview_update(command)
        if isinstance(command, DeleteTask):
            return self._preview_delete(command)
        if isinstance(command, MoveTask):
            return self._preview_move(command)
        if isinstance(command, CompleteTask):
            return self._preview_complete(command)
        if isinstance(command, ReopenTask):
            return self._preview_reopen(command)
        if isinstance(command, CheckReminders):
            return self._preview_check_reminders(command)
        return CommandResult(ok=False, message=f"Unsupported command: {type(command).__name__}")

    def _preview_add(self, command: AddTask) -> CommandResult:
        validation = self._validate_task_values(
            title=command.title,
            description=command.description,
            due_date=command.due_date,
            has_time=command.has_time,
            reminder_minutes=command.reminder_minutes,
        )
        if validation:
            return validation
        if not is_valid_quadrant(command.quadrant):
            return CommandResult(ok=False, message="Invalid quadrant")

        return CommandResult(
            ok=True,
            message="Dry run: task would be added",
            would_change=True,
            preview={
                "operation": "add",
                "task": {
                    "title": command.title.strip(),
                    "description": command.description,
                    "quadrant": command.quadrant,
                    "due_date": command.due_date,
                    "has_time": command.has_time,
                    "reminder_minutes": command.reminder_minutes,
                    "tags": self._normalize_tags(command.tags),
                },
            },
        )

    def _preview_update(self, command: UpdateTask) -> CommandResult:
        task = self.tasks.get(command.task_id)
        if not task:
            return CommandResult(ok=False, message="Task not found", task_id=command.task_id)
        validation = self._validate_task_values(
            title=command.title,
            description=command.description,
            due_date=command.due_date,
            has_time=command.has_time,
            reminder_minutes=command.reminder_minutes,
            task_id=task.id,
        )
        if validation:
            return validation

        before = asdict(task)
        after = {**before}
        after.update(
            {
                "title": command.title.strip(),
                "description": command.description,
                "due_date": command.due_date,
                "has_time": command.has_time,
                "reminder_minutes": command.reminder_minutes,
            }
        )
        if command.tags is not None:
            after["tags"] = self._normalize_tags(command.tags)
        if (
            before["due_date"] != command.due_date
            or before["reminder_minutes"] != command.reminder_minutes
            or before["has_time"] != command.has_time
        ):
            after["reminder_sent"] = False

        return self._preview_result("update", task.id, before, after)

    def _preview_delete(self, command: DeleteTask) -> CommandResult:
        task = self.tasks.get(command.task_id)
        if not task:
            return CommandResult(ok=False, message="Task not found", task_id=command.task_id)
        return CommandResult(
            ok=True,
            message="Dry run: task would be deleted",
            would_change=True,
            task_id=task.id,
            preview={"operation": "delete", "task": asdict(task)},
        )

    def _preview_move(self, command: MoveTask) -> CommandResult:
        task = self.tasks.get(command.task_id)
        if not task:
            return CommandResult(ok=False, message="Task not found", task_id=command.task_id)
        if not is_valid_quadrant(command.new_quadrant):
            return CommandResult(ok=False, message="Invalid quadrant", task_id=task.id)

        before = asdict(task)
        after = {**before, "quadrant": command.new_quadrant}
        if command.insert_index is not None:
            after["insert_index"] = command.insert_index
        return self._preview_result("move", task.id, before, after)

    def next_sort_order(self, quadrant: str) -> int:
        orders = [task.sort_order for task in self.tasks.values() if task.quadrant == quadrant]
        return (max(orders) + 1000) if orders else 1000

    def visible_index(self, task_id: str, quadrant: str) -> int | None:
        for index, task in enumerate(self.visible_tasks_for_quadrant(quadrant)):
            if task.id == task_id:
                return index
        return None

    def visible_tasks_for_quadrant(self, quadrant: str) -> list[Task]:
        if quadrant == "inbox":
            return self.get_visible_inbox_tasks()
        return [task for task in self.get_visible_matrix_tasks() if task.quadrant == quadrant]

    def reorder_visible_tasks(self, quadrant: str, moved_task_id: str, insert_index: int) -> None:
        ordered = [task for task in self.visible_tasks_for_quadrant(quadrant) if task.id != moved_task_id]
        moved_task = self.tasks.get(moved_task_id)
        if moved_task is None:
            return

        insert_index = max(0, min(insert_index, len(ordered)))
        ordered.insert(insert_index, moved_task)
        for index, task in enumerate(ordered):
            task.sort_order = (index + 1) * 1000

    def normalize_sort_orders(self) -> None:
        for quadrant in {"inbox", "q1", "q2", "q3", "q4"}:
            ordered = self.visible_tasks_for_quadrant(quadrant)
            for index, task in enumerate(ordered):
                if task.sort_order <= 0:
                    task.sort_order = (index + 1) * 1000

    def _preview_complete(self, command: CompleteTask) -> CommandResult:
        task = self.tasks.get(command.task_id)
        if not task:
            return CommandResult(ok=False, message="Task not found", task_id=command.task_id)
        validation = self._validate_completed_at(command.completed_at, task.id)
        if validation:
            return validation

        before = asdict(task)
        after = (
            before
            if task.completed
            else {
                **before,
                "completed": True,
                "completed_at": command.completed_at or "<execution-time>",
                "reminder_sent": True,
            }
        )
        return self._preview_result("complete", task.id, before, after)

    def _preview_reopen(self, command: ReopenTask) -> CommandResult:
        task = self.tasks.get(command.task_id)
        if not task:
            return CommandResult(ok=False, message="Task not found", task_id=command.task_id)

        before = asdict(task)
        after = (
            before if not task.completed else {**before, "completed": False, "completed_at": None}
        )
        return self._preview_result("reopen", task.id, before, after)

    def _preview_check_reminders(self, command: CheckReminders) -> CommandResult:
        now = command.now or datetime.now()
        reminders = [
            {"task_id": task.id, "title": task.title}
            for task in self.tasks.values()
            if should_trigger_reminder(task, now=now)
        ]
        return CommandResult(
            ok=True,
            message=(
                "Dry run: reminders would be triggered"
                if reminders
                else "Dry run: no reminders would trigger"
            ),
            would_change=bool(reminders),
            preview={"operation": "check_reminders", "reminders": reminders},
        )

    def _preview_result(
        self,
        operation: str,
        task_id: str,
        before: dict[str, Any],
        after: dict[str, Any],
    ) -> CommandResult:
        would_change = before != after
        labels = {
            "update": "updated",
            "move": "moved",
            "complete": "completed",
            "reopen": "reopened",
        }
        return CommandResult(
            ok=True,
            message=(
                f"Dry run: task would be {labels.get(operation, operation)}"
                if would_change
                else "Dry run: no changes"
            ),
            would_change=would_change,
            task_id=task_id,
            preview={"operation": operation, "before": before, "after": after},
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

    def _validate_task_values(
        self,
        *,
        title: str,
        description: str,
        due_date: str | None,
        has_time: bool,
        reminder_minutes: int | None,
        task_id: str | None = None,
    ) -> CommandResult | None:
        title = title.strip()
        if not title:
            return CommandResult(ok=False, message="Task title is required", task_id=task_id)
        if len(title) > TITLE_MAX_LENGTH:
            return CommandResult(ok=False, message="Task title is too long", task_id=task_id)
        if len(description) > DESCRIPTION_MAX_LENGTH:
            return CommandResult(ok=False, message="Task description is too long", task_id=task_id)
        if due_date is not None and parse_datetime(due_date) is None:
            return CommandResult(ok=False, message="Invalid due_date", task_id=task_id)
        if due_date is None and has_time:
            return CommandResult(ok=False, message="has_time requires due_date", task_id=task_id)
        if reminder_minutes is not None:
            if reminder_minutes < 0:
                return CommandResult(
                    ok=False,
                    message="reminder_minutes must be non-negative",
                    task_id=task_id,
                )
            if due_date is None:
                return CommandResult(
                    ok=False,
                    message="reminder_minutes requires due_date",
                    task_id=task_id,
                )
        return None

    def _normalize_tags(self, tags: list[dict[str, str]] | None) -> list[dict[str, str]]:
        if not tags:
            return []

        normalized = []
        seen = set()
        for tag in tags:
            if not isinstance(tag, dict):
                continue
            name = str(tag.get("name", "")).strip()
            color = str(tag.get("color", "#6B7280")).strip() or "#6B7280"
            key = name.casefold()
            if not name or key in seen:
                continue
            seen.add(key)
            normalized.append({"name": name, "color": color})
        return normalized

    def _validate_completed_at(
        self,
        completed_at: str | None,
        task_id: str | None = None,
    ) -> CommandResult | None:
        if completed_at is not None and parse_datetime(completed_at) is None:
            return CommandResult(ok=False, message="Invalid completed_at", task_id=task_id)
        return None

    def _requires_dry_run(self, command: TaskCommand, context: CommandContext) -> bool:
        return (
            isinstance(command, DeleteTask)
            and context.source == FUTURE_AI_SOURCE
            and not context.dry_run
        )

    def _task_id_from_command(self, command: TaskCommand) -> str | None:
        return getattr(command, "task_id", None)

    def _write_audit(
        self,
        command: TaskCommand,
        context: CommandContext,
        result: CommandResult,
    ) -> None:
        if self.audit_log is None:
            return
        record = {
            "time": datetime.now().isoformat(timespec="seconds"),
            "source": context.source,
            "dry_run": context.dry_run,
            "request_id": context.request_id,
            "actor": context.actor,
            "context": context_to_dict(context),
            "command": type(command).__name__,
            "payload": command_to_dict(command),
            "ok": result.ok,
            "changed": result.changed,
            "would_change": result.would_change,
            "task_id": result.task_id,
            "preview": command_result_to_dict(result)["preview"],
            "events": [event_to_dict(event) for event in result.events],
        }
        try:
            self.audit_log.append(record)
        except OSError as exc:
            result.data.setdefault("audit_error", str(exc))
