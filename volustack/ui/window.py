import ctypes
import gc

from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

# ── Win32 API for game overlay support ──────────────────────────────
_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32
_HWND_TOPMOST = -1
_SWP_NOMOVE = 0x0002
_SWP_NOSIZE = 0x0001
_SWP_NOACTIVATE = 0x0010

from volustack.audio.manager import AudioManager
from volustack.audio.session import AppAudioState, AudioSessionInfo
from volustack.hotkey.service import HotkeyService
from volustack.settings.service import SettingsService
from volustack.tray.service import TrayService
from volustack.ui.header_widget import HeaderWidget
from volustack.ui.session_row_widget import SessionRowWidget
from volustack.ui.settings_panel_widget import SettingsPanelWidget
from volustack.ui.styles import BORDER_COLOR, FONT_FAMILY, TEXT_MUTED
from volustack.updater.info import UpdateInfo
from volustack.updater.worker import UpdateCheckWorker
from volustack.version import __version__


class VoluStackWindow(QWidget):
    HEADER_HEIGHT = 88
    SESSION_ROW_HEIGHT = 48
    MAX_VISIBLE_SESSIONS = 6
    SETTINGS_PANEL_HEIGHT = 185
    WINDOW_WIDTH = 360

    def __init__(self, minimized: bool = False) -> None:
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setFixedWidth(self.WINDOW_WIDTH)
        self.setFixedHeight(self.HEADER_HEIGHT)

        # Position top-left with a small margin
        self.move(12, 12)

        self._drag_pos: QPoint | None = None
        self._prev_foreground: int | None = None
        self._expanded = False
        self._settings_visible = False
        self._session_widgets: dict[str, SessionRowWidget] = {}
        self._active_sessions: list[AudioSessionInfo] = []
        self._audio_manager = AudioManager()
        self._minimized_start = minimized
        self._pending_update: UpdateInfo | None = None
        self._update_worker: UpdateCheckWorker | None = None
        self._manual_update_worker: UpdateCheckWorker | None = None

        self._settings = SettingsService()
        self._tray = TrayService(self)
        self._hotkey = HotkeyService()

        self._setup_ui()
        self._setup_services()
        self._setup_polling()

    def _setup_ui(self) -> None:
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(1, 1, 1, 1)
        self._layout.setSpacing(0)

        self._header = HeaderWidget()
        self._header.expand_toggled.connect(self._toggle_expand)
        self._header.close_clicked.connect(self._on_close)
        self._header.settings_clicked.connect(self._toggle_settings)
        self._header.master_volume_changed.connect(self._on_master_volume_changed)
        self._layout.addWidget(self._header)

        # Sync master volume slider with system
        self._header.set_master_volume(self._audio_manager.get_master_volume())

        self._separator = QWidget()
        self._separator.setFixedHeight(1)
        self._separator.setStyleSheet(f"background: {BORDER_COLOR};")
        self._separator.hide()
        self._layout.addWidget(self._separator)

        self._sessions_inner = QWidget()
        self._sessions_layout = QVBoxLayout(self._sessions_inner)
        self._sessions_layout.setContentsMargins(0, 0, 0, 0)
        self._sessions_layout.setSpacing(0)

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setWidget(self._sessions_inner)
        self._scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._scroll_area.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollBar:vertical { background: transparent; width: 6px; margin: 2px 0; }"
            "QScrollBar::handle:vertical { background: rgba(255,255,255,0.15); border-radius: 3px; min-height: 20px; }"
            "QScrollBar::handle:vertical:hover { background: rgba(255,255,255,0.25); }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
            "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }"
        )
        self._scroll_area.hide()
        self._layout.addWidget(self._scroll_area)

        self._settings_panel = SettingsPanelWidget(self._settings.hotkey_combo)
        self._settings_panel.hotkey_changed.connect(self._on_hotkey_changed)
        self._settings_panel.check_updates_clicked.connect(self._on_check_updates)
        self._settings_panel.recording_started.connect(self._hotkey.unregister)
        self._settings_panel.recording_stopped.connect(
            lambda: self._hotkey.register(self._toggle_visibility, self._settings.hotkey_combo)
        )
        self._settings_panel.hide()
        self._layout.addWidget(self._settings_panel)

        self._empty_label = QLabel("No apps playing audio")
        self._empty_label.setFont(QFont(FONT_FAMILY, 9))
        self._empty_label.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setContentsMargins(12, 12, 12, 12)
        self._empty_label.hide()

    def _setup_services(self) -> None:
        self._tray.initialize()
        combo = self._settings.hotkey_combo
        self._hotkey.register(self._toggle_visibility, combo)

        # Passive update check on startup
        if self._settings.auto_check_updates:
            self._start_passive_update_check()

    def _setup_polling(self) -> None:
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_sessions)

        self._volume_timer = QTimer(self)
        self._volume_timer.timeout.connect(self._sync_volumes)

        self._topmost_timer = QTimer(self)
        self._topmost_timer.timeout.connect(self._enforce_topmost)

        if not self._minimized_start:
            QTimer.singleShot(1000, self._start_polling)

    def _start_polling(self) -> None:
        self._poll_sessions()
        self._poll_timer.start(3000)
        self._volume_timer.start(500)
        self._topmost_timer.start(1000)

    def _poll_sessions(self) -> None:
        sessions = self._audio_manager.enumerate_sessions()
        # Show active AND inactive sessions (for apps like Discord in voice chat)
        self._active_sessions = [
            s for s in sessions if s.state != AppAudioState.EXPIRED
        ]
        self._update_session_list()

        # Sync master volume slider if user changed it from Windows
        if not self._header._master_slider.isSliderDown():
            self._header.set_master_volume(self._audio_manager.get_master_volume())

    def _sync_volumes(self) -> None:
        """Fast volume sync from cached COM controls (no session re-enumeration)."""
        # Master volume
        if not self._header._master_slider.isSliderDown():
            self._header.set_master_volume(self._audio_manager.get_master_volume())

        # Per-session volumes
        volumes = self._audio_manager.get_session_volumes()
        for sid, widget in self._session_widgets.items():
            if sid in volumes:
                vol, muted = volumes[sid]
                if not widget._slider.isSliderDown():
                    widget._slider.blockSignals(True)
                    widget._slider.setValue(round(vol * 100))
                    widget._slider.blockSignals(False)
                    widget._pct_label.setText(f"{round(vol * 100)}%")
                if muted != widget._is_muted:
                    widget._is_muted = muted
                    widget._update_mute_icon(muted)
                    widget._slider.setEnabled(not muted)

    def _update_session_list(self) -> None:
        current_ids = {s.session_identifier for s in self._active_sessions}
        existing_ids = set(self._session_widgets.keys())

        for sid in existing_ids - current_ids:
            widget = self._session_widgets.pop(sid)
            self._sessions_layout.removeWidget(widget)
            widget.deleteLater()

        for session in self._active_sessions:
            sid = session.session_identifier
            if sid in self._session_widgets:
                self._session_widgets[sid].update_session(session)
            else:
                row = SessionRowWidget(session)
                row.volume_changed.connect(self._on_volume_changed)
                row.mute_toggled.connect(self._on_mute_toggled)
                self._session_widgets[sid] = row
                self._sessions_layout.addWidget(row)

        self._update_window_size()

    def _on_master_volume_changed(self, volume: float) -> None:
        self._audio_manager.set_master_volume(volume)

    def _on_volume_changed(self, session_id: str, volume: float) -> None:
        self._audio_manager.set_session_volume(session_id, volume)

    def _on_mute_toggled(self, session_id: str, is_muted: bool) -> None:
        self._audio_manager.set_session_mute(session_id, is_muted)

    # -- Settings panel --

    def _toggle_settings(self) -> None:
        self._settings_visible = not self._settings_visible

        if self._settings_visible:
            self._separator.show()
            self._scroll_area.hide()
            self._empty_label.hide()
            self._settings_panel.show()
            self._header.set_settings_active(True)
            if self._pending_update:
                self._settings_panel.set_update_status(
                    f"v{self._pending_update.version} available"
                )
                self._header.hide_update_dot()
        else:
            self._settings_panel.hide()
            self._header.set_settings_active(False)
            if self._expanded:
                self._scroll_area.show()
            else:
                self._separator.hide()

        self._update_window_size()

    def _on_hotkey_changed(self, modifiers: str, key: str) -> None:
        self._hotkey.unregister()
        self._settings.hotkey_modifiers = modifiers
        self._settings.hotkey_key = key
        combo = self._settings.hotkey_combo
        self._hotkey.register(self._toggle_visibility, combo)
        self._settings_panel.update_hotkey_display(combo)

    # -- Update checking --

    def _start_passive_update_check(self) -> None:
        self._update_worker = UpdateCheckWorker(__version__, parent=self)
        self._update_worker.update_found.connect(self._on_update_found)
        self._update_worker.check_finished.connect(self._on_passive_check_finished)
        self._update_worker.start()

    def _on_update_found(self, info: UpdateInfo) -> None:
        self._pending_update = info
        self._header.show_update_dot()

    def _on_passive_check_finished(self) -> None:
        if self._update_worker:
            self._update_worker.deleteLater()
            self._update_worker = None

    def _on_check_updates(self) -> None:
        self._settings_panel.set_checking(True)
        worker = UpdateCheckWorker(__version__, parent=self)
        worker.update_found.connect(self._on_manual_update_found)
        worker.check_finished.connect(self._on_manual_check_finished)
        worker.start()
        self._manual_update_worker = worker

    def _on_manual_update_found(self, info: UpdateInfo) -> None:
        self._pending_update = info
        self._settings_panel.set_update_status(f"v{info.version} available!")
        self._header.hide_update_dot()

    def _on_manual_check_finished(self) -> None:
        self._settings_panel.set_checking(False)
        if not self._pending_update:
            self._settings_panel.set_update_status("You're up to date")
        if self._manual_update_worker:
            self._manual_update_worker.deleteLater()
            self._manual_update_worker = None

    # -- Expand / sizing --

    def _toggle_expand(self) -> None:
        if self._settings_visible:
            self._settings_visible = False
            self._settings_panel.hide()
            self._header.set_settings_active(False)
        self._expanded = self._header.expanded
        self._update_window_size()

    def _update_window_size(self) -> None:
        if self._settings_visible:
            height = self.HEADER_HEIGHT + self.SETTINGS_PANEL_HEIGHT
            self.setFixedHeight(int(height))
            return

        count = len(self._active_sessions)

        if self._expanded and count > 0:
            self._separator.show()
            self._scroll_area.show()
            self._empty_label.hide()
            if self._empty_label.parent() == self._sessions_inner:
                self._sessions_layout.removeWidget(self._empty_label)
            visible = min(count, self.MAX_VISIBLE_SESSIONS)
            height = self.HEADER_HEIGHT + (visible * self.SESSION_ROW_HEIGHT) + 8
        elif self._expanded:
            self._separator.show()
            self._scroll_area.show()
            if self._empty_label.parent() != self._sessions_inner:
                self._sessions_layout.addWidget(self._empty_label)
            self._empty_label.show()
            height = self.HEADER_HEIGHT + 40
        else:
            self._separator.hide()
            self._scroll_area.hide()
            self._empty_label.hide()
            height = self.HEADER_HEIGHT

        self.setFixedHeight(int(height))

    # -- Visibility & lifecycle --

    def _toggle_visibility(self) -> None:
        if self.isVisible():
            prev = self._prev_foreground
            self._prev_foreground = None
            self.hide()
            # Restore focus to the previous window (the game)
            if prev:
                _user32.BringWindowToTop(prev)
                _user32.SetForegroundWindow(prev)
        else:
            # Save the current foreground window so we can restore it on hide
            self._prev_foreground = _user32.GetForegroundWindow()
            self.show()
            self._enforce_topmost()
            self._bring_to_foreground()

    def _on_close(self) -> None:
        if self._settings.minimize_to_tray:
            self.hide()
        else:
            self._cleanup_and_quit()

    # -- Win32 game overlay helpers --

    def _enforce_topmost(self) -> None:
        """Re-assert HWND_TOPMOST via Win32 so overlay stays above games."""
        hwnd = int(self.winId())
        _user32.SetWindowPos(
            hwnd, _HWND_TOPMOST, 0, 0, 0, 0,
            _SWP_NOMOVE | _SWP_NOSIZE | _SWP_NOACTIVATE,
        )

    def _bring_to_foreground(self) -> None:
        """Force overlay to foreground, stealing focus from games."""
        hwnd = int(self.winId())
        fg = _user32.GetForegroundWindow()
        fg_thread = _user32.GetWindowThreadProcessId(fg, None)
        our_thread = _kernel32.GetCurrentThreadId()

        attached = False
        if fg_thread and fg_thread != our_thread:
            attached = bool(_user32.AttachThreadInput(fg_thread, our_thread, True))

        _user32.ShowWindow(hwnd, 5)  # SW_SHOW
        _user32.BringWindowToTop(hwnd)
        _user32.SetForegroundWindow(hwnd)

        if attached:
            _user32.AttachThreadInput(fg_thread, our_thread, False)

        self.activateWindow()
        self.raise_()

    def _sleep(self) -> None:
        """Enter sleep mode: stop polling, destroy widgets, free caches."""
        self._poll_timer.stop()
        self._volume_timer.stop()
        self._topmost_timer.stop()

        for widget in self._session_widgets.values():
            self._sessions_layout.removeWidget(widget)
            widget.deleteLater()
        self._session_widgets.clear()
        self._active_sessions.clear()

        self._audio_manager.sleep()
        gc.collect()

    def _wake(self) -> None:
        """Exit sleep mode: poll immediately and restart timers."""
        self._poll_sessions()
        self._poll_timer.start(3000)
        self._volume_timer.start(500)
        self._topmost_timer.start(1000)

    def _cleanup_and_quit(self) -> None:
        self._poll_timer.stop()
        self._volume_timer.stop()
        self._topmost_timer.stop()
        self._hotkey.dispose()
        self._tray.dispose()
        for worker in (self._update_worker, self._manual_update_worker):
            if worker and worker.isRunning():
                worker.quit()
                worker.wait(1000)
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def show(self) -> None:
        if self._minimized_start:
            self._minimized_start = False
            self._sleep()
            return
        super().show()
        self._wake()

    def hide(self) -> None:
        super().hide()
        self._sleep()

    # -- Window chrome --

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Clip to rounded rect so nothing leaks outside
        path = QPainterPath()
        path.addRoundedRect(0.5, 0.5, self.width() - 1.0, self.height() - 1.0, 8.0, 8.0)
        painter.setClipPath(path)

        # Solid opaque background (no transparency)
        painter.fillRect(self.rect(), QColor(0x2D, 0x2D, 0x2D))

        # Border on top
        painter.setClipping(False)
        painter.setPen(QPen(QColor(0x40, 0x40, 0x40), 1.0))
        painter.drawPath(path)

        painter.end()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_pos = None
