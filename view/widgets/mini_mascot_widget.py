"""
POP Mini Floating Mascot Widget - Always-on-Top Desktop Floating Assistant matching specification.
"""

import math
from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal, QRectF, QSettings
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
        self._settings = QSettings("PopAI", "MiniMascot")

        self.setFixedSize(72, 72)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("POP AI Assistant Mini Mascot\n• Click đơn: Micro\n• Bấm đúp (Double-click): Mở/Ẩn cửa sổ Chat")

        # Load saved desktop position
        saved_pos = self._settings.value("position", None)
        if saved_pos and isinstance(saved_pos, QPoint):
            self.move(saved_pos)

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
        if event.button() == Qt.MouseButton.LeftButton:
            # Save new desktop position
            self._settings.setValue("position", self.pos())
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx, cy = w / 2.0, h / 2.0
        r = 28.0

        # Dynamic State Color & Multi-Ring Pulse
        if self.voice_state == VoiceState.READY:
            primary_color = QColor(0, 255, 170)    # Emerald Green
            secondary_color = QColor(0, 204, 255)  # Cyan
            pulse_speed = 1.0
        elif self.voice_state == VoiceState.LISTENING:
            primary_color = QColor(0, 255, 255)    # Neon Cyan
            secondary_color = QColor(0, 150, 255)  # Deep Sky Blue
            pulse_speed = 2.5
        elif self.voice_state == VoiceState.THINKING:
            primary_color = QColor(255, 204, 0)    # Neon Gold / Amber
            secondary_color = QColor(255, 102, 0)  # Sunset Orange
            pulse_speed = 2.0
        elif self.voice_state == VoiceState.SPEAKING:
            primary_color = QColor(124, 60, 255)   # Electric Purple
            secondary_color = QColor(255, 75, 180)  # Hot Pink
            pulse_speed = 1.8
        else:
            primary_color = QColor(85, 112, 136)   # Slate Muted
            secondary_color = QColor(40, 60, 80)
            pulse_speed = 0.5

        # Multi-layer Neon Pulse Radius Calculation
        pulse_val = math.sin(self._pulse_phase * pulse_speed)
        pulse_r = r + 6.0 + 4.0 * pulse_val
        outer_r = pulse_r + 6.0

        # Layer 1: Distant Neon Glow Aura
        outer_grad = QRadialGradient(cx, cy, outer_r)
        g1 = QColor(secondary_color)
        g1.setAlpha(60)
        outer_grad.setColorAt(0.0, g1)
        outer_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(outer_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2))

        # Layer 2: Core Neon Ring Glow
        inner_grad = QRadialGradient(cx, cy, pulse_r + 2)
        g2 = QColor(primary_color)
        g2.setAlpha(140)
        inner_grad.setColorAt(0.0, g2)
        inner_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(inner_grad))
        painter.drawEllipse(QRectF(cx - pulse_r, cy - pulse_r, pulse_r * 2, pulse_r * 2))

        # Layer 3: Dark Glass Core Circle
        bg_grad = QRadialGradient(cx, cy, r)
        bg_grad.setColorAt(0.0, QColor(16, 22, 31, 245))
        bg_grad.setColorAt(1.0, QColor(8, 15, 22, 255))
        painter.setBrush(QBrush(bg_grad))
        
        # Neon Border Stroke with pulsating thickness
        border_pen = QPen(primary_color, 2.0 + 0.5 * pulse_val)
        painter.setPen(border_pen)
        painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # Draw POP Logo in Center
        logo_pix = get_pop_logo_pixmap(32)
        painter.drawPixmap(int(cx - 16), int(cy - 16), logo_pix)
