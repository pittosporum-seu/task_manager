import json
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from app.config import DATA_DIR
from app.models.task import Task


class TaskService(QObject):
    data_changed = pyqtSignal()
    reminder_triggered = pyqtSignal(str, str)

    def __init__(self, filename: Optional[str] = None):
        super().__init__()
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.filepath = Path(filename) if filename else DATA_DIR / "tasks.json"
        self.tasks: Dict[str, Task] = {}
        self.load_data()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_reminders)
        self.timer.start(30_000)

    def load_data(self) -> None:
        if not self.filepath.exists():
            return
        try:
            with self.filepath.open("r", encoding="utf-8") as handle:
                raw = json.load(handle)
            self.tasks = {
                task_id: Task.from_dict(payload)
                for task_id, payload in raw.items()
                if isinstance(payload, dict)
            }
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            print(f"Error loading tasks: {exc}")

    def save_data(self) -> None:
        try:
            data = {task_id: asdict(task) for task_id, task in self.tasks.items()}
            with self.filepath.open("w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
            self.data_changed.emit()
        except OSError as exc:
            print(f"Error saving tasks: {exc}")

    def add_task(
        self,
        title: str,
        description: str = "",
        due_date: Optional[str] = None,
        has_time: bool = False,
        reminder_minutes: Optional[int] = None,
        quadrant: str = "inbox",
    ) -> Task:
        task = Task.create(
            title=title,
            description=description,
            due_date=due_date,
            has_time=has_time,
            reminder_minutes=reminder_minutes,
            quadrant=quadrant,
        )
        self.tasks[task.id] = task
        self.save_data()
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
        task = self.tasks.get(task_id)
        if not task:
            return

        reminder_changed = (
            task.due_date != due_date
            or task.reminder_minutes != reminder_minutes
            or task.has_time != has_time
        )

        task.title = title
        task.description = description
        task.due_date = due_date
        task.has_time = has_time
        task.reminder_minutes = reminder_minutes
        if reminder_changed:
            task.reminder_sent = False
        self.save_data()

    def delete_task(self, task_id: str) -> None:
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.save_data()

    def move_task(self, task_id: str, new_quadrant: str) -> None:
        task = self.tasks.get(task_id)
        if not task or task.quadrant == new_quadrant:
            return
        task.quadrant = new_quadrant
        self.save_data()

    def toggle_complete(self, task_id: str, completed: bool) -> None:
        task = self.tasks.get(task_id)
        if not task:
            return
        task.completed = completed
        task.completed_at = (
            datetime.now().isoformat(timespec="seconds") if completed else None
        )
        if completed:
            task.reminder_sent = True
        self.save_data()

    def check_reminders(self) -> None:
        now = datetime.now()
        changed = False

        for task in self.tasks.values():
            if (
                not task.due_date
                or task.reminder_minutes is None
                or task.reminder_sent
                or task.completed
            ):
                continue

            try:
                due_at = datetime.fromisoformat(task.due_date)
            except ValueError:
                continue

            trigger_at = due_at - timedelta(minutes=task.reminder_minutes)
            if now >= trigger_at:
                task.reminder_sent = True
                changed = True
                self.reminder_triggered.emit(task.title, task.id)

        if changed:
            self.save_data()

