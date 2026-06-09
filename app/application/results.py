from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.application.events import ApplicationEvent


@dataclass
class CommandResult:
    ok: bool
    message: str = ""
    changed: bool = False
    task_id: Optional[str] = None
    data: dict[str, Any] = field(default_factory=dict)
    events: list[ApplicationEvent] = field(default_factory=list)
