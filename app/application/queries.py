from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.models.task import Task


TaskView = Literal["all", "inbox", "matrix", "archive"]


@dataclass(frozen=True)
class ListTasks:
    view: TaskView = "all"


@dataclass(frozen=True)
class TaskList:
    view: TaskView
    tasks: list[Task]


def list_tasks(application, query: ListTasks) -> TaskList:
    if query.view == "inbox":
        tasks = application.get_visible_inbox_tasks()
    elif query.view == "matrix":
        tasks = application.get_visible_matrix_tasks()
    elif query.view == "archive":
        tasks = application.get_archived_tasks()
    else:
        tasks = sorted(application.tasks.values(), key=lambda task: task.created_at)
    return TaskList(view=query.view, tasks=tasks)
