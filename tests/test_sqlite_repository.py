import json

from app.application.commands import AddTask, DeleteTask, MoveTask
from app.application.context import CommandContext
from app.application.task_app import TaskApplication
from app.infrastructure.sqlite_repository import SqliteRepository


def test_independent_connections(tmp_path):
    first = SqliteRepository(tmp_path / "tasks.db")
    second = SqliteRepository(tmp_path / "tasks.db")
    a = TaskApplication(first, audit_log=first)
    b = TaskApplication(second, audit_log=second)
    one = a.dispatch(AddTask(title="one")).task_id
    two = b.dispatch(AddTask(title="two")).task_id
    assert a.dispatch(MoveTask(one, "q1")).ok
    assert set(first.load_all()) == {one, two}
    assert b.dispatch(DeleteTask(one), CommandContext(dry_run=True)).would_change
    assert set(second.load_all()) == {one, two}


def test_migration_is_once_and_preserves_source(tmp_path):
    source = tmp_path / "tasks.json"
    content = json.dumps({"legacy": {"title": "old"}})
    source.write_text(content, encoding="utf-8")
    repository = SqliteRepository(tmp_path / "tasks.db")
    assert repository.load_all()["legacy"].id == "legacy"
    assert TaskApplication(repository).dispatch(DeleteTask("legacy")).ok
    assert SqliteRepository(tmp_path / "tasks.db").load_all() == {}
    assert source.read_text(encoding="utf-8") == content
