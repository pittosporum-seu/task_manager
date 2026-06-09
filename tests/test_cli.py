import json

from app.cli import main


def run_cli(capsys, data_file, *args):
    exit_code = main(["--file", str(data_file), *args])
    output = capsys.readouterr().out
    return exit_code, json.loads(output)


def test_cli_add_update_list_and_archive_flow(tmp_path, capsys):
    data_file = tmp_path / "tasks.json"

    exit_code, payload = run_cli(
        capsys,
        data_file,
        "add",
        "CLI task",
        "--description",
        "Created from CLI",
        "--quadrant",
        "q1",
        "--due-date",
        "2026-06-09T09:30",
        "--has-time",
        "--reminder-minutes",
        "5",
    )
    assert exit_code == 0
    task_id = payload["task_id"]
    assert payload["changed"]
    assert payload["events"][0]["type"] == "TaskChanged"

    exit_code, payload = run_cli(capsys, data_file, "list", "--view", "matrix")
    assert exit_code == 0
    assert [task["id"] for task in payload["data"]["tasks"]] == [task_id]

    exit_code, payload = run_cli(
        capsys,
        data_file,
        "update",
        task_id,
        "--title",
        "Updated CLI task",
        "--clear-due-date",
    )
    assert exit_code == 0
    assert payload["changed"]

    exit_code, payload = run_cli(capsys, data_file, "get", task_id)
    assert exit_code == 0
    assert payload["data"]["task"]["title"] == "Updated CLI task"
    assert payload["data"]["task"]["due_date"] is None

    exit_code, _ = run_cli(
        capsys,
        data_file,
        "complete",
        task_id,
        "--completed-at",
        "2026-06-07T10:00:00",
    )
    assert exit_code == 0

    exit_code, payload = run_cli(capsys, data_file, "list", "--view", "archive")
    assert exit_code == 0
    assert [task["id"] for task in payload["data"]["tasks"]] == [task_id]


def test_cli_check_reminders_outputs_events(tmp_path, capsys):
    data_file = tmp_path / "tasks.json"
    _, add_payload = run_cli(
        capsys,
        data_file,
        "add",
        "Reminder",
        "--due-date",
        "2026-06-08T10:00:00",
        "--has-time",
        "--reminder-minutes",
        "30",
    )
    task_id = add_payload["task_id"]

    exit_code, payload = run_cli(
        capsys,
        data_file,
        "check-reminders",
        "--now",
        "2026-06-08T09:30:00",
    )

    assert exit_code == 0
    assert payload["changed"]
    assert payload["data"]["reminders"] == [{"task_id": task_id, "title": "Reminder"}]
    assert [event["type"] for event in payload["events"]] == [
        "ReminderTriggered",
        "TaskChanged",
    ]


def test_cli_returns_failure_for_invalid_command_data(tmp_path, capsys):
    data_file = tmp_path / "tasks.json"

    exit_code, payload = run_cli(capsys, data_file, "add", "Title", "--quadrant", "bad")

    assert exit_code == 1
    assert not payload["ok"]
    assert payload["message"] == "Invalid quadrant"

    exit_code, payload = run_cli(capsys, data_file, "check-reminders", "--now", "bad")

    assert exit_code == 1
    assert not payload["ok"]
    assert payload["message"] == "Invalid datetime"
