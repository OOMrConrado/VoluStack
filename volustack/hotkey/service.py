from typing import Callable

import keyboard
from PyQt6.QtCore import QObject, pyqtSignal


class HotkeyService(QObject):
    """Global hotkey manager that marshals callbacks to the Qt main thread.

    The ``keyboard`` library fires callbacks from a background hook thread.
    Qt GUI operations must run on the main thread, so we use a signal
    (auto-queued across threads) to bridge the gap.
    """

    _triggered = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._registered_combo: str | None = None
        self._callback: Callable[[], None] | None = None
        self._triggered.connect(self._on_triggered)

    def register(self, on_pressed: Callable[[], None], combo: str = "ctrl+shift+v") -> None:
        self.unregister()
        self._registered_combo = combo
        self._callback = on_pressed
        keyboard.add_hotkey(combo, self._triggered.emit, suppress=False)

    def _on_triggered(self) -> None:
        if self._callback:
            self._callback()

    def unregister(self) -> None:
        if self._registered_combo is not None:
            try:
                keyboard.remove_hotkey(self._registered_combo)
            except (KeyError, ValueError):
                pass
            self._registered_combo = None

    def dispose(self) -> None:
        self.unregister()
