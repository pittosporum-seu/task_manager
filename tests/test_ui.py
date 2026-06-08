from app.services.task_service import TaskService
from app.ui.views.archive_dialog import ArchiveDialog
from app.ui.views.matrix import MatrixView
from app.ui.views.sidebar import SidebarView


def make_service(tmp_path):
    service = TaskService(filename=str(tmp_path / "ui_tasks.json"))
    service.timer.stop()
    return service


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
    assert archive.list_widget.count() == 1

    archive.close()
    matrix.close()
    sidebar.close()
