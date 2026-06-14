from app.services.task_service import TaskService
from app.ui.components.task_dialog import DateTimePickerPopup, TaskDialog
from app.ui.views.archive_dialog import ArchiveDialog
from app.ui.views.matrix import MatrixView
from app.ui.views.sidebar import SidebarView


def make_service(tmp_path):
    return TaskService(filename=str(tmp_path / "ui_tasks.json"), enable_timer=False)


def test_ui_smoke_workflow(tmp_path, qapp):
    service = make_service(tmp_path)
    task = service.add_task(
        title="Smoke test task with a long enough title to wrap inside the card width",
        description="Created by automated smoke test.",
        due_date="2026-06-09T09:30",
        has_time=True,
        reminder_minutes=5,
    )

    sidebar = SidebarView(service)
    sidebar.refresh()
    assert sidebar.inbox_list.count() == 1

    service.move_task(task.id, "q1")
    matrix = MatrixView(service)
    matrix.refresh()
    assert matrix.lists["q1"].count() == 1

    service.toggle_complete(task.id, True)
    archive = ArchiveDialog(service)
    archive.load_data()
    archive.adjust_layout()
    assert archive.list_widget.count() == 0

    historical_task = service.add_task("Historical done", quadrant="q2")
    service.toggle_complete(historical_task.id, True, completed_at="2026-06-07T10:00:00")
    archive.load_data()
    archive.adjust_layout()
    assert archive.list_widget.count() == 1

    archive.close()
    matrix.close()
    sidebar.close()


def test_matrix_filters_by_double_clicked_tag(tmp_path, qapp):
    service = make_service(tmp_path)
    work = {"name": "Work", "color": "#2563EB"}
    home = {"name": "Home", "color": "#059669"}
    service.add_task("Work task", quadrant="q1", tags=[work])
    service.add_task("Home task", quadrant="q1", tags=[home])

    matrix = MatrixView(service)
    matrix.refresh()
    assert matrix.lists["q1"].count() == 2

    matrix.filter_by_tag("Work")
    assert matrix.lists["q1"].count() == 1

    matrix.filter_by_tag("Work")
    assert matrix.lists["q1"].count() == 2
    assert service.get_all_tags() == [home, work]

    matrix.close()


def test_new_task_dialog_due_date_defaults(qapp):
    dialog = TaskDialog()

    assert dialog.has_date_check.isChecked()
    assert not dialog.has_time_check.isChecked()
    assert dialog.due_edit.isEnabled()
    assert dialog.due_edit.displayFormat() == "yyyy-MM-dd"

    dialog.close()


def test_date_time_picker_shows_time_panel_only_when_needed(qapp):
    dialog = TaskDialog()

    picker_with_time = DateTimePickerPopup(dialog, include_time=True)
    assert picker_with_time.include_time
    assert not picker_with_time.time_panel.isHidden()
    picker_with_time.hour_spin.setValue(18)
    picker_with_time.minute_spin.setValue(45)
    picker_with_time.apply_selection()
    assert dialog.due_edit.time().hour() == 18
    assert dialog.due_edit.time().minute() == 45
    picker_with_time.close()

    picker_without_time = DateTimePickerPopup(dialog, include_time=False)
    assert picker_without_time.time_panel.isHidden()
    picker_without_time.close()

    dialog.close()
