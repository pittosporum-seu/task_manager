from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class AddTask:
    title: str
    description: str = ""
    due_date: Optional[str] = None
    has_time: bool = False
    reminder_minutes: Optional[int] = None
    quadrant: str = "inbox"


@dataclass(frozen=True)
class UpdateTask:
    task_id: str
    title: str
    description: str
    due_date: Optional[str]
    has_time: bool
    reminder_minutes: Optional[int]


@dataclass(frozen=True)
class DeleteTask:
    task_id: str


@dataclass(frozen=True)
class MoveTask:
    task_id: str
    new_quadrant: str


@dataclass(frozen=True)
class CompleteTask:
    task_id: str
    completed_at: Optional[str] = None


@dataclass(frozen=True)
class ReopenTask:
    task_id: str


@dataclass(frozen=True)
class CheckReminders:
    now: Optional[datetime] = None


TaskCommand = (
    AddTask | UpdateTask | DeleteTask | MoveTask | CompleteTask | ReopenTask | CheckReminders
)
