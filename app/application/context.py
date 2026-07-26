from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandContext:
    source: str = "ui"
    dry_run: bool = False
    request_id: str | None = None
    actor: str | None = None
