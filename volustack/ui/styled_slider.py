from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import QSlider, QStyle


class StyledSlider(QSlider):
    """Custom-painted slider — avoids stylesheet compositing artifacts
    on WA_TranslucentBackground windows."""

    _GROOVE_H = 4
    _HANDLE_R = 7
    _GROOVE = QColor(0x40, 0x40, 0x40)
    _FILL = QColor(0x60, 0xCD, 0xFF)
    _FILL_HOVER = QColor(0x78, 0xD6, 0xFF)
    _DIS_GROOVE = QColor(0x33, 0x33, 0x33)
    _DIS_FILL = QColor(0x55, 0x55, 0x55)

    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setMouseTracking(True)
        self._hover = False

    # -- painting --

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cy = h / 2.0
        r = self._HANDLE_R
        span = w - 2 * r

        pos = QStyle.sliderPositionFromValue(
            self.minimum(), self.maximum(), self.value(), int(span)
        )
        hx = r + pos  # handle centre-x

        dis = not self.isEnabled()
        gc = self._DIS_GROOVE if dis else self._GROOVE
        fc = self._DIS_FILL if dis else self._FILL
        hc = self._DIS_FILL if dis else (self._FILL_HOVER if self._hover else self._FILL)

        gh = self._GROOVE_H
        gy = cy - gh / 2.0

        # groove (full track)
        groove = QPainterPath()
        groove.addRoundedRect(0.0, gy, float(w), float(gh), 2.0, 2.0)
        p.fillPath(groove, gc)

        # sub-page (filled part, left of handle)
        if hx > 0:
            sub = QPainterPath()
            sub.addRoundedRect(0.0, gy, float(hx), float(gh), 2.0, 2.0)
            p.fillPath(sub, fc)

        # handle
        handle = QPainterPath()
        handle.addEllipse(float(hx - r), float(cy - r), float(r * 2), float(r * 2))
        p.fillPath(handle, hc)

        p.end()

    # -- mouse handling (bypasses style geometry, always in sync with paint) --

    def _value_at(self, x: float) -> int:
        r = self._HANDLE_R
        span = self.width() - 2 * r
        return QStyle.sliderValueFromPosition(
            self.minimum(), self.maximum(), int(x - r), int(span)
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setSliderDown(True)
            self.setValue(self._value_at(event.position().x()))
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.isSliderDown():
            self.setValue(self._value_at(event.position().x()))
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setSliderDown(False)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    # -- hover tracking --

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()
