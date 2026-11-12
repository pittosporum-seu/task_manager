import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

from app.models.task import Task


class SqliteRepository:
    def __init__(self, filepath):
        path = Path(filepath)
        self.filepath = path.with_suffix(".db") if path.suffix == ".json" else path
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.filepath, timeout=10, isolation_level=None)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS tags (name TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT);
        """)
        with self.transaction():
            if not self.connection.execute(
                "SELECT 1 FROM metadata WHERE key='migrated'"
            ).fetchone():
                legacy = path if path.suffix == ".json" else path.with_suffix(".json")
                if legacy.exists():
                    raw = json.loads(legacy.read_text(encoding="utf-8"))
                    if not isinstance(raw, dict):
                        raise ValueError("Legacy tasks must be an object")
                    self.save_all({k: Task.from_dict(v, fallback_id=k) for k, v in raw.items()})
                tags = path.parent / "tags.json"
                if tags.exists():
                    self.save_catalog(json.loads(tags.read_text(encoding="utf-8")))
                audit = path.parent / "audit.log.jsonl"
                if audit.exists():
                    for line in audit.read_text(encoding="utf-8").splitlines():
                        if line.strip():
                            self.append(json.loads(line))
                self.connection.execute("INSERT INTO metadata VALUES ('migrated', '1')")

    @contextmanager
    def transaction(self):
        if self.connection.in_transaction:
            yield
            return
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.connection.execute("COMMIT")
        except BaseException:
            self.connection.execute("ROLLBACK")
            raise

    def load_all(self):
        return {
            key: Task.from_dict(json.loads(payload), fallback_id=key)
            for key, payload in self.connection.execute("SELECT id, payload FROM tasks")
        }

    def save_all(self, tasks):
        if not self.connection.in_transaction:
            raise RuntimeError("Task writes require a transaction and fresh snapshot")
        self.connection.execute("DELETE FROM tasks")
        self.connection.executemany(
            "INSERT INTO tasks VALUES (?, ?)",
            [(t.id, json.dumps(asdict(t), ensure_ascii=False)) for t in tasks.values()],
        )

    def load_catalog(self):
        return [json.loads(row[0]) for row in self.connection.execute("SELECT payload FROM tags")]

    def save_catalog(self, tags):
        with self.transaction():
            self.connection.execute("DELETE FROM tags")
            self.connection.executemany(
                "INSERT INTO tags VALUES (?, ?)",
                [(t["name"], json.dumps(t, ensure_ascii=False)) for t in tags],
            )

    def append(self, record):
        self.connection.execute(
            "INSERT INTO audit(payload) VALUES (?)", (json.dumps(record, ensure_ascii=False),)
        )
