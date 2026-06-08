import sys

from PyQt6.QtWidgets import QApplication

from app.config import GLOBAL_STYLES
from app.ui.main_window import MainWindow


def main() -> int:
    smoke_test = "--smoke-test" in sys.argv
    argv = [arg for arg in sys.argv if arg != "--smoke-test"]

    app = QApplication(argv)
    app.setStyle("Fusion")
    app.setStyleSheet(GLOBAL_STYLES)

    window = MainWindow()
    if smoke_test:
        window.refresh_all_views()
        window.show()
        app.processEvents()
        window.close()
        app.quit()
        return 0

    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
