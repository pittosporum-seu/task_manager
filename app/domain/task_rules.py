from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable, List, Optional

from app.models.task import Task


QUADRANT_DEFINITIONS = (
    {"id": "q1", "title_key": "q1_title"},
    {"id": "q2", "title_key": "q2_title"},
    {"id": "q3", "title_key": "q3_title"},
    {"id": "q4", "title_key": "q4_title"},
)
VALID_QUADRANTS = ("inbox",) + tuple(definition["id"] for definition in QUADRANT_DEFINITIONS)


def is_valid_quadrant(quadrant_id: str) -> bool:
    return quadrant_id in VALID_QUADRANTS


def today_key(now: Optional[datetime | date] = None) -> str:
    current = now or datetime.now()
    return current.strftime("%Y-%m-%d")


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def is_completed_today(task: Task, today: Optional[str] = None) -> bool:
    if not task.completed or not task.completed_at:
        return False
    return task.completed_at.startswith(today or today_key())


def is_visible_active_task(task: Task, today: Optional[str] = None) -> bool:
    return not task.completed or is_completed_today(task, today)


def task_sort_key(task: Task) -> tuple[bool, bool, str]:
    return (
        task.completed,
        task.due_date is None or task.due_date == "",
        task.due_date or "",
    )


def visible_active_tasks(
    tasks: Iterable[Task],
    *,
    quadrant_id: Optional[str] = None,
    today: Optional[str] = None,
) -> List[Task]:
    visible = []
    current_day = today or today_key()
    for task in tasks:
        if quadrant_id is not None and task.quadrant != quadrant_id:
            continue
        if is_visible_active_task(task, current_day):
            visible.append(task)
    return sorted(visible, key=task_sort_key)


def visible_inbox_tasks(tasks: Iterable[Task], *, today: Optional[str] = None) -> List[Task]:
    return visible_active_tasks(tasks, quadrant_id="inbox", today=today)


def visible_matrix_tasks(tasks: Iterable[Task], *, today: Optional[str] = None) -> List[Task]:
    visible = [
        task
        for task in tasks
        if task.quadrant != "inbox" and is_visible_active_task(task, today or today_key())
    ]
    return sorted(visible, key=task_sort_key)


def archived_tasks(tasks: Iterable[Task], *, today: Optional[str] = None) -> List[Task]:
    archive_day = today or today_key()
    completed = [
        task for task in tasks if task.completed and not is_completed_today(task, archive_day)
    ]
    return sorted(completed, key=lambda task: task.completed_at or "", reverse=True)


def should_trigger_reminder(task: Task, now: Optional[datetime] = None) -> bool:
    if not task.due_date or task.reminder_minutes is None or task.reminder_sent or task.completed:
        return False

    due_at = parse_datetime(task.due_date)
    if due_at is None:
        return False

    trigger_at = due_at - timedelta(minutes=task.reminder_minutes)
    return (now or datetime.now()) >= trigger_at
