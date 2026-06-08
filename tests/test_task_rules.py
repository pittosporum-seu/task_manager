from datetime import datetime

from app.domain.task_rules import (
    QUADRANT_DEFINITIONS,
    archived_tasks,
    should_trigger_reminder,
    visible_inbox_tasks,
    visible_matrix_tasks,
)
from app.models.task import Task


def make_task(
    task_id,
    *,
    quadrant="inbox",
    due_date=None,
    completed=False,
    completed_at=None,
    reminder_minutes=None,
    reminder_sent=False,
):
    return Task(
        id=task_id,
        title=task_id,
        quadrant=quadrant,
        created_at="2026-06-08T08:00:00",
        due_date=due_date,
        completed=completed,
        completed_at=completed_at,
        reminder_minutes=reminder_minutes,
        reminder_sent=reminder_sent,
    )


def test_visible_inbox_tasks_filters_and_sorts():
    tasks = [
        make_task("no_due"),
        make_task("due_early", due_date="2026-06-08T09:00:00"),
        make_task("old_done", completed=True, completed_at="2026-06-07T20:00:00"),
        make_task("today_done", completed=True, completed_at="2026-06-08T12:00:00"),
        make_task("other_quadrant", quadrant="q1", due_date="2026-06-08T08:00:00"),
    ]

    result = visible_inbox_tasks(tasks, today="2026-06-08")

    assert [task.id for task in result] == ["due_early", "no_due", "today_done"]


def test_visible_matrix_tasks_excludes_inbox_and_old_completed():
    tasks = [
        make_task("inbox", quadrant="inbox"),
        make_task("q2_open", quadrant="q2", due_date="2026-06-08T10:00:00"),
        make_task("q1_open", quadrant="q1", due_date="2026-06-08T09:00:00"),
        make_task("q3_old_done", quadrant="q3", completed=True, completed_at="2026-06-07T10:00:00"),
        make_task(
            "q4_today_done", quadrant="q4", completed=True, completed_at="2026-06-08T11:00:00"
        ),
    ]

    result = visible_matrix_tasks(tasks, today="2026-06-08")

    assert [task.id for task in result] == ["q1_open", "q2_open", "q4_today_done"]


def test_archived_tasks_are_historical_completed_and_newest_first():
    tasks = [
        make_task("open"),
        make_task("done_old", completed=True, completed_at="2026-06-07T10:00:00"),
        make_task("done_new", completed=True, completed_at="2026-06-06T10:00:00"),
        make_task("done_today", completed=True, completed_at="2026-06-08T10:00:00"),
    ]

    result = archived_tasks(tasks, today="2026-06-08")

    assert [task.id for task in result] == ["done_old", "done_new"]


def test_should_trigger_reminder():
    task = make_task(
        "reminder",
        due_date="2026-06-08T10:00:00",
        reminder_minutes=30,
    )

    assert not should_trigger_reminder(task, now=datetime(2026, 6, 8, 9, 29))
    assert should_trigger_reminder(task, now=datetime(2026, 6, 8, 9, 30))

    task.reminder_sent = True
    assert not should_trigger_reminder(task, now=datetime(2026, 6, 8, 9, 31))


def test_quadrant_definitions_are_domain_only():
    assert QUADRANT_DEFINITIONS[0] == {"id": "q1", "title_key": "q1_title"}
    assert "row" not in QUADRANT_DEFINITIONS[0]
    assert "bg" not in QUADRANT_DEFINITIONS[0]
