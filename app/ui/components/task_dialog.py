from datetime import datetime

from PyQt6.QtCore import QDate, QDateTime, QTime, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from app.config import (
    APP_LOGO_PATH,
    STYLE_BTN_PRIMARY,
    STYLE_BTN_SECONDARY,
    STYLE_CHECKBOX,
    STYLE_COMBOBOX,
    STYLE_DIALOG_CONTAINER,
    STYLE_FORM_LABEL,
    STYLE_INPUT,
)
from app.models.task import Task
from app.resources.strings import Strings


class TaskDialog(QDialog):
    def __init__(self, parent=None, task: Task = None):
        super().__init__(parent)
        self.task = task
        self.result_data = None
        self.reminders = [
            (Strings.get("remind_none"), None),
            (Strings.get("remind_on_time"), 0),
            (Strings.get("remind_5min"), 5),
            (Strings.get("remind_15min"), 15),
            (Strings.get("remind_30min"), 30),
            (Strings.get("remind_1h"), 60),
            (Strings.get("remind_1d"), 1440),
        ]

        title_key = "dialog_edit_title" if task else "dialog_add_title"
        self.setWindowTitle(Strings.get(title_key))
        self.setWindowIcon(QIcon(APP_LOGO_PATH))
        self.setStyleSheet(STYLE_DIALOG_CONTAINER)
        self.resize(500, 560)
        self.setup_ui()
        self.load_task()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 24)
        layout.setSpacing(14)

        lbl_title = QLabel(Strings.get("label_title"))
        lbl_title.setStyleSheet(STYLE_FORM_LABEL)
        layout.addWidget(lbl_title)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText(Strings.get("placeholder_title"))
        self.title_edit.setStyleSheet(STYLE_INPUT)
        layout.addWidget(self.title_edit)

        lbl_desc = QLabel(Strings.get("label_desc"))
        lbl_desc.setStyleSheet(STYLE_FORM_LABEL)
        layout.addWidget(lbl_desc)

        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText(Strings.get("placeholder_desc"))
        self.desc_edit.setStyleSheet(STYLE_INPUT)
        self.desc_edit.setFixedHeight(120)
        layout.addWidget(self.desc_edit)

        self.has_date_check = QCheckBox(Strings.get("label_has_date"))
        self.has_date_check.setStyleSheet(STYLE_CHECKBOX)
        self.has_date_check.stateChanged.connect(self.update_date_controls)
        layout.addWidget(self.has_date_check)

        self.due_edit = QDateTimeEdit()
        self.due_edit.setCalendarPopup(True)
        self.due_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.due_edit.setDateTime(QDateTime.currentDateTime())
        self.due_edit.setStyleSheet(STYLE_INPUT)
        layout.addWidget(self.due_edit)

        self.has_time_check = QCheckBox(Strings.get("label_has_time"))
        self.has_time_check.setStyleSheet(STYLE_CHECKBOX)
        self.has_time_check.stateChanged.connect(self.update_date_controls)
        layout.addWidget(self.has_time_check)

        lbl_reminder = QLabel(Strings.get("label_reminder"))
        lbl_reminder.setStyleSheet(STYLE_FORM_LABEL)
        layout.addWidget(lbl_reminder)

        self.reminder_combo = QComboBox()
        self.reminder_combo.setStyleSheet(STYLE_COMBOBOX)
        for text, value in self.reminders:
            self.reminder_combo.addItem(text, value)
        layout.addWidget(self.reminder_combo)

        layout.addStretch()

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        btn_cancel = QPushButton(Strings.get("btn_cancel"))
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet(STYLE_BTN_SECONDARY)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton(Strings.get("btn_save"))
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet(STYLE_BTN_PRIMARY)
        btn_save.clicked.connect(self.save_task)

        button_layout.addWidget(btn_cancel)
        button_layout.addWidget(btn_save)
        layout.addLayout(button_layout)

        self.update_date_controls()

    def load_task(self) -> None:
        if not self.task:
            return

        self.title_edit.setText(self.task.title)
        self.desc_edit.setPlainText(self.task.description)

        has_due_date = bool(self.task.due_date)
        self.has_date_check.setChecked(has_due_date)
        self.has_time_check.setChecked(bool(self.task.has_time))
        if self.task.due_date:
            try:
                due_at = datetime.fromisoformat(self.task.due_date)
                self.due_edit.setDateTime(
                    QDateTime(
                        QDate(due_at.year, due_at.month, due_at.day),
                        QTime(due_at.hour, due_at.minute),
                    )
                )
            except ValueError:
                pass

        for index, (_, value) in enumerate(self.reminders):
            if value == self.task.reminder_minutes:
                self.reminder_combo.setCurrentIndex(index)
                break
        self.update_date_controls()

    def update_date_controls(self) -> None:
        has_date = self.has_date_check.isChecked()
        has_time = self.has_time_check.isChecked()
        self.due_edit.setEnabled(has_date)
        self.has_time_check.setEnabled(has_date)
        self.reminder_combo.setEnabled(has_date)
        self.due_edit.setDisplayFormat("yyyy-MM-dd HH:mm" if has_time else "yyyy-MM-dd")

    def save_task(self) -> None:
        title = self.title_edit.text().strip()
        if not title:
            return

        due_date = None
        has_time = False
        if self.has_date_check.isChecked():
            has_time = self.has_time_check.isChecked()
            due_dt = self.due_edit.dateTime().toPyDateTime()
            if not has_time:
                due_dt = due_dt.replace(hour=23, minute=59, second=59, microsecond=0)
            due_date = due_dt.isoformat(timespec="minutes" if has_time else "seconds")

        self.result_data = {
            "title": title,
            "description": self.desc_edit.toPlainText().strip(),
            "due_date": due_date,
            "has_time": has_time,
            "reminder_minutes": self.reminder_combo.currentData() if due_date else None,
        }
        self.accept()
