from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QSystemTrayIcon, QWidget

from app.config import APP_LOGO_PATH
from app.resources.strings import Strings
from app.services.task_service import TaskService
from app.ui.views.matrix import MatrixView
from app.ui.views.sidebar import SidebarView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(Strings.get("window_main_title"))
        self.setWindowIcon(QIcon(APP_LOGO_PATH))
        self.resize(1100, 750)

        self.service = TaskService()
        self.tray_icon = None
        self.setup_tray()
        self.setup_ui()

        self.service.data_changed.connect(self.refresh_all_views)
        self.service.reminder_triggered.connect(self.show_notification)
        self.refresh_all_views()

    def setup_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(APP_LOGO_PATH))
        self.tray_icon.show()

    def setup_ui(self) -> None:
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = SidebarView(self.service)
        self.matrix = MatrixView(self.service)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.matrix, 1)

    def refresh_all_views(self) -> None:
        self.sidebar.refresh()
        self.matrix.refresh()

    def show_notification(self, title: str, task_id: str) -> None:
        if self.tray_icon is None:
            return
        self.tray_icon.showMessage(
            Strings.get("notification_title"),
            Strings.get("notification_body", title=title),
            QSystemTrayIcon.MessageIcon.Information,
            5000,
        )

    def closeEvent(self, event):
        if self.tray_icon is not None:
            self.tray_icon.hide()
        super().closeEvent(event)
