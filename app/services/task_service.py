import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from app.config import DATA_DIR
from app.domain.task_rules import (
    archived_tasks,
    should_trigger_reminder,
    visible_inbox_tasks,
    visible_matrix_tasks,
)
from app.models.task import Task


class TaskService(QObject):
    data_changed = pyqtSignal()
    reminder_triggered = pyqtSignal(str, str)

    def __init__(self, filename: Optional[str] = None, enable_timer: bool = True):
        super().__init__()
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.filepath = Path(filename) if filename else DATA_DIR / "tasks.json"
        self.tasks: Dict[str, Task] = {}
        self.load_data()

        self.timer = None
        if enable_timer:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.check_reminders)
            self.timer.start(30_000)

    def load_data(self) -> None:
        if not self.filepath.exists():
            return
        try:
            with self.filepath.open("r", encoding="utf-8") as handle:
                raw = json.load(handle)
            tasks = {}
            for task_id, payload in raw.items():
                if not isinstance(payload, dict):
                    continue
                task = Task.from_dict(payload, fallback_id=task_id)
                tasks[task.id] = task
            self.tasks = tasks
            self.normalize_sort_orders()
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
        task.sort_order = self.next_sort_order(quadrant)
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

    def move_task(self, task_id: str, new_quadrant: str, insert_index: Optional[int] = None) -> None:
        task = self.tasks.get(task_id)
        if not task:
            return

        old_quadrant = task.quadrant
        old_index = self.visible_index(task_id, old_quadrant)
        if old_quadrant == new_quadrant and insert_index is not None and old_index is not None:
            if insert_index > old_index:
                insert_index -= 1
            if insert_index == old_index:
                return

        task.quadrant = new_quadrant
        if insert_index is None:
            task.sort_order = self.next_sort_order(new_quadrant)
        else:
            self.reorder_visible_tasks(new_quadrant, task_id, insert_index)

        self.save_data()

    def next_sort_order(self, quadrant: str) -> int:
        orders = [task.sort_order for task in self.tasks.values() if task.quadrant == quadrant]
        return (max(orders) + 1000) if orders else 1000

    def visible_index(self, task_id: str, quadrant: str) -> Optional[int]:
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

    def toggle_complete(self, task_id: str, completed: bool) -> None:
        task = self.tasks.get(task_id)
        if not task:
            return
        task.completed = completed
        task.completed_at = datetime.now().isoformat(timespec="seconds") if completed else None
        if completed:
            task.reminder_sent = True
        self.save_data()

    def get_visible_inbox_tasks(self) -> list[Task]:
        return visible_inbox_tasks(self.tasks.values())

    def get_visible_matrix_tasks(self) -> list[Task]:
        return visible_matrix_tasks(self.tasks.values())

    def get_archived_tasks(self) -> list[Task]:
        return archived_tasks(self.tasks.values())

    def check_reminders(self) -> None:
        now = datetime.now()
        changed = False

        for task in self.tasks.values():
            if should_trigger_reminder(task, now=now):
                task.reminder_sent = True
                changed = True
                self.reminder_triggered.emit(task.title, task.id)

        if changed:
            self.save_data()
