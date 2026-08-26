"""
Starfield Widget for POP AI Assistant Main Window Background.
Pure jet-black background with subtle, tiny, pure-white sparkling stars popping up and rotating 45° before turning off.
"""

import math
import random
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QBrush, QRadialGradient, QPainterPath
from PyQt6.QtWidgets import QWidget


class StarfieldWidget(QWidget):
    """Subtle cosmic background with tiny pure-white stars popping up 4-6 at a time across corners, rotating 45° before turning off."""

    def __init__(self, parent=None, star_count=28):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setObjectName("starfield")

        self.stars = []
        self.star_count = star_count
        self._init_stars()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(33)  # ~30 FPS

    def _init_stars(self):
        """Initialize fixed tiny pure-white star positions distributed in corners and edges."""
        w = max(self.width(), 960)
        h = max(self.height(), 600)
        self.stars.clear()

        # Define 8 regions around corners and edges to ensure sparse distribution
        regions = [
            (20, w * 0.35, 20, h * 0.35),           # Top-Left Corner
            (w * 0.65, w - 20, 20, h * 0.35),       # Top-Right Corner
            (20, w * 0.35, h * 0.65, h - 20),       # Bottom-Left Corner
            (w * 0.65, w - 20, h * 0.65, h - 20),   # Bottom-Right Corner
            (w * 0.35, w * 0.65, 20, h * 0.25),     # Top-Center Edge
            (w * 0.35, w * 0.65, h * 0.75, h - 20), # Bottom-Center Edge
            (20, w * 0.25, h * 0.35, h * 0.65),     # Left-Center Edge
            (w * 0.75, w - 20, h * 0.35, h * 0.65), # Right-Center Edge
        ]

        count_per_region = max(1, self.star_count // len(regions))
        total_created = 0

        for r_x1, r_x2, r_y1, r_y2 in regions:
            for _ in range(count_per_region):
                if total_created >= self.star_count:
                    break
                size = random.uniform(2.0, 4.2)
                max_alpha = random.randint(180, 255)
                twinkle_speed = random.uniform(0.015, 0.04)
                phase = (total_created / max(1, self.star_count)) * (2 * math.pi) + random.uniform(-0.3, 0.3)

                self.stars.append({
                    'x': random.uniform(r_x1, r_x2),
                    'y': random.uniform(r_y1, r_y2),
                    'size': size,
                    'max_alpha': max_alpha,
                    'current_alpha': 0,
                    'twinkle_speed': twinkle_speed,
                    'twinkle_phase': phase,
                    'rotation': 0.0,
                    'color': QColor(255, 255, 255),
                })
                total_created += 1

        while total_created < self.star_count:
            size = random.uniform(2.0, 4.2)
            max_alpha = random.randint(180, 255)
            twinkle_speed = random.uniform(0.015, 0.04)
            phase = random.uniform(0, 2 * math.pi)
            self.stars.append({
                'x': random.uniform(20, w - 20),
                'y': random.uniform(20, h - 20),
                'size': size,
                'max_alpha': max_alpha,
                'current_alpha': 0,
                'twinkle_speed': twinkle_speed,
                'twinkle_phase': phase,
                'rotation': 0.0,
                'color': QColor(255, 255, 255),
            })
            total_created += 1

    def _animate(self):
        """Update star twinkling phase so only ~4-6 stars pop up ('lấp ló') at a time, rotating 45° before turning off."""
        for star in self.stars:
            star['twinkle_phase'] += star['twinkle_speed']
            raw_sin = math.sin(star['twinkle_phase'])
            raw_cos = math.cos(star['twinkle_phase'])

            # Only visible when raw_sin >= 0.35
            if raw_sin > 0.35:
                normalized = (raw_sin - 0.35) / 0.65
                twinkle_factor = math.pow(normalized, 2.0)
                star['current_alpha'] = int(star['max_alpha'] * twinkle_factor)

                # Rotate 45° (pi / 4) during fade-out phase (raw_cos < 0)
                if raw_cos < 0:
                    fade_out_progress = (1.0 - raw_sin) / 0.65
                    star['rotation'] = fade_out_progress * (math.pi / 4.0)
                else:
                    star['rotation'] = 0.0
            else:
                star['current_alpha'] = 0
                star['rotation'] = 0.0

        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._init_stars()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Pure Jet-Black Background (#000000)
        painter.fillRect(0, 0, w, h, QColor(0, 0, 0))

        # Draw 4-Pointed Tiny White Sparkle Stars
        for star in self.stars:
            alpha = star['current_alpha']
            if alpha < 10:
                continue

            cx = star['x']
            cy = star['y']
            size = star['size']
            color = QColor(star['color'])
            color.setAlpha(alpha)
            rotation = star.get('rotation', 0.0)

            # Soft white radial glow for slightly larger stars
            if size > 3.2 and alpha > 160:
                glow_r = size * 2.0
                glow = QRadialGradient(cx, cy, glow_r)
                g_col = QColor(255, 255, 255, int(alpha * 0.25))
                glow.setColorAt(0.0, g_col)
                glow.setColorAt(1.0, QColor(0, 0, 0, 0))
                painter.setBrush(QBrush(glow))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(cx, cy), glow_r, glow_r)

            # Draw 4-pointed diamond star shape with rotation
            self._draw_four_point_star(painter, cx, cy, size, color, rotation)

    def _draw_four_point_star(self, painter, cx, cy, size, color, rotation=0.0):
        """Draw a symmetrical 4-pointed tiny diamond star sparkle rotated by rotation angle."""
        path = QPainterPath()
        r_outer = size
        r_inner = size * 0.22

        for i in range(8):
            angle = i * math.pi / 4.0 + rotation
            r = r_outer if i % 2 == 0 else r_inner
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)
        path.closeSubpath()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawPath(path)
