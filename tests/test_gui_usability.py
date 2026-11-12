from app.services.task_service import TaskService
from app.ui.components.task_dialog import TaskDialog
from app.ui.views.matrix import MatrixView


def test_form_rejects_invalid_input_and_recovers(qapp):
    dialog = TaskDialog()
    assert not dialog.save_button.isEnabled()
    dialog.title_edit.setText("A task")
    assert dialog.save_button.isEnabled()
    dialog.desc_edit.setPlainText("x" * 2001)
    assert not dialog.save_button.isEnabled()
    assert dialog.validation_label.text()
    dialog.desc_edit.setPlainText("Valid description")
    assert dialog.save_button.isEnabled()
    dialog.save_task()
    assert dialog.result_data["title"] == "A task"


def test_filter_can_be_cleared_without_matching_card(tmp_path, qapp):
    service = TaskService(str(tmp_path / "tasks.db"), enable_timer=False)
    service.add_task("Task", quadrant="q1")
    view = MatrixView(service)
    view.filter_by_tag("missing")
    assert view.lists["q1"].count() == 0
    assert not view.clear_filter.isHidden()
    view.reset_filter()
    assert view.lists["q1"].count() == 1
    assert view.clear_filter.isHidden()
