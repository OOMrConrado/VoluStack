import qtawesome as qta
from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetrics, QIcon, QPixmap
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from volustack.audio.session import AudioSessionInfo
from volustack.ui.styled_slider import StyledSlider
from volustack.ui.styles import FONT_FAMILY, ICON_BG, TEXT_DIM, TEXT_FAINT, TEXT_SECONDARY

# Pre-cached mute icons (class-level, created once)
_ICON_UNMUTED: QIcon | None = None
_ICON_MUTED: QIcon | None = None


def _get_mute_icons() -> tuple[QIcon, QIcon]:
    global _ICON_UNMUTED, _ICON_MUTED
    if _ICON_UNMUTED is None:
        _ICON_UNMUTED = qta.icon("fa5s.volume-up", color="#999999")
        _ICON_MUTED = qta.icon("fa5s.volume-mute", color="#4d4d4d")
    return _ICON_UNMUTED, _ICON_MUTED


class SessionRowWidget(QWidget):
    volume_changed = pyqtSignal(str, float)
    mute_toggled = pyqtSignal(str, bool)  # session_id, new_muted_state

    def __init__(self, session: AudioSessionInfo, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("SessionRowWidget { background: transparent; }")
        self.session_id = session.session_identifier
        self.setFixedHeight(48)
        self._is_muted = session.is_muted
        self._setup_ui(session)

    def _setup_ui(self, session: AudioSessionInfo) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        self._icon_label = QLabel()
        self._icon_label.setFixedSize(24, 24)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if session.icon and not session.icon.isNull():
            self._icon_label.setStyleSheet("background: transparent;")
            self._icon_label.setPixmap(session.icon)
        else:
            self._icon_label.setStyleSheet(
                f"background: {ICON_BG}; border-radius: 4px;"
            )
            self._icon_label.setPixmap(
                qta.icon("fa5s.volume-up", color="rgba(255,255,255,0.5)").pixmap(14, 14)
            )
        layout.addWidget(self._icon_label)

        self._name_label = QLabel()
        self._name_label.setFixedWidth(70)
        self._name_label.setFont(QFont(FONT_FAMILY, 8))
        self._name_label.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self._set_name_text(session.process_name, session.display_suffix)
        layout.addWidget(self._name_label)

        self._mute_btn = QPushButton()
        self._mute_btn.setFixedSize(32, 32)
        self._mute_btn.setIconSize(QSize(18, 18))
        self._mute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mute_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; padding: 0px; }"
            "QPushButton:hover { background: rgba(255,255,255,0.08); border-radius: 4px; }"
        )
        self._mute_btn.clicked.connect(self._on_mute_clicked)
        self._update_mute_icon(session.is_muted)
        layout.addWidget(self._mute_btn)

        self._slider = StyledSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 100)
        self._slider.setValue(round(session.volume * 100))
        self._slider.setEnabled(not session.is_muted)
        self._slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self._slider, 1)

        self._pct_label = QLabel(f"{round(session.volume * 100)}%")
        self._pct_label.setFixedWidth(32)
        self._pct_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._pct_label.setFont(QFont(FONT_FAMILY, 8))
        self._pct_label.setStyleSheet(f"color: {TEXT_DIM}; background: transparent;")
        layout.addWidget(self._pct_label)

    def _set_name_text(self, name: str, suffix: str) -> None:
        metrics = QFontMetrics(self._name_label.font())
        max_w = self._name_label.width() or 70

        if suffix:
            suffix_part = f" ({suffix})"
            available = max_w - metrics.horizontalAdvance(suffix_part)
            elided = metrics.elidedText(name, Qt.TextElideMode.ElideRight, max(available, 20))
            self._name_label.setText(
                f'{elided} <span style="color:{TEXT_FAINT}; font-size:7pt">({suffix})</span>'
            )
            self._name_label.setTextFormat(Qt.TextFormat.RichText)
        else:
            elided = metrics.elidedText(name, Qt.TextElideMode.ElideRight, max_w)
            self._name_label.setText(elided)
            self._name_label.setTextFormat(Qt.TextFormat.PlainText)

    def _on_slider_changed(self, value: int) -> None:
        self._pct_label.setText(f"{value}%")
        self.volume_changed.emit(self.session_id, value / 100.0)

    def _on_mute_clicked(self) -> None:
        self._is_muted = not self._is_muted
        self._update_mute_icon(self._is_muted)
        self._slider.setEnabled(not self._is_muted)
        self.mute_toggled.emit(self.session_id, self._is_muted)

    def _update_mute_icon(self, muted: bool) -> None:
        unmuted_icon, muted_icon = _get_mute_icons()
        self._mute_btn.setIcon(muted_icon if muted else unmuted_icon)

    def update_session(self, session: AudioSessionInfo) -> None:
        self._set_name_text(session.process_name, session.display_suffix)

        if not self._slider.isSliderDown():
            self._slider.blockSignals(True)
            self._slider.setValue(round(session.volume * 100))
            self._slider.blockSignals(False)
            self._pct_label.setText(f"{round(session.volume * 100)}%")

        if session.is_muted != self._is_muted:
            self._is_muted = session.is_muted
            self._update_mute_icon(session.is_muted)
            self._slider.setEnabled(not session.is_muted)
