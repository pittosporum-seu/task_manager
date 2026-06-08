from PyQt6.QtCore import QByteArray, QMimeData, QPoint, Qt
from PyQt6.QtGui import QDrag
from PyQt6.QtWidgets import QAbstractItemView, QApplication, QListWidget

from app.services.task_service import TaskService


class DraggableListWidget(QListWidget):
    MIME_TYPE = "application/x-quadrant-task-id"

    def __init__(self, quadrant_id: str, service: TaskService):
        super().__init__()
        self.quadrant_id = quadrant_id
        self.service = service
        self._drag_start_pos = QPoint()
        self._drag_task_id = None

        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def mousePressEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        self._drag_task_id = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        self._drag_start_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self._drag_task_id:
            super().mouseMoveEvent(event)
            return

        distance = (event.position().toPoint() - self._drag_start_pos).manhattanLength()
        if distance < QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return

        mime_data = QMimeData()
        mime_data.setData(self.MIME_TYPE, QByteArray(self._drag_task_id.encode("utf-8")))

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(self.MIME_TYPE):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(self.MIME_TYPE):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if not event.mimeData().hasFormat(self.MIME_TYPE):
            super().dropEvent(event)
            return

        task_id = bytes(event.mimeData().data(self.MIME_TYPE)).decode("utf-8")
        self.service.move_task(task_id, self.quadrant_id)
        event.acceptProposedAction()
