import os

from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon, QWidget


class TrayService:
    def __init__(self, window: QWidget) -> None:
        self._window = window
        self._tray: QSystemTrayIcon | None = None

    def initialize(self) -> None:
        if self._tray is not None:
            return

        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets", "icon.ico",
        )
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

        self._tray = QSystemTrayIcon(icon, self._window)
        self._tray.setToolTip("VoluStack - Volume Mixer")

        menu = QMenu()
        show_action = QAction("Show VoluStack", menu)
        show_action.triggered.connect(self.show_window)
        menu.addAction(show_action)
        menu.addSeparator()
        exit_action = QAction("Exit", menu)
        exit_action.triggered.connect(self.exit_app)
        menu.addAction(exit_action)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_activated)
        self._tray.show()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window()

    def show_window(self) -> None:
        self._window.show()
        self._window.activateWindow()
        self._window.raise_()

    def exit_app(self) -> None:
        if self._tray:
            self._tray.hide()
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def dispose(self) -> None:
        if self._tray:
            self._tray.hide()
            self._tray = None
