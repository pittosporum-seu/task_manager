from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Callable, Iterable, List, Optional

from app.models.task import Task


QUADRANT_META = (
    {
        "id": "q1",
        "title_key": "q1_title",
        "row": 0,
        "col": 0,
        "bg": "#FEF2F2",
        "text": "#7F1D1D",
    },
    {
        "id": "q2",
        "title_key": "q2_title",
        "row": 0,
        "col": 1,
        "bg": "#EFF6FF",
        "text": "#1E3A8A",
    },
    {
        "id": "q3",
        "title_key": "q3_title",
        "row": 1,
        "col": 0,
        "bg": "#ECFDF5",
        "text": "#065F46",
    },
    {
        "id": "q4",
        "title_key": "q4_title",
        "row": 1,
        "col": 1,
        "bg": "#F3F4F6",
        "text": "#4B5563",
    },
)


def build_quadrant_configs(title_resolver: Callable[[str], str]) -> list[dict]:
    configs = []
    for quadrant in QUADRANT_META:
        item = dict(quadrant)
        item["title"] = title_resolver(item.pop("title_key"))
        configs.append(item)
    return configs


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


def archived_tasks(tasks: Iterable[Task]) -> List[Task]:
    completed = [task for task in tasks if task.completed]
    return sorted(completed, key=lambda task: task.completed_at or "", reverse=True)


def should_trigger_reminder(task: Task, now: Optional[datetime] = None) -> bool:
    if not task.due_date or task.reminder_minutes is None or task.reminder_sent or task.completed:
        return False

    due_at = parse_datetime(task.due_date)
    if due_at is None:
        return False

    trigger_at = due_at - timedelta(minutes=task.reminder_minutes)
    return (now or datetime.now()) >= trigger_at
