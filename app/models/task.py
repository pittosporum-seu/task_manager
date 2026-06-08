import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class Task:
    id: str
    title: str
    quadrant: str
    created_at: str
    description: str = ""
    due_date: Optional[str] = None
    has_time: bool = False
    reminder_minutes: Optional[int] = None
    reminder_sent: bool = False
    status: str = "pending"
    completed: bool = False
    completed_at: Optional[str] = None

    @classmethod
    def create(
        cls,
        title: str,
        description: str = "",
        quadrant: str = "inbox",
        due_date: Optional[str] = None,
        has_time: bool = False,
        reminder_minutes: Optional[int] = None,
    ) -> "Task":
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            quadrant=quadrant,
            created_at=datetime.now().isoformat(timespec="seconds"),
            due_date=due_date,
            has_time=has_time,
            reminder_minutes=reminder_minutes,
        )

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Task":
        defaults = {
            "id": str(uuid.uuid4()),
            "title": "Untitled",
            "quadrant": "inbox",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "description": "",
            "due_date": None,
            "has_time": False,
            "reminder_minutes": None,
            "reminder_sent": False,
            "status": "pending",
            "completed": False,
            "completed_at": None,
        }
        fields = cls.__dataclass_fields__.keys()
        data = {**defaults, **{k: v for k, v in payload.items() if k in fields}}
        return cls(**data)
