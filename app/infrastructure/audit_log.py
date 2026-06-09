from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonlAuditLog:
    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)

    def append(self, record: dict[str, Any]) -> None:
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        with self.filepath.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
