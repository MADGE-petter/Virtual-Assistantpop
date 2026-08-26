"""
Starfield Widget - Pop Assistant
Pure jet-black background with subtle, tiny, pure-white sparkling stars lấp ló ở các góc.
"""

import random
import math
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush, QRadialGradient, QPainterPath


class StarfieldWidget(QWidget):
    """Subtle cosmic background with tiny pure-white stars popping up 3-4 at a time across corners."""
    
    def __init__(self, parent=None, star_count=16):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setObjectName("starfield")
        
        self.stars = []
        self.star_count = star_count
        self._init_stars()
        
        # Animation timer for smooth 30 FPS twinkling
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(33)
    
    def _init_stars(self):
        """Initialize fixed tiny pure-white star positions distributed in corners/edges."""
        w = max(self.width(), 360)
        h = max(self.height(), 460)
        
        self.stars.clear()

        # Define corner regions to ensure sparse distribution around corners & edges
        # (Top-Left, Top-Right, Bottom-Left, Bottom-Right, Middle-Left, Middle-Right)
        regions = [
            (15, w * 0.4, 15, h * 0.35),          # Top-Left
            (w * 0.6, w - 15, 15, h * 0.35),      # Top-Right
            (15, w * 0.4, h * 0.65, h - 15),      # Bottom-Left
            (w * 0.6, w - 15, h * 0.65, h - 15),  # Bottom-Right
            (15, w * 0.3, h * 0.35, h * 0.65),    # Middle-Left
            (w * 0.7, w - 15, h * 0.35, h * 0.65), # Middle-Right
        ]

        count_per_region = max(1, self.star_count // len(regions))
        total_created = 0

        for r_x1, r_x2, r_y1, r_y2 in regions:
            for _ in range(count_per_region):
                if total_created >= self.star_count:
                    break
                size = random.uniform(1.8, 3.8)  # Bé hơn nhiều
                max_alpha = random.randint(180, 255)
                twinkle_speed = random.uniform(0.02, 0.05)
                # Stagger initial phase evenly so only ~3-4 stars pop up at any given frame
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
                    'color': QColor(255, 255, 255),  # Màu trắng thuần
                })
                total_created += 1

        # Any remainder stars
        while total_created < self.star_count:
            size = random.uniform(1.8, 3.8)
            max_alpha = random.randint(180, 255)
            twinkle_speed = random.uniform(0.02, 0.05)
            phase = random.uniform(0, 2 * math.pi)
            self.stars.append({
                'x': random.uniform(15, w - 15),
                'y': random.uniform(15, h - 15),
                'size': size,
                'max_alpha': max_alpha,
                'current_alpha': 0,
                'twinkle_speed': twinkle_speed,
                'twinkle_phase': phase,
                'rotation': 0.0,
                'color': QColor(255, 255, 255),  # Màu trắng thuần
            })
            total_created += 1
    
    def _animate(self):
        """Update star twinkling phase so only ~3-4 stars pop up ('lấp ló') at a time, rotating 45° before turning off."""
        for star in self.stars:
            star['twinkle_phase'] += star['twinkle_speed']
            raw_sin = math.sin(star['twinkle_phase'])
            raw_cos = math.cos(star['twinkle_phase'])
            
            # Chỉ hiển thị ("lấp ló") khi raw_sin nằm ở phần đỉnh (>= 0.35)
            if raw_sin > 0.35:
                normalized = (raw_sin - 0.35) / 0.65
                twinkle_factor = math.pow(normalized, 2.0)
                star['current_alpha'] = int(star['max_alpha'] * twinkle_factor)

                # Xoay xoắn góc 45 độ (pi / 4) khi đang mờ dần chuẩn bị tắt (giai đoạn fade-out: raw_cos < 0)
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
            if size > 3.0 and alpha > 160:
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