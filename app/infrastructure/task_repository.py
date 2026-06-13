from __future__ import annotations

from typing import Protocol

from app.models.task import Task


class TaskRepository(Protocol):
    def load_all(self) -> dict[str, Task]:
        raise NotImplementedError

    def save_all(self, tasks: dict[str, Task]) -> None:
        raise NotImplementedError
