import qtawesome as qta
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from volustack.ui.styled_slider import StyledSlider
from volustack.ui.styles import (
    BG_COLOR,
    BTN_ACTIVE,
    BTN_BG,
    BTN_HOVER,
    FONT_FAMILY,
    TEXT_DIM,
    TEXT_PRIMARY,
    UPDATE_DOT_COLOR,
)


class HeaderWidget(QWidget):
    expand_toggled = pyqtSignal()
    close_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    master_volume_changed = pyqtSignal(float)  # 0.0 - 1.0

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("HeaderWidget { background: transparent; }")
        self._expanded = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 8, 8)
        layout.setSpacing(6)

        # Title bar row
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        icon_label = QLabel()
        icon_label.setFixedSize(16, 16)
        icon_label.setStyleSheet("background: transparent;")
        icon_label.setPixmap(qta.icon("fa5s.volume-up", color="#e6e6e6").pixmap(16, 16))
        title_row.addWidget(icon_label)

        title = QLabel("VoluStack")
        title.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.DemiBold))
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
        title_row.addWidget(title)

        title_row.addStretch()

        self._chevron_btn = QPushButton()
        self._chevron_btn.setFixedSize(28, 28)
        self._chevron_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._chevron_btn.setIcon(qta.icon("fa5s.chevron-down", color="#b3b3b3"))
        self._chevron_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BTN_BG};
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {BTN_HOVER};
            }}
        """)
        self._chevron_btn.clicked.connect(self._on_expand)
        title_row.addWidget(self._chevron_btn)

        # Gear / settings button
        self._gear_btn = QPushButton()
        self._gear_btn.setFixedSize(28, 28)
        self._gear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._gear_btn.setIcon(qta.icon("fa5s.cog", color="#b3b3b3"))
        self._gear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BTN_BG};
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {BTN_HOVER};
            }}
        """)
        self._gear_btn.clicked.connect(self.settings_clicked.emit)
        title_row.addWidget(self._gear_btn)

        # Blinking update dot (overlaid on gear button)
        self._update_dot = QLabel(self._gear_btn)
        self._update_dot.setFixedSize(8, 8)
        self._update_dot.move(18, 2)
        self._update_dot.setStyleSheet(
            f"background: {UPDATE_DOT_COLOR}; border-radius: 4px;"
            f" border: 1px solid {BG_COLOR};"
        )
        self._update_dot.hide()

        self._dot_timer = QTimer(self)
        self._dot_timer.setInterval(800)
        self._dot_timer.timeout.connect(self._toggle_dot)
        self._dot_visible = True

        self._close_btn = QPushButton()
        self._close_btn.setFixedSize(28, 28)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.setIcon(qta.icon("fa5s.times", color="#b3b3b3"))
        self._close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BTN_BG};
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: #C42B1C;
            }}
        """)
        self._close_btn.clicked.connect(self.close_clicked.emit)
        title_row.addWidget(self._close_btn)

        layout.addLayout(title_row)

        # Master volume row
        master_row = QHBoxLayout()
        master_row.setSpacing(8)

        master_label = QLabel("Master")
        master_label.setFont(QFont(FONT_FAMILY, 8))
        master_label.setStyleSheet(f"color: {TEXT_DIM}; background: transparent;")
        master_row.addWidget(master_label)

        self._master_slider = StyledSlider(Qt.Orientation.Horizontal)
        self._master_slider.setRange(0, 100)
        self._master_slider.setValue(100)
        master_row.addWidget(self._master_slider, 1)

        self._master_pct = QLabel("100%")
        self._master_pct.setFixedWidth(36)
        self._master_pct.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._master_pct.setFont(QFont(FONT_FAMILY, 8))
        self._master_pct.setStyleSheet(f"color: {TEXT_DIM}; background: transparent;")
        master_row.addWidget(self._master_pct)

        self._master_slider.valueChanged.connect(self._on_master_changed)

        layout.addLayout(master_row)

    def _on_master_changed(self, value: int) -> None:
        self._master_pct.setText(f"{value}%")
        self.master_volume_changed.emit(value / 100.0)

    def set_master_volume(self, volume: float) -> None:
        self._master_slider.blockSignals(True)
        self._master_slider.setValue(round(volume * 100))
        self._master_slider.blockSignals(False)
        self._master_pct.setText(f"{round(volume * 100)}%")

    def _on_expand(self) -> None:
        self._expanded = not self._expanded
        icon_name = "fa5s.chevron-up" if self._expanded else "fa5s.chevron-down"
        self._chevron_btn.setIcon(qta.icon(icon_name, color="#b3b3b3"))
        self.expand_toggled.emit()

    @property
    def expanded(self) -> bool:
        return self._expanded

    # -- Update dot --

    def show_update_dot(self) -> None:
        self._update_dot.show()
        self._dot_visible = True
        self._dot_timer.start()

    def hide_update_dot(self) -> None:
        self._dot_timer.stop()
        self._update_dot.hide()

    def _toggle_dot(self) -> None:
        self._dot_visible = not self._dot_visible
        self._update_dot.setVisible(self._dot_visible)

    # -- Gear active state --

    def set_settings_active(self, active: bool) -> None:
        bg = BTN_ACTIVE if active else BTN_BG
        self._gear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {BTN_HOVER};
            }}
        """)
