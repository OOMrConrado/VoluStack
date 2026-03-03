import keyboard
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from volustack.ui.styles import (
    ACCENT_COLOR,
    BORDER_COLOR,
    BTN_BG,
    BTN_HOVER,
    FONT_FAMILY,
    HOTKEY_RECORDER_ACTIVE_BORDER,
    HOTKEY_RECORDER_BG,
    HOTKEY_RECORDER_BORDER,
    TEXT_DIM,
    TEXT_PRIMARY,
)

_RECORDER_NORMAL_STYLE = f"""
    QLabel {{
        color: {TEXT_PRIMARY};
        background: {HOTKEY_RECORDER_BG};
        border: 1px solid {HOTKEY_RECORDER_BORDER};
        border-radius: 4px;
        padding: 0 12px;
    }}
"""

_RECORDER_ACTIVE_STYLE = f"""
    QLabel {{
        color: {ACCENT_COLOR};
        background: {HOTKEY_RECORDER_BG};
        border: 1px solid {HOTKEY_RECORDER_ACTIVE_BORDER};
        border-radius: 4px;
        padding: 0 12px;
    }}
"""

_SMALL_BTN_STYLE = f"""
    QPushButton {{
        background: {BTN_BG};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_COLOR};
        border-radius: 4px;
        padding: 0 10px;
    }}
    QPushButton:hover {{
        background: {BTN_HOVER};
    }}
    QPushButton:disabled {{
        color: {TEXT_DIM};
    }}
"""

# All names the keyboard library may report for modifier keys (EN + ES layouts)
_MODIFIER_SCANCODES = {
    "ctrl", "shift", "alt",
    "left ctrl", "right ctrl",
    "left shift", "right shift",
    "left alt", "right alt",
    "left windows", "right windows",
    # Spanish layout names
    "control", "left control", "right control",
    "mayus", "mayúsculas",
    "alt gr",
}

# Map every variant to a canonical short name
_MODIFIER_NORMALIZE = {
    "left ctrl": "ctrl", "right ctrl": "ctrl",
    "control": "ctrl", "left control": "ctrl", "right control": "ctrl",
    "left shift": "shift", "right shift": "shift",
    "mayus": "shift", "mayúsculas": "shift",
    "left alt": "alt", "right alt": "alt", "alt gr": "alt",
    "left windows": "win", "right windows": "win",
}

# Display order (max 2 modifiers + 1 key = 3 keys total)
_MODIFIER_ORDER = ["ctrl", "shift", "alt", "win"]

# Keys that should cancel recording
_CANCEL_KEYS = {"esc", "escape"}


class HotkeyRecorderWidget(QWidget):
    hotkey_changed = pyqtSignal(str, str)  # (modifiers, key)
    recording_started = pyqtSignal()       # tells window to unregister global hotkey
    recording_stopped = pyqtSignal()       # tells window to re-register global hotkey

    # Internal signals to marshal keyboard-thread callbacks to Qt main thread
    _sig_stop = pyqtSignal()
    _sig_partial = pyqtSignal(str)
    _sig_finish = pyqtSignal(str, str)

    def __init__(self, current_combo: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._recording = False
        self._current_combo = current_combo
        self._hook_handle = None
        self._pressed_mods: set[str] = set()
        self._pending_key: str | None = None  # non-modifier key held down
        self._pending_combo_mods: str | None = None
        self._sig_stop.connect(self._stop_recording)
        self._sig_partial.connect(self._update_display)
        self._sig_finish.connect(self._finish_recording)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._display = QLabel(self._current_combo.upper())
        self._display.setFont(QFont(FONT_FAMILY, 9))
        self._display.setFixedHeight(32)
        self._display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._display.setStyleSheet(_RECORDER_NORMAL_STYLE)
        layout.addWidget(self._display, 1)

        self._record_btn = QPushButton("Change")
        self._record_btn.setFixedSize(64, 32)
        self._record_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._record_btn.setFont(QFont(FONT_FAMILY, 8))
        self._record_btn.setStyleSheet(_SMALL_BTN_STYLE)
        self._record_btn.clicked.connect(self._toggle_recording)
        layout.addWidget(self._record_btn)

    def _toggle_recording(self) -> None:
        if self._recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self) -> None:
        self._recording = True
        self._pressed_mods.clear()
        self._pending_key = None
        self._record_btn.setText("Cancel")
        self._display.setText("Press keys...")
        self._display.setStyleSheet(_RECORDER_ACTIVE_STYLE)
        self.recording_started.emit()
        self._hook_handle = keyboard.hook(self._on_key_event, suppress=False)

    def _stop_recording(self) -> None:
        self._unhook()
        self._recording = False
        self._record_btn.setText("Change")
        self._display.setText(self._current_combo.upper())
        self._display.setStyleSheet(_RECORDER_NORMAL_STYLE)
        self.recording_stopped.emit()

    def _unhook(self) -> None:
        if self._hook_handle is not None:
            try:
                keyboard.unhook(self._hook_handle)
            except (KeyError, ValueError):
                pass
            self._hook_handle = None

    def _on_key_event(self, event: keyboard.KeyboardEvent) -> None:
        if not self._recording:
            return

        name = (event.name or "").lower()
        normalized = _MODIFIER_NORMALIZE.get(name, name)

        if event.event_type == keyboard.KEY_UP:
            if name in _MODIFIER_SCANCODES:
                self._pressed_mods.discard(normalized)
            # Confirm combo when all keys released and we have a valid pending combo
            if self._pending_key and not self._pressed_mods:
                mod_str = self._pending_combo_mods or ""
                key = self._pending_key
                self._pending_key = None
                self._pending_combo_mods = None
                if mod_str:
                    self._current_combo = f"{mod_str}+{key}"
                    self._sig_finish.emit(mod_str, key)
            return

        # KEY_DOWN
        if name in _CANCEL_KEYS:
            self._sig_stop.emit()
            return

        # Modifier key pressed — track it (max 2 to keep combo <= 3 keys)
        if name in _MODIFIER_SCANCODES:
            if len(self._pressed_mods) < 2 or normalized in self._pressed_mods:
                self._pressed_mods.add(normalized)
            self._pending_key = None
            partial = "+".join(m for m in _MODIFIER_ORDER if m in self._pressed_mods)
            if partial:
                self._sig_partial.emit(partial)
            return

        # Non-modifier key — need at least one modifier held
        if not self._pressed_mods:
            return

        mod_parts = [m for m in _MODIFIER_ORDER if m in self._pressed_mods]
        if not mod_parts:
            return

        # Store pending combo, show preview, release to confirm
        self._pending_key = name
        self._pending_combo_mods = "+".join(mod_parts)
        self._sig_partial.emit(f"{self._pending_combo_mods}+{name}")

    def _update_display(self, text: str) -> None:
        # If it contains a non-modifier key, show full combo; otherwise show "MOD+..."
        if self._pending_key:
            self._display.setText(text.upper())
        else:
            self._display.setText(f"{text.upper()}+...")

    def _finish_recording(self, modifiers: str, key: str) -> None:
        self._unhook()
        self._recording = False
        self._record_btn.setText("Change")
        self._display.setText(self._current_combo.upper())
        self._display.setStyleSheet(_RECORDER_NORMAL_STYLE)
        self.hotkey_changed.emit(modifiers, key)

    def update_combo(self, combo: str) -> None:
        self._current_combo = combo
        if not self._recording:
            self._display.setText(combo.upper())


_CHECKBOX_STYLE = f"""
    QCheckBox {{
        color: {TEXT_PRIMARY};
        background: transparent;
        spacing: 6px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {BORDER_COLOR};
        border-radius: 3px;
        background: {HOTKEY_RECORDER_BG};
    }}
    QCheckBox::indicator:checked {{
        background: {ACCENT_COLOR};
        border-color: {ACCENT_COLOR};
    }}
    QCheckBox::indicator:hover {{
        border-color: {ACCENT_COLOR};
    }}
"""


class SettingsPanelWidget(QWidget):
    hotkey_changed = pyqtSignal(str, str)  # (modifiers, key)
    check_updates_clicked = pyqtSignal()
    download_clicked = pyqtSignal(str)  # download_url
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()

    PANEL_HEIGHT = 185

    def __init__(self, current_hotkey: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("SettingsPanelWidget { background: transparent; }")
        self._setup_ui(current_hotkey)

    def _setup_ui(self, current_hotkey: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(10)

        # --- Hotkey section ---
        hotkey_label = QLabel("Toggle Hotkey")
        hotkey_label.setFont(QFont(FONT_FAMILY, 8, QFont.Weight.DemiBold))
        hotkey_label.setStyleSheet(f"color: {TEXT_DIM}; background: transparent;")
        layout.addWidget(hotkey_label)

        self._hotkey_recorder = HotkeyRecorderWidget(current_hotkey)
        self._hotkey_recorder.hotkey_changed.connect(self.hotkey_changed.emit)
        self._hotkey_recorder.recording_started.connect(self.recording_started.emit)
        self._hotkey_recorder.recording_stopped.connect(self.recording_stopped.emit)
        layout.addWidget(self._hotkey_recorder)

        # --- Separator 1 ---
        sep1 = QWidget()
        sep1.setFixedHeight(1)
        sep1.setStyleSheet(f"background: {BORDER_COLOR};")
        layout.addWidget(sep1)

        # --- Startup section ---
        from volustack.settings.startup import is_startup_enabled, set_startup_enabled

        self._startup_cb = QCheckBox("Start with Windows")
        self._startup_cb.setFont(QFont(FONT_FAMILY, 8))
        self._startup_cb.setStyleSheet(_CHECKBOX_STYLE)
        self._startup_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        self._startup_cb.setChecked(is_startup_enabled())
        self._startup_cb.toggled.connect(lambda on: set_startup_enabled(on))
        layout.addWidget(self._startup_cb)

        # --- Separator 2 ---
        sep2 = QWidget()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background: {BORDER_COLOR};")
        layout.addWidget(sep2)

        # --- Update section ---
        update_label = QLabel("Updates")
        update_label.setFont(QFont(FONT_FAMILY, 8, QFont.Weight.DemiBold))
        update_label.setStyleSheet(f"color: {TEXT_DIM}; background: transparent;")
        layout.addWidget(update_label)

        update_row = QHBoxLayout()
        update_row.setSpacing(8)

        self._update_status = QLabel("")
        self._update_status.setFont(QFont(FONT_FAMILY, 8))
        self._update_status.setStyleSheet(f"color: {TEXT_DIM}; background: transparent;")
        update_row.addWidget(self._update_status, 1)

        self._check_btn = QPushButton("Check for Updates")
        self._check_btn.setFixedHeight(28)
        self._check_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._check_btn.setFont(QFont(FONT_FAMILY, 8))
        self._check_btn.setStyleSheet(_SMALL_BTN_STYLE)
        self._check_btn.clicked.connect(self.check_updates_clicked.emit)
        update_row.addWidget(self._check_btn)

        self._download_btn = QPushButton("Download")
        self._download_btn.setFixedHeight(28)
        self._download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._download_btn.setFont(QFont(FONT_FAMILY, 8))
        self._download_btn.setStyleSheet(
            f"QPushButton {{ background: {ACCENT_COLOR}; color: #000; "
            f"border: none; border-radius: 4px; padding: 0 10px; "
            f"font-weight: bold; }}"
            f"QPushButton:hover {{ background: #7DD8FF; }}"
        )
        self._download_btn.clicked.connect(self._open_download)
        self._download_btn.hide()
        self._download_url: str | None = None
        update_row.addWidget(self._download_btn)

        layout.addLayout(update_row)

    def _open_download(self) -> None:
        if self._download_url:
            self._download_btn.setEnabled(False)
            self._download_btn.setText("0%")
            self.download_clicked.emit(self._download_url)

    def set_download_progress(self, pct: int) -> None:
        self._download_btn.setText(f"{pct}%")

    def set_download_failed(self) -> None:
        self._download_btn.setEnabled(True)
        self._download_btn.setText("Retry")

    def set_update_status(self, text: str, download_url: str | None = None) -> None:
        self._update_status.setText(text)
        self._download_url = download_url
        if download_url:
            self._check_btn.hide()
            self._download_btn.show()
        else:
            self._download_btn.hide()
            self._check_btn.show()

    def set_checking(self, checking: bool) -> None:
        self._check_btn.setEnabled(not checking)
        self._check_btn.setText("Checking..." if checking else "Check for Updates")

    def update_hotkey_display(self, combo: str) -> None:
        self._hotkey_recorder.update_combo(combo)
