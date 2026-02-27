from PyQt6.QtCore import QThread, pyqtSignal

from volustack.updater.checker import UpdateChecker
from volustack.updater.info import UpdateInfo


class UpdateCheckWorker(QThread):
    update_found = pyqtSignal(UpdateInfo)
    check_finished = pyqtSignal()

    def __init__(self, current_version: str, parent=None) -> None:
        super().__init__(parent)
        self._current_version = current_version

    def run(self) -> None:
        checker = UpdateChecker(self._current_version)
        result = checker.check_for_updates()
        if result is not None:
            self.update_found.emit(result)
        self.check_finished.emit()
