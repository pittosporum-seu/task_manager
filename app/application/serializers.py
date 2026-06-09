from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from app.application.events import ApplicationEvent
from app.application.results import CommandResult
from app.models.task import Task


def task_to_dict(task: Task) -> dict[str, Any]:
    return asdict(task)


def event_to_dict(event: ApplicationEvent) -> dict[str, Any]:
    data = asdict(event)
    data["type"] = type(event).__name__
    return data


def command_result_to_dict(result: CommandResult) -> dict[str, Any]:
    return {
        "ok": result.ok,
        "message": result.message,
        "changed": result.changed,
        "task_id": result.task_id,
        "data": _json_ready(result.data),
        "events": [event_to_dict(event) for event in result.events],
    }


def _json_ready(value):
    if isinstance(value, Task):
        return task_to_dict(value)
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value
