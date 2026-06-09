from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from app.models.task import Task


class JsonTaskRepository:
    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)

    def load_all(self) -> dict[str, Task]:
        if not self.filepath.exists():
            return {}

        try:
            with self.filepath.open("r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except (OSError, json.JSONDecodeError, TypeError):
            return {}

        if not isinstance(raw, dict):
            return {}

        tasks = {}
        for task_id, payload in raw.items():
            if not isinstance(payload, dict):
                continue
            task = Task.from_dict(payload, fallback_id=task_id)
            tasks[task.id] = task
        return tasks

    def save_all(self, tasks: dict[str, Task]) -> None:
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        data = {task_id: asdict(task) for task_id, task in tasks.items()}
        with self.filepath.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
