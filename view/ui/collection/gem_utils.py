"""
Gemstone & Jewel Rendering Utility for Mascot Cards.
Renders a glowing, faceted crystal gem embedded into card borders,
colored dynamically according to character rarity rank / rate.
"""

from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QRadialGradient, QLinearGradient, QPolygonF
)


def draw_embedded_gem(painter: QPainter, cx: float, cy: float, r_col: QColor, size: float = 10.0):
    """
    Vẽ viên ngọc pha lê phát sáng khảm nạm ở đáy thẻ theo màu rate.

    Args:
        painter: QPainter đang active
        cx: Toạ độ X tâm viên ngọc
        cy: Toạ độ Y tâm viên ngọc
        r_col: QColor của phẩm cấp (Rarity color)
        size: Kích thước bán kính tương đối của ngọc
    """
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 1. Vầng sáng hào quang mềm tỏa ra xung quanh (Ambient Radial Glow)
    glow_radius = size * 1.65
    glow_grad = QRadialGradient(cx, cy, glow_radius)
    glow_grad.setColorAt(0.0, QColor(r_col.red(), r_col.green(), r_col.blue(), 130))
    glow_grad.setColorAt(0.45, QColor(r_col.red(), r_col.green(), r_col.blue(), 45))
    glow_grad.setColorAt(1.0, QColor(r_col.red(), r_col.green(), r_col.blue(), 0))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(glow_grad))
    painter.drawEllipse(QRectF(cx - glow_radius, cy - glow_radius, glow_radius * 2.0, glow_radius * 2.0))

    # 2. Khung đế khảm ngọc bằng kim loại tối viền bạc (Bezel / Socket)
    socket_r = size * 0.72
    painter.setPen(QPen(QColor(255, 255, 255, 100), 0.9))
    painter.setBrush(QBrush(QColor(6, 9, 14, 245)))
    painter.drawEllipse(QRectF(cx - socket_r, cy - socket_r, socket_r * 2.0, socket_r * 2.0))

    # 3. Thân viên ngọc giác cắt kim cương hình thoi (Faceted Diamond Gemstone)
    hw = size * 0.52
    hh = size * 0.58
    diamond = QPolygonF([
        QPointF(cx, cy - hh),       # Đỉnh trên
        QPointF(cx + hw, cy),       # Đỉnh phải
        QPointF(cx, cy + hh),       # Đỉnh dưới
        QPointF(cx - hw, cy),       # Đỉnh trái
    ])

    gem_grad = QLinearGradient(cx - hw, cy - hh, cx + hw, cy + hh)
    gem_grad.setColorAt(0.0, r_col.lighter(175))   # Ánh sáng chói phản chiếu góc trên
    gem_grad.setColorAt(0.35, r_col.lighter(130))
    gem_grad.setColorAt(0.85, r_col)
    gem_grad.setColorAt(1.0, r_col.darker(145))    # Độ sâu đáy ngọc

    painter.setPen(QPen(r_col.lighter(185), 0.8))
    painter.setBrush(QBrush(gem_grad))
    painter.drawPolygon(diamond)

    # 4. Giác phản quang nội tại (Inner facet accent lines)
    painter.setPen(QPen(QColor(255, 255, 255, 90), 0.6))
    painter.drawLine(QPointF(cx, cy - hh), QPointF(cx, cy + hh))
    painter.drawLine(QPointF(cx - hw, cy), QPointF(cx + hw, cy))

    # 5. Đốm lấp lánh điểm nhấn (Specular Sparkle Highlight)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
    sparkle_size = max(1.5, size * 0.18)
    painter.drawEllipse(QRectF(cx - hw * 0.35, cy - hh * 0.40, sparkle_size, sparkle_size))

    painter.restore()

