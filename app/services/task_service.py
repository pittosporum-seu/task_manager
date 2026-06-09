from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

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
from app.config import DATA_DIR
from app.infrastructure.json_task_repository import JsonTaskRepository
from app.models.task import Task


class TaskService(QObject):
    data_changed = pyqtSignal()
    reminder_triggered = pyqtSignal(str, str)

    def __init__(self, filename: Optional[str] = None, enable_timer: bool = True):
        super().__init__()
        self.filepath = Path(filename) if filename else DATA_DIR / "tasks.json"
        self.repository = JsonTaskRepository(self.filepath)
        self.event_bus = EventBus()
        self.event_bus.subscribe(TaskChanged, self._handle_task_changed)
        self.event_bus.subscribe(ReminderTriggered, self._handle_reminder_triggered)
        self.application = TaskApplication(self.repository, self.event_bus)

        self.timer = None
        if enable_timer:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.check_reminders)
            self.timer.start(30_000)

    @property
    def tasks(self) -> dict[str, Task]:
        return self.application.tasks

    def load_data(self) -> None:
        self.application.reload()

    def save_data(self) -> None:
        self.application.save()
        self.data_changed.emit()

    def add_task(
        self,
        title: str,
        description: str = "",
        due_date: Optional[str] = None,
        has_time: bool = False,
        reminder_minutes: Optional[int] = None,
        quadrant: str = "inbox",
    ) -> Task:
        result = self.application.dispatch(
            AddTask(
                title=title,
                description=description,
                due_date=due_date,
                has_time=has_time,
                reminder_minutes=reminder_minutes,
                quadrant=quadrant,
            )
        )
        task = self.get_task(result.task_id or "")
        if task is None:
            raise RuntimeError(result.message or "Task was not created")
        return task

    def update_task(
        self,
        task_id: str,
        title: str,
        description: str,
        due_date: Optional[str],
        has_time: bool,
        reminder_minutes: Optional[int],
    ) -> None:
        self.application.dispatch(
            UpdateTask(
                task_id=task_id,
                title=title,
                description=description,
                due_date=due_date,
                has_time=has_time,
                reminder_minutes=reminder_minutes,
            )
        )

    def delete_task(self, task_id: str) -> None:
        self.application.dispatch(DeleteTask(task_id=task_id))

    def move_task(self, task_id: str, new_quadrant: str) -> None:
        self.application.dispatch(MoveTask(task_id=task_id, new_quadrant=new_quadrant))

    def toggle_complete(
        self,
        task_id: str,
        completed: bool,
        completed_at: Optional[str] = None,
    ) -> None:
        if completed:
            self.application.dispatch(CompleteTask(task_id=task_id, completed_at=completed_at))
        else:
            self.application.dispatch(ReopenTask(task_id=task_id))

    def get_task(self, task_id: str) -> Task | None:
        return self.application.get_task(task_id)

    def get_visible_inbox_tasks(self) -> list[Task]:
        return self.application.get_visible_inbox_tasks()

    def get_visible_matrix_tasks(self) -> list[Task]:
        return self.application.get_visible_matrix_tasks()

    def get_archived_tasks(self) -> list[Task]:
        return self.application.get_archived_tasks()

    def check_reminders(self) -> None:
        self.application.dispatch(CheckReminders())

    def _handle_task_changed(self, event) -> None:
        self.data_changed.emit()

    def _handle_reminder_triggered(self, event) -> None:
        self.reminder_triggered.emit(event.title, event.task_id)
