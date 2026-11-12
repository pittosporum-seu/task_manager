import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

from app.config import GLOBAL_STYLES
from app.ui.main_window import MainWindow


def main() -> int:
    smoke_test = "--smoke-test" in sys.argv
    argv = [arg for arg in sys.argv if arg != "--smoke-test"]

    app = QApplication(argv)
    app.setStyle("Fusion")
    app.setStyleSheet(GLOBAL_STYLES)
    app.setQuitOnLastWindowClosed(False)

    server = QLocalServer(app)
    if not smoke_test:
        socket = QLocalSocket()
        socket.connectToServer("MyTask-desktop")
        if socket.waitForConnected(1000):
            socket.disconnectFromServer()
            return 0
        if not server.listen("MyTask-desktop"):
            return 1

    window = MainWindow()

    def activate_existing():
        connection = server.nextPendingConnection()
        if connection:
            connection.deleteLater()
        window.restore_window()

    server.newConnection.connect(activate_existing)
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
