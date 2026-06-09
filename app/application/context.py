from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CommandContext:
    source: str = "ui"
    dry_run: bool = False
    request_id: Optional[str] = None
    actor: Optional[str] = None
