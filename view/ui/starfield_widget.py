"""
Starfield Widget for POP AI Assistant Main Window Background.
"""

import math
import random
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QBrush, QRadialGradient, QLinearGradient, QPen
from PyQt6.QtWidgets import QWidget


class StarfieldWidget(QWidget):
    """Animated interactive starfield space background widget."""

    def __init__(self, parent=None, star_count=130):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setObjectName("starfield")

        self.stars = []
        self.star_count = star_count
        self._init_stars()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(40)  # ~25 FPS

        self._hue_offset = 0

    def _init_stars(self):
        w = max(self.width(), 800)
        h = max(self.height(), 600)
        self.stars = []

        for _ in range(self.star_count):
            layer = random.choices([0, 1, 2], weights=[0.5, 0.35, 0.15])[0]
            if layer == 0:
                size = random.uniform(0.6, 1.4)
                base_alpha = random.randint(30, 90)
                speed = random.uniform(0.04, 0.12)
                twinkle_speed = random.uniform(0.005, 0.015)
            elif layer == 1:
                size = random.uniform(1.5, 2.4)
                base_alpha = random.randint(90, 160)
                speed = random.uniform(0.12, 0.25)
                twinkle_speed = random.uniform(0.01, 0.025)
            else:
                size = random.uniform(2.5, 3.8)
                base_alpha = random.randint(160, 230)
                speed = random.uniform(0.25, 0.45)
                twinkle_speed = random.uniform(0.02, 0.04)

            color_type = random.choices([0, 1, 2], weights=[0.6, 0.3, 0.1])[0]
            if color_type == 0:
                base_color = QColor(190, 220, 255)
            elif color_type == 1:
                base_color = QColor(255, 240, 220)
            else:
                base_color = QColor(0, 255, 200)

            self.stars.append({
                'x': random.uniform(0, w),
                'y': random.uniform(0, h),
                'size': size,
                'base_alpha': base_alpha,
                'current_alpha': base_alpha,
                'speed': speed,
                'twinkle_speed': twinkle_speed,
                'twinkle_phase': random.uniform(0, 2 * math.pi),
                'layer': layer,
                'base_color': base_color,
                'drift_x': random.uniform(-0.02, 0.02),
            })

    def _animate(self):
        w = self.width()
        h = self.height()
        for star in self.stars:
            star['y'] += star['speed'] * (star['layer'] + 1) * 0.4
            star['x'] += star['drift_x'] * (star['layer'] + 1)

            if star['y'] > h + 10:
                star['y'] = -10
                star['x'] = random.uniform(0, w)
            if star['x'] < -10:
                star['x'] = w + 10
            elif star['x'] > w + 10:
                star['x'] = -10

            star['twinkle_phase'] += star['twinkle_speed']
            twinkle = (math.sin(star['twinkle_phase']) + 1) * 0.5
            star['current_alpha'] = int(star['base_alpha'] * (0.4 + 0.6 * twinkle))

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Dark space radial ambient glow in top-left & bottom-right
        rad1 = QRadialGradient(w * 0.1, h * 0.2, max(w, h) * 0.6)
        rad1.setColorAt(0, QColor(0, 180, 255, 18))
        rad1.setColorAt(0.6, QColor(120, 40, 255, 10))
        rad1.setColorAt(1, QColor(3, 5, 11, 0))
        painter.fillRect(0, 0, w, h, QBrush(rad1))

        # Stars rendering
        for star in self.stars:
            alpha = star['current_alpha']
            color = QColor(star['base_color'])
            color.setAlpha(alpha)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))

            size = star['size']
            x = star['x']
            y = star['y']

            if star['layer'] == 2 and alpha > 180:
                glow_gradient = QRadialGradient(x, y, size * 3)
                glow_color = QColor(color)
                glow_color.setAlpha(int(alpha * 0.2))
                glow_gradient.setColorAt(0, glow_color)
                glow_gradient.setColorAt(1, QColor(0, 0, 0, 0))
                painter.setBrush(QBrush(glow_gradient))
                painter.drawEllipse(QPointF(x, y), size * 3, size * 3)

                painter.setBrush(QBrush(color))
                painter.drawEllipse(QPointF(x, y), size, size)
            else:
                painter.drawEllipse(QPointF(x, y), size, size)
