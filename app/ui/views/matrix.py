from datetime import datetime
from typing import Dict, List

from PyQt6.QtCore import QPoint, QSize, Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QLabel, QGridLayout, QListWidgetItem, QMenu, QVBoxLayout, QWidget

from app.config import QUADRANT_CONFIGS, STYLE_MENU, style_quadrant_container, style_quadrant_header
from app.resources.strings import Strings
from app.services.task_service import TaskService
from app.ui.components.draggable_list import DraggableListWidget
from app.ui.components.task_card import TaskCardWidget
from app.ui.components.task_dialog import TaskDialog


class MatrixView(QWidget):
    def __init__(self, service: TaskService, parent=None):
        super().__init__(parent)
        self.service = service
        self.lists: Dict[str, DraggableListWidget] = {}
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QGridLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        for conf in QUADRANT_CONFIGS:
            container = QWidget()
            container.setStyleSheet(style_quadrant_container(conf["bg"]))
            v_layout = QVBoxLayout(container)
            v_layout.setContentsMargins(12, 12, 12, 12)
            v_layout.setSpacing(10)

            header = QLabel(conf["title"])
            header.setStyleSheet(style_quadrant_header(conf["text"]))
            v_layout.addWidget(header)

            list_widget = DraggableListWidget(conf["id"], self.service)
            list_widget.itemDoubleClicked.connect(self.handle_double_click)
            list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            list_widget.customContextMenuRequested.connect(
                lambda pos, lw=list_widget: self.show_context_menu(pos, lw)
            )

            self.lists[conf["id"]] = list_widget
            v_layout.addWidget(list_widget)
            layout.addWidget(container, conf["row"], conf["col"])

    def refresh(self) -> None:
        for list_widget in self.lists.values():
            list_widget.clear()

        for task in self.visible_tasks():
            list_widget = self.lists.get(task.quadrant)
            if not list_widget:
                continue

            current_width = list_widget.viewport().width() - 20
            if current_width <= 0:
                current_width = 200

            item = QListWidgetItem(list_widget)
            item.setData(Qt.ItemDataRole.UserRole, task.id)

            widget = TaskCardWidget(task, on_status_change=self.service.toggle_complete)
            height = widget.update_preferred_height(current_width)
            item.setSizeHint(QSize(current_width, height))
            list_widget.setItemWidget(item, widget)

    def visible_tasks(self) -> List:
        today = datetime.now().strftime("%Y-%m-%d")
        tasks = []
        for task in self.service.tasks.values():
            if task.quadrant == "inbox":
                continue
            if not task.completed:
                tasks.append(task)
            elif task.completed_at and task.completed_at.startswith(today):
                tasks.append(task)

        tasks.sort(
            key=lambda task: (
                task.completed,
                task.due_date is None or task.due_date == "",
                task.due_date or "",
            )
        )
        return tasks

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refresh()

    def handle_double_click(self, item) -> None:
        task_id = item.data(Qt.ItemDataRole.UserRole)
        task = self.service.tasks.get(task_id)
        if task:
            self.open_task_dialog(task)

    def show_context_menu(self, pos: QPoint, list_widget: DraggableListWidget) -> None:
        item = list_widget.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)
        menu.setStyleSheet(STYLE_MENU)
        delete_action = QAction(Strings.get("menu_delete"), self)
        delete_action.triggered.connect(
            lambda: self.service.delete_task(item.data(Qt.ItemDataRole.UserRole))
        )
        menu.addAction(delete_action)
        menu.exec(list_widget.mapToGlobal(pos))

    def open_task_dialog(self, task) -> None:
        dialog = TaskDialog(self, task)
        if dialog.exec():
            data = dialog.result_data
            self.service.update_task(
                task.id,
                data["title"],
                data["description"],
                data["due_date"],
                data["has_time"],
                data["reminder_minutes"],
            )

