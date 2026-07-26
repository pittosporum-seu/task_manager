from __future__ import annotations

import json
from datetime import datetime, timedelta
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
from app.application.context import CommandContext
from app.application.event_bus import EventBus
from app.application.events import ReminderTriggered, TaskChanged
from app.application.task_app import TaskApplication
from app.config import DATA_DIR
from app.infrastructure.audit_log import JsonlAuditLog
from app.infrastructure.json_task_repository import JsonTaskRepository
from app.models.task import Task


class TaskService(QObject):
    data_changed = pyqtSignal()
    reminder_triggered = pyqtSignal(str, str)

    def __init__(self, filename: Optional[str] = None, enable_timer: bool = True):
        super().__init__()
        self.filepath = Path(filename) if filename else DATA_DIR / "tasks.json"
        self.tags_filepath = self.filepath.parent / "tags.json"
        self.repository = JsonTaskRepository(self.filepath)
        self.audit_log = JsonlAuditLog(self.filepath.parent / "audit.log.jsonl")
        self.context = CommandContext(source="ui")
        self.event_bus = EventBus()
        self.event_bus.subscribe(TaskChanged, self._handle_task_changed)
        self.event_bus.subscribe(ReminderTriggered, self._handle_reminder_triggered)
        self.application = TaskApplication(self.repository, self.event_bus, self.audit_log)

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
        self._save_tag_catalog(self.get_all_tags())
        self.data_changed.emit()

    def add_task(
        self,
        title: str,
        description: str = "",
        due_date: Optional[str] = None,
        has_time: bool = False,
        reminder_minutes: Optional[int] = None,
        quadrant: str = "inbox",
        tags: Optional[list[dict[str, str]]] = None,
    ) -> Task:
        result = self._dispatch(
            AddTask(
                title=title,
                description=description,
                due_date=due_date,
                has_time=has_time,
                reminder_minutes=reminder_minutes,
                quadrant=quadrant,
                tags=tags,
            )
        )
        task = self.get_task(result.task_id or "")
        if task is None:
            raise RuntimeError(result.message or "Task was not created")
        self._sync_catalog_from_tags(tags or [])
        return task

    def update_task(
        self,
        task_id: str,
        title: str,
        description: str,
        due_date: Optional[str],
        has_time: bool,
        reminder_minutes: Optional[int],
        tags: Optional[list[dict[str, str]]] = None,
    ) -> None:
        self._dispatch(
            UpdateTask(
                task_id=task_id,
                title=title,
                description=description,
                due_date=due_date,
                has_time=has_time,
                reminder_minutes=reminder_minutes,
                tags=tags,
            )
        )
        self._sync_catalog_from_tags(tags or [])

    def delete_task(self, task_id: str) -> None:
        self._dispatch(DeleteTask(task_id=task_id))

    def move_task(self, task_id: str, new_quadrant: str, insert_index: Optional[int] = None) -> None:
        self._dispatch(
            MoveTask(task_id=task_id, new_quadrant=new_quadrant, insert_index=insert_index)
        )

    def toggle_complete(
        self,
        task_id: str,
        completed: bool,
        completed_at: Optional[str] = None,
    ) -> None:
        if completed:
            self._dispatch(CompleteTask(task_id=task_id, completed_at=completed_at))
        else:
            self._dispatch(ReopenTask(task_id=task_id))

    def get_task(self, task_id: str) -> Task | None:
        return self.application.get_task(task_id)

    def get_visible_inbox_tasks(self) -> list[Task]:
        return self.application.get_visible_inbox_tasks()

    def get_visible_matrix_tasks(self) -> list[Task]:
        return self.application.get_visible_matrix_tasks()

    def get_archived_tasks(self) -> list[Task]:
        return self.application.get_archived_tasks()

    def visible_tasks_for_quadrant(self, quadrant: str) -> list[Task]:
        return self.application.visible_tasks_for_quadrant(quadrant)

    def get_all_tags(self) -> list[dict[str, str]]:
        tags_by_name: dict[str, dict[str, str]] = {
            tag["name"].casefold(): tag for tag in self._load_tag_catalog()
        }
        for task in self.tasks.values():
            for tag in task.tags:
                name = tag.get("name", "").strip()
                if not name:
                    continue
                tags_by_name.setdefault(
                    name.casefold(),
                    {"name": name, "color": tag.get("color", "#6B7280")},
                )
        return sorted(tags_by_name.values(), key=lambda tag: tag["name"].casefold())

    def get_tag_reference_counts(self) -> dict[str, int]:
        counts = {tag["name"].casefold(): 0 for tag in self.get_all_tags()}
        for task in self.tasks.values():
            for tag in task.tags:
                name = tag.get("name", "").strip()
                if name:
                    counts[name.casefold()] = counts.get(name.casefold(), 0) + 1
        return counts

    def rename_tag(self, old_name: str, new_name: str, color: str) -> None:
        old_key = old_name.casefold()
        new_name = new_name.strip()
        if not new_name:
            return
        new_key = new_name.casefold()
        for task in self.tasks.values():
            updated = []
            has_new = False
            changed = False
            for tag in task.tags:
                tag_key = tag.get("name", "").casefold()
                if tag_key == new_key and tag_key != old_key:
                    has_new = True
                    updated.append({"name": new_name, "color": color})
                elif tag_key == old_key:
                    changed = True
                    if not has_new:
                        updated.append({"name": new_name, "color": color})
                        has_new = True
                else:
                    updated.append(tag)
            if changed:
                task.tags = self._dedupe_tags(updated)
        catalog = [
            tag for tag in self.get_all_tags() if tag["name"].casefold() not in {old_key, new_key}
        ]
        catalog.append({"name": new_name, "color": color})
        self._save_tag_catalog(catalog)
        self.save_data()

    def delete_tag(self, name: str) -> None:
        key = name.casefold()
        for task in self.tasks.values():
            task.tags = [tag for tag in task.tags if tag.get("name", "").casefold() != key]
        catalog = [tag for tag in self.get_all_tags() if tag["name"].casefold() != key]
        self._save_tag_catalog(catalog)
        self.save_data()

    def merge_tag(self, source_name: str, target_tag: dict[str, str]) -> None:
        source_key = source_name.casefold()
        target_name = target_tag["name"].strip()
        target_key = target_name.casefold()
        if not target_name or source_key == target_key:
            return

        for task in self.tasks.values():
            has_source = any(tag.get("name", "").casefold() == source_key for tag in task.tags)
            if not has_source:
                continue
            has_target = any(tag.get("name", "").casefold() == target_key for tag in task.tags)
            task.tags = [tag for tag in task.tags if tag.get("name", "").casefold() != source_key]
            if not has_target:
                task.tags.append({"name": target_name, "color": target_tag.get("color", "#6B7280")})
            task.tags = self._dedupe_tags(task.tags)

        catalog = [
            tag
            for tag in self.get_all_tags()
            if tag["name"].casefold() not in {source_key, target_key}
        ]
        catalog.append({"name": target_name, "color": target_tag.get("color", "#6B7280")})
        self._save_tag_catalog(catalog)
        self.save_data()

    def prune_stale_tags(self) -> int:
        referenced = self._recent_reference_keys()
        stale = [
            tag
            for tag in self.get_all_tags()
            if tag["name"].casefold() not in referenced
        ]
        for tag in stale:
            key = tag["name"].casefold()
            for task in self.tasks.values():
                task.tags = [item for item in task.tags if item.get("name", "").casefold() != key]
        kept = [tag for tag in self.get_all_tags() if tag["name"].casefold() in referenced]
        self._save_tag_catalog(kept)
        self.save_data()
        return len(stale)

    def check_reminders(self) -> None:
        self._dispatch(CheckReminders())

    def _recent_reference_keys(self) -> set[str]:
        cutoff = datetime.now() - timedelta(days=90)
        referenced = set()
        for task in self.tasks.values():
            if task.completed:
                completed_at = self._parse_datetime(task.completed_at)
                if completed_at is None or completed_at < cutoff:
                    continue
            for tag in task.tags:
                name = tag.get("name", "").strip()
                if name:
                    referenced.add(name.casefold())
        return referenced

    def _load_tag_catalog(self) -> list[dict[str, str]]:
        if not self.tags_filepath.exists():
            return []
        try:
            with self.tags_filepath.open("r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except (OSError, json.JSONDecodeError, TypeError):
            return []
        return self._dedupe_tags(raw if isinstance(raw, list) else [])

    def _save_tag_catalog(self, tags: list[dict[str, str]]) -> None:
        self.tags_filepath.parent.mkdir(parents=True, exist_ok=True)
        with self.tags_filepath.open("w", encoding="utf-8") as handle:
            json.dump(self._dedupe_tags(tags), handle, ensure_ascii=False, indent=2)

    def _sync_catalog_from_tags(self, tags: list[dict[str, str]]) -> None:
        if not tags:
            return
        merged = self.get_all_tags() + tags
        self._save_tag_catalog(merged)

    def _dedupe_tags(self, tags: list[dict[str, str]]) -> list[dict[str, str]]:
        deduped = []
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
            deduped.append({"name": name, "color": color})
        return sorted(deduped, key=lambda tag: tag["name"].casefold())

    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _dispatch(self, command):
        return self.application.dispatch(command, context=self.context)

    def _handle_task_changed(self, event) -> None:
        self.data_changed.emit()

    def _handle_reminder_triggered(self, event) -> None:
        self.reminder_triggered.emit(event.title, event.task_id)
