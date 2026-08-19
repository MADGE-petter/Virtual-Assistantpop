"""
POP Mini Floating Mascot Widget - Always-on-Top Desktop Floating Assistant matching specification.
"""

import math
from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QRadialGradient, QMouseEvent
from PyQt6.QtWidgets import QWidget

from view.ui.styles import DesignTokens
from view.ui.icons import get_pop_logo_pixmap
from model.voice_state_model import VoiceState


class MiniMascotWidget(QWidget):
    """Always-On-Top Floating Circular Mascot Widget on Desktop."""

    toggleMainWindowRequested = pyqtSignal()
    toggleVoiceRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.voice_state = VoiceState.READY
        self._drag_pos = QPoint()
        self._pulse_phase = 0.0

        self.setFixedSize(72, 72)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("POP AI Assistant Mini Mascot\n• Click đơn: Micro\n• Bấm đúp (Double-click): Mở/Ẩn cửa sổ Chat")

        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(40)  # ~25 FPS

    def set_voice_state(self, state: VoiceState):
        self.voice_state = state
        self.update()

    def _animate(self):
        self._pulse_phase += 0.1
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            print("[MiniMascot] Double-click detected! Toggling main POP window.")
            self.toggleMainWindowRequested.emit()
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        # Single click toggle voice if not dragging significantly
        if event.button() == Qt.MouseButton.LeftButton:
            pass  # Handled or click signal

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx, cy = w / 2.0, h / 2.0
        r = 28.0

        # State color selection
        if self.voice_state == VoiceState.READY:
            halo_color = QColor(0, 255, 170)
        elif self.voice_state == VoiceState.LISTENING:
            halo_color = QColor(0, 255, 255)
        elif self.voice_state == VoiceState.THINKING:
            halo_color = QColor(255, 204, 0)
        elif self.voice_state == VoiceState.SPEAKING:
            halo_color = QColor(124, 60, 255)
        else:  # SLEEPING
            halo_color = QColor(85, 112, 136)

        # Pulse halo radius
        pulse_r = r + 6.0 + 3.0 * math.sin(self._pulse_phase)

        # Outer Radial Glow
        grad = QRadialGradient(cx, cy, pulse_r + 4)
        g_col = QColor(halo_color)
        g_col.setAlpha(80)
        grad.setColorAt(0.0, g_col)
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))

        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - pulse_r, cy - pulse_r, pulse_r * 2, pulse_r * 2))

        # Core Background Circle
        bg_grad = QRadialGradient(cx, cy, r)
        bg_grad.setColorAt(0.0, QColor(16, 22, 31, 240))
        bg_grad.setColorAt(1.0, QColor(8, 15, 22, 255))
        painter.setBrush(QBrush(bg_grad))
        painter.setPen(QPen(halo_color, 2))
        painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # Draw POP Logo in Center
        logo_pix = get_pop_logo_pixmap(32)
        painter.drawPixmap(int(cx - 16), int(cy - 16), logo_pix)
