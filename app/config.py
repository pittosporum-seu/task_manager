from pathlib import Path

from app.domain.task_rules import QUADRANT_DEFINITIONS
from app.resources.strings import Strings


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
LANGUAGE = "cn"
Strings.current_lang = LANGUAGE


def resource_path(*parts: str) -> str:
    return (BASE_DIR / "app" / "resources" / "imgs" / Path(*parts)).as_posix()


APP_LOGO_PATH = resource_path("app_logo.svg")
ICON_INBOX_PATH = resource_path("icon_inbox.svg")
ICON_ARCHIVE_PATH = resource_path("icon_archive.svg")
ICON_MATRIX_PATH = resource_path("icon_matrix.svg")
CHECKBOX_UNCHECKED_PATH = resource_path("checkbox_unchecked.svg")
CHECKBOX_CHECKED_PATH = resource_path("checkbox_checked.svg")

COLORS = {
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "text_main": "#111827",
    "text_muted": "#6B7280",
    "text_light": "#9CA3AF",
    "surface": "#FFFFFF",
    "surface_soft": "#F9FAFB",
    "bg_gray": "#F3F4F6",
    "border": "#E5E7EB",
    "border_hover": "#D1D5DB",
    "danger": "#DC2626",
    "warning": "#D97706",
    "blue_soft": "#EFF6FF",
}

_QUADRANT_PRESENTATION = {
    "q1": {"row": 0, "col": 0, "bg": "#FEF2F2", "text": "#7F1D1D"},
    "q2": {"row": 0, "col": 1, "bg": "#EFF6FF", "text": "#1E3A8A"},
    "q3": {"row": 1, "col": 0, "bg": "#ECFDF5", "text": "#065F46"},
    "q4": {"row": 1, "col": 1, "bg": "#F3F4F6", "text": "#4B5563"},
}


def build_quadrant_configs() -> list[dict]:
    configs = []
    for definition in QUADRANT_DEFINITIONS:
        quadrant_id = definition["id"]
        configs.append(
            {
                "id": quadrant_id,
                "title": Strings.get(definition["title_key"]),
                **_QUADRANT_PRESENTATION[quadrant_id],
            }
        )
    return configs


QUADRANT_CONFIGS = build_quadrant_configs()

GLOBAL_STYLES = f"""
    QMainWindow {{
        background-color: {COLORS["surface_soft"]};
    }}
    QWidget#sidebar {{
        background-color: {COLORS["surface"]};
        border-right: 1px solid {COLORS["border"]};
    }}
    QToolTip {{
        background-color: {COLORS["surface"]};
        color: {COLORS["text_main"]};
        border: 1px solid {COLORS["border_hover"]};
        border-radius: 6px;
        padding: 8px;
        opacity: 240;
        font-size: 13px;
        font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    }}
    QScrollBar:vertical {{
        border: none;
        background: transparent;
        width: 6px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS["border_hover"]};
        min-height: 20px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLORS["text_light"]};
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar::sub-page:vertical,
    QScrollBar::add-page:vertical {{
        background: none;
    }}
    QListWidget {{
        border: none;
        outline: none;
        background: transparent;
    }}
    QListWidget::item {{
        margin: 0px;
        background: transparent;
    }}
    QListWidget::item:hover,
    QListWidget::item:selected {{
        background: transparent;
        outline: none;
    }}
"""

STYLE_SIDEBAR_TITLE = f"""
    color: {COLORS["text_main"]};
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 10px;
"""

STYLE_SIDEBAR_SUBTITLE = f"""
    color: {COLORS["text_light"]};
    font-size: 12px;
    font-weight: 700;
    margin-top: 20px;
    margin-bottom: 5px;
    letter-spacing: 0px;
"""

STYLE_BTN_SIDEBAR_ADD = f"""
    QPushButton {{
        background-color: {COLORS["primary"]};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px;
        font-weight: 700;
        font-size: 14px;
        text-align: center;
    }}
    QPushButton:hover {{
        background-color: {COLORS["primary_hover"]};
    }}
"""

STYLE_BTN_ARCHIVE = f"""
    QPushButton {{
        text-align: left;
        padding: 10px;
        background: transparent;
        border: none;
        border-radius: 6px;
        font-size: 14px;
        color: {COLORS["text_muted"]};
    }}
    QPushButton:hover {{
        background-color: {COLORS["bg_gray"]};
        color: {COLORS["text_main"]};
    }}
"""

STYLE_CARD_CONTAINER = f"""
    TaskCardWidget {{
        background-color: {COLORS["surface"]};
        border-radius: 8px;
        border: 1px solid {COLORS["border"]};
    }}
    TaskCardWidget:hover {{
        border: 1px solid {COLORS["border_hover"]};
    }}
"""

STYLE_CARD_TITLE = f"""
    QLabel {{
        font-weight: 700;
        font-size: 13px;
        color: {COLORS["text_main"]};
        background: transparent;
        border: none;
    }}
"""

STYLE_COMPLETED_TEXT = f"""
    QLabel {{
        font-size: 13px;
        font-weight: 600;
        color: {COLORS["text_light"]};
        text-decoration: line-through;
        border: none;
        background: transparent;
    }}
"""

STYLE_CARD_META = f"""
    QLabel {{
        font-size: 11px;
        color: {COLORS["text_muted"]};
        border: none;
        background: transparent;
    }}
"""

STYLE_CUSTOM_POPUP = f"""
    #popupContainer {{
        background-color: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
    }}
    QLabel {{
        border: none;
        background-color: transparent;
        color: {COLORS["text_main"]};
    }}
"""

STYLE_CHECKBOX = f"""
    QCheckBox {{
        background: transparent;
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border: none;
        background-color: transparent;
        image: url("{CHECKBOX_UNCHECKED_PATH}");
    }}
    QCheckBox::indicator:checked {{
        image: url("{CHECKBOX_CHECKED_PATH}");
    }}
"""

STYLE_DIALOG_CONTAINER = f"""
    QDialog {{
        background-color: {COLORS["surface"]};
    }}
"""

STYLE_FORM_LABEL = f"""
    color: {COLORS["text_muted"]};
    font-weight: 700;
    font-size: 12px;
"""

STYLE_INPUT = f"""
    QLineEdit, QTextEdit, QDateTimeEdit {{
        padding: 10px;
        border: 1px solid {COLORS["border"]};
        border-radius: 6px;
        font-size: 14px;
        color: {COLORS["text_main"]};
        background-color: {COLORS["surface"]};
    }}
    QLineEdit:focus, QTextEdit:focus, QDateTimeEdit:focus {{
        border: 2px solid {COLORS["primary"]};
    }}
"""

STYLE_COMBOBOX = f"""
    QComboBox {{
        padding: 8px;
        border: 1px solid {COLORS["border"]};
        border-radius: 6px;
        color: {COLORS["text_main"]};
        background-color: {COLORS["surface"]};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 22px;
    }}
"""

STYLE_BTN_PRIMARY = f"""
    QPushButton {{
        background-color: {COLORS["primary"]};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 20px;
        font-weight: 700;
        font-size: 14px;
        text-align: center;
    }}
    QPushButton:hover {{
        background-color: {COLORS["primary_hover"]};
    }}
"""

STYLE_BTN_SECONDARY = f"""
    QPushButton {{
        border: none;
        color: {COLORS["text_muted"]};
        font-size: 14px;
        font-weight: 600;
        padding: 8px 16px;
        background: transparent;
        text-align: center;
        border-radius: 4px;
    }}
    QPushButton:hover {{
        color: #374151;
        background-color: {COLORS["bg_gray"]};
    }}
"""

STYLE_ARCHIVE_LIST = f"""
    QListWidget {{
        background: transparent;
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
    }}
"""

STYLE_ARCHIVE_TITLE = f"""
    font-size: 18px;
    font-weight: 700;
    color: {COLORS["text_main"]};
    margin-bottom: 10px;
"""

STYLE_EMPTY_STATE = f"""
    color: {COLORS["text_light"]};
    font-size: 13px;
    padding: 12px;
"""

STYLE_SEPARATOR = f"""
    background-color: {COLORS["border"]};
    margin: 10px 0px;
"""

STYLE_MENU = f"""
    QMenu {{
        background-color: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        padding: 4px 0px;
    }}
    QMenu::item {{
        padding: 6px 20px 6px 16px;
        background-color: transparent;
        color: {COLORS["text_main"]};
        font-size: 13px;
    }}
    QMenu::item:selected {{
        background-color: {COLORS["bg_gray"]};
        color: {COLORS["text_main"]};
        border-radius: 4px;
        margin: 0px 4px;
    }}
"""


def style_quadrant_container(background: str) -> str:
    return f"background-color: {background}; border-radius: 12px;"


def style_quadrant_header(color: str) -> str:
    return f"color: {color}; font-weight: 700; font-size: 14px;"
