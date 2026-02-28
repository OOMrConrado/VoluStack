import sys
import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from volustack.ui.window import VoluStackWindow


def main() -> None:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    minimized = "--minimized" in sys.argv
    window = VoluStackWindow(minimized=minimized)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
