import os

from PyQt6.QtCore import QFileInfo
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFileIconProvider


class IconCache:
    def __init__(self) -> None:
        self._cache: dict[str, QPixmap | None] = {}
        self._provider = QFileIconProvider()

    def get_icon(self, executable_path: str) -> QPixmap | None:
        if not executable_path:
            return None

        if executable_path in self._cache:
            return self._cache[executable_path]

        pixmap = self._extract_icon(executable_path)
        self._cache[executable_path] = pixmap
        return pixmap

    def _extract_icon(self, exe_path: str) -> QPixmap | None:
        if not os.path.exists(exe_path):
            return None
        try:
            icon = self._provider.icon(QFileInfo(exe_path))
            if not icon.isNull():
                return icon.pixmap(24, 24)
        except Exception:
            pass
        return None

    def clear(self) -> None:
        self._cache.clear()
