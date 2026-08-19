"""
Starfield Widget - Pop Assistant
Animated starfield background with parallax layers and shooting stars
"""

import random
import math
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush, QRadialGradient, QLinearGradient, QPen


class StarfieldWidget(QWidget):
    """Animated starfield background widget"""
    
    def __init__(self, parent=None, star_count=120):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setObjectName("starfield")
        
        self.stars = []
        self.star_count = star_count
        self._init_stars()
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(50)  # ~20 FPS
        
        # Subtle color shift timer
        self.color_timer = QTimer(self)
        self.color_timer.timeout.connect(self._shift_colors)
        self.color_timer.start(3000)
        
        self._hue_offset = 0
    
    def _init_stars(self):
        """Initialize star positions and properties"""
        w = max(self.width(), 400)
        h = max(self.height(), 550)
        
        for _ in range(self.star_count):
            # Layered depth: 0=far (small, dim), 1=mid, 2=near (large, bright)
            layer = random.choices([0, 1, 2], weights=[0.5, 0.35, 0.15])[0]
            
            if layer == 0:  # Far stars
                size = random.uniform(0.5, 1.5)
                base_alpha = random.randint(30, 80)
                speed = random.uniform(0.05, 0.15)
                twinkle_speed = random.uniform(0.005, 0.015)
            elif layer == 1:  # Mid stars
                size = random.uniform(1.5, 2.5)
                base_alpha = random.randint(80, 150)
                speed = random.uniform(0.15, 0.3)
                twinkle_speed = random.uniform(0.01, 0.025)
            else:  # Near stars
                size = random.uniform(2.5, 4.0)
                base_alpha = random.randint(150, 220)
                speed = random.uniform(0.3, 0.5)
                twinkle_speed = random.uniform(0.02, 0.04)
            
            # Color variation: mostly white/blue, occasional warm
            color_type = random.choices([0, 1, 2], weights=[0.6, 0.3, 0.1])[0]
            if color_type == 0:  # Cool white/blue
                base_color = QColor(200, 220, 255)
            elif color_type == 1:  # Warm white
                base_color = QColor(255, 240, 220)
            else:  # Accent tint
                base_color = QColor(0, 255, 170)
            
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
                'drift_y': random.uniform(-0.01, 0.01),
            })
    
    def _animate(self):
        """Update star positions and twinkle"""
        w = self.width()
        h = self.height()
        
        for star in self.stars:
            # Vertical drift (parallax by layer)
            star['y'] += star['speed'] * (star['layer'] + 1) * 0.5
            star['x'] += star['drift_x'] * (star['layer'] + 1)
            
            # Wrap around
            if star['y'] > h + 10:
                star['y'] = -10
                star['x'] = random.uniform(0, w)
            if star['x'] < -10:
                star['x'] = w + 10
            elif star['x'] > w + 10:
                star['x'] = -10
            
            # Twinkle effect
            star['twinkle_phase'] += star['twinkle_speed']
            twinkle = (math.sin(star['twinkle_phase']) + 1) * 0.5  # 0 to 1
            star['current_alpha'] = int(star['base_alpha'] * (0.4 + 0.6 * twinkle))
        
        self.update()
    
    def _shift_colors(self):
        """Subtle color temperature shift over time"""
        self._hue_offset = (self._hue_offset + 1) % 360
        self.update()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Reinitialize stars for new size if needed
        if len(self.stars) < self.star_count:
            self._init_stars()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Draw subtle gradient overlay for depth
        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, QColor(3, 5, 8, 0))
        gradient.setColorAt(0.5, QColor(8, 12, 20, 0))
        gradient.setColorAt(1, QColor(5, 8, 16, 0))
        painter.fillRect(0, 0, w, h, gradient)
        
        # Draw stars
        for star in self.stars:
            alpha = star['current_alpha']
            color = star['base_color']
            color.setAlpha(alpha)
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            
            size = star['size']
            x = star['x']
            y = star['y']
            
            # Draw star as small circle with glow for near stars
            if star['layer'] == 2 and alpha > 180:
                # Glow effect
                glow_gradient = QRadialGradient(x, y, size * 3)
                glow_color = QColor(color)
                glow_color.setAlpha(int(alpha * 0.15))
                glow_gradient.setColorAt(0, glow_color)
                glow_gradient.setColorAt(1, QColor(0, 0, 0, 0))
                painter.setBrush(QBrush(glow_gradient))
                painter.drawEllipse(QPointF(x, y), size * 3, size * 3)
                
                # Core
                painter.setBrush(QBrush(color))
                painter.drawEllipse(QPointF(x, y), size, size)
            else:
                painter.drawEllipse(QPointF(x, y), size, size)
        
        # Draw occasional "shooting star" trail
        if random.random() < 0.002:  # Very rare
            self._draw_shooting_star(painter, w, h)
    
    def _draw_shooting_star(self, painter, w, h):
        """Draw a rare shooting star"""
        start_x = random.uniform(0, w)
        start_y = random.uniform(0, h * 0.3)
        length = random.uniform(80, 150)
        angle = random.uniform(-0.5, 0.5)  # Slight downward angle
        
        end_x = start_x + length * math.cos(angle)
        end_y = start_y + length * math.sin(angle)
        
        gradient = QLinearGradient(start_x, start_y, end_x, end_y)
        gradient.setColorAt(0, QColor(0, 255, 170, 180))
        gradient.setColorAt(0.5, QColor(0, 204, 255, 100))
        gradient.setColorAt(1, QColor(0, 204, 255, 0))
        
        painter.setPen(QPen(gradient, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(start_x, start_y), QPointF(end_x, end_y))