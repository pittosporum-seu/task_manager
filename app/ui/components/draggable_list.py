from PyQt6.QtCore import QByteArray, QMimeData, QPoint, QSize, Qt
from PyQt6.QtGui import QDrag, QPainter, QPixmap
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QListWidget,
)

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
        self.drop_indicator = QFrame(self.viewport())
        self.drop_indicator.setStyleSheet(
            """
            background: qlineargradient(
                x1: 0, y1: 0,
                x2: 1, y2: 0,
                stop: 0 rgba(37, 99, 235, 0),
                stop: 0.18 rgba(37, 99, 235, 210),
                stop: 0.5 rgba(37, 99, 235, 255),
                stop: 0.82 rgba(37, 99, 235, 210),
                stop: 1 rgba(37, 99, 235, 0)
            );
            border-radius: 2px;
            min-height: 4px;
            """
        )
        glow = QGraphicsDropShadowEffect(self.drop_indicator)
        glow.setBlurRadius(18)
        glow.setColor(QColor(37, 99, 235, 180))
        glow.setOffset(0, 0)
        self.drop_indicator.setGraphicsEffect(glow)
        self.drop_indicator.hide()

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
        self.apply_drag_preview(drag)
        drag.exec(Qt.DropAction.MoveAction)
        self.hide_drop_indicator()

    def apply_drag_preview(self, drag: QDrag) -> None:
        item = self.itemAt(self._drag_start_pos)
        if item is None:
            return

        widget = self.itemWidget(item)
        if widget is None:
            return

        source = widget.grab()
        if source.isNull():
            return

        target_size = QSize(
            max(1, int(source.width() * 0.82)),
            max(1, int(source.height() * 0.82)),
        )
        scaled = source.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        preview = QPixmap(scaled.size())
        preview.fill(Qt.GlobalColor.transparent)
        painter = QPainter(preview)
        painter.setOpacity(0.72)
        painter.drawPixmap(0, 0, scaled)
        painter.end()

        drag.setPixmap(preview)
        drag.setHotSpot(QPoint(preview.width() // 2, min(preview.height() // 2, 24)))

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(self.MIME_TYPE):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(self.MIME_TYPE):
            self.update_drop_indicator(event.position().toPoint())
            event.acceptProposedAction()
        else:
            self.hide_drop_indicator()
            super().dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        self.hide_drop_indicator()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        if not event.mimeData().hasFormat(self.MIME_TYPE):
            self.hide_drop_indicator()
            super().dropEvent(event)
            return

        task_id = bytes(event.mimeData().data(self.MIME_TYPE)).decode("utf-8")
        insert_index = self.insert_index_at(event.position().toPoint())
        self.hide_drop_indicator()
        self.service.move_task(task_id, self.quadrant_id, insert_index)
        event.acceptProposedAction()

    def insert_index_at(self, pos: QPoint) -> int:
        for index in range(self.count()):
            rect = self.visualItemRect(self.item(index))
            if pos.y() < rect.center().y():
                return index
        return self.count()

    def update_drop_indicator(self, pos: QPoint) -> None:
        index = self.insert_index_at(pos)
        if self.count() == 0:
            y = 6
        elif index >= self.count():
            y = self.visualItemRect(self.item(self.count() - 1)).bottom() + 4
        else:
            y = self.visualItemRect(self.item(index)).top() - 3

        width = max(40, int((self.viewport().width() - 20) * 0.75))
        x = max(10, (self.viewport().width() - width) // 2)
        self.drop_indicator.setGeometry(x, max(2, y), width, 4)
        self.drop_indicator.raise_()
        self.drop_indicator.show()

    def hide_drop_indicator(self) -> None:
        self.drop_indicator.hide()
