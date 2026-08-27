"""
POP Vector Icons Provider - Generates sharp vector QIcon / QPixmap objects matching po1 and po designs.
"""

import os
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QLinearGradient, QPainterPath
)


def get_pop_logo_pixmap(size: int = 40) -> QPixmap:
    """Generate POP AI Assistant Logo matching POP.png gradient brand icon in po1."""
    # Check if assets/POP.png exists first
    asset_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "POP.png")
    if os.path.exists(asset_path):
        pm = QPixmap(asset_path)
        if not pm.isNull():
            return pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0.0, QColor(0, 255, 255))
    gradient.setColorAt(0.5, QColor(0, 142, 255))
    gradient.setColorAt(1.0, QColor(124, 60, 255))

    path = QPainterPath()
    # Draw stylized 'P' curve logo shape
    r = size * 0.45
    cx = size * 0.45
    cy = size * 0.45
    path.moveTo(size * 0.25, size * 0.85)
    path.lineTo(size * 0.25, size * 0.15)
    path.lineTo(size * 0.55, size * 0.15)
    path.cubicTo(size * 0.85, size * 0.15, size * 0.85, size * 0.55, size * 0.55, size * 0.55)
    path.lineTo(size * 0.25, size * 0.55)

    pen = QPen(QBrush(gradient), size * 0.18, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.drawPath(path)
    painter.end()
    return pix


def get_pop_logo_icon(size: int = 32) -> QIcon:
    return QIcon(get_pop_logo_pixmap(size))


def get_brand_logo_pixmap(brand: str, size: int = 32) -> QPixmap:
    """Generate high quality vector brand logos (Google, Qwen, Meta, Mistral, Liquid, HuggingFace)."""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    b = brand.lower()
    s = float(size)
    cx, cy = s / 2.0, s / 2.0

    if "gemma" in b or "google" in b:
        # Google 4-color G logo badge
        # Draw outer circle background with subtle dark container
        painter.setBrush(QBrush(QColor(24, 32, 45)))
        painter.setPen(QPen(QColor(66, 133, 244, 100), 1))
        painter.drawRoundedRect(QRectF(1, 1, s - 2, s - 2), s * 0.25, s * 0.25)
        
        # 4-color Google geometric arc
        pen_w = s * 0.16
        r = s * 0.26
        rect = QRectF(cx - r, cy - r, r * 2, r * 2)
        
        # Red top
        painter.setPen(QPen(QColor(234, 67, 53), pen_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        painter.drawArc(rect, 45 * 16, 135 * 16)
        # Yellow left
        painter.setPen(QPen(QColor(251, 188, 5), pen_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        painter.drawArc(rect, 180 * 16, 90 * 16)
        # Green bottom
        painter.setPen(QPen(QColor(52, 168, 83), pen_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        painter.drawArc(rect, 270 * 16, 90 * 16)
        # Blue right bar
        painter.setPen(QPen(QColor(66, 133, 244), pen_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        painter.drawArc(rect, 0, 45 * 16)
        painter.setPen(QPen(QColor(66, 133, 244), pen_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(cx, cy), QPointF(cx + r, cy))

    elif "qwen" in b or "alibaba" in b:
        # Qwen Whale Purple-Blue gradient logo
        grad = QLinearGradient(0, 0, s, s)
        grad.setColorAt(0.0, QColor(97, 92, 237))   # Qwen Deep Violet
        grad.setColorAt(1.0, QColor(48, 178, 255))  # Qwen Bright Cyan
        
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Draw Qwen Whale body curve path
        path = QPainterPath()
        path.moveTo(s * 0.15, s * 0.65)
        path.cubicTo(s * 0.15, s * 0.35, s * 0.45, s * 0.2, s * 0.75, s * 0.25)
        path.cubicTo(s * 0.9, s * 0.3, s * 0.85, s * 0.55, s * 0.65, s * 0.7)
        path.cubicTo(s * 0.45, s * 0.85, s * 0.25, s * 0.8, s * 0.15, s * 0.65)
        painter.drawPath(path)
        
        # Tail fin
        tail = QPainterPath()
        tail.moveTo(s * 0.75, s * 0.25)
        tail.lineTo(s * 0.9, s * 0.15)
        tail.lineTo(s * 0.85, s * 0.4)
        painter.drawPath(tail)

    elif "llama" in b or "meta" in b:
        # Meta Llama Infinity Gradient Logo
        grad = QLinearGradient(0, 0, s, s)
        grad.setColorAt(0.0, QColor(0, 129, 251))  # Meta Blue
        grad.setColorAt(1.0, QColor(0, 198, 255))  # Meta Cyan
        
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QBrush(grad), s * 0.16, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        
        # Infinity loop path
        path = QPainterPath()
        path.moveTo(cx, cy)
        path.cubicTo(cx - s * 0.3, cy - s * 0.3, cx - s * 0.4, cy + s * 0.3, cx - s * 0.25, cy + s * 0.2)
        path.cubicTo(cx - s * 0.1, cy + s * 0.1, cx + s * 0.1, cy - s * 0.1, cx + s * 0.25, cy - s * 0.2)
        path.cubicTo(cx + s * 0.4, cy - s * 0.3, cx + s * 0.3, cy + s * 0.3, cx, cy)
        painter.drawPath(path)

    elif "mistral" in b or "mixtral" in b:
        # Mistral AI 5-bar orange/gold logo
        grad = QLinearGradient(0, 0, 0, s)
        grad.setColorAt(0.0, QColor(255, 112, 0))   # Warm Orange
        grad.setColorAt(1.0, QColor(255, 184, 0))   # Bright Amber
        
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        
        bar_w = s * 0.12
        spacing = s * 0.06
        start_x = (s - (5 * bar_w + 4 * spacing)) / 2.0
        heights = [0.4, 0.7, 0.9, 0.7, 0.4]
        
        for i, h in enumerate(heights):
            x = start_x + i * (bar_w + spacing)
            bh = s * h
            y = (s - bh) / 2.0
            painter.drawRoundedRect(QRectF(x, y, bar_w, bh), bar_w * 0.4, bar_w * 0.4)

    elif "lfm" in b or "liquid" in b:
        # Liquid AI Cyan Drop Logo
        grad = QLinearGradient(0, 0, s, s)
        grad.setColorAt(0.0, QColor(0, 255, 170))
        grad.setColorAt(1.0, QColor(0, 142, 255))
        
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        
        path = QPainterPath()
        path.moveTo(cx, s * 0.15)
        path.cubicTo(cx + s * 0.35, s * 0.5, cx + s * 0.35, s * 0.8, cx, s * 0.8)
        path.cubicTo(cx - s * 0.35, s * 0.8, cx - s * 0.35, s * 0.5, cx, s * 0.15)
        painter.drawPath(path)

    else:
        # Hugging Face Official Gold Badge
        grad = QLinearGradient(0, 0, s, s)
        grad.setColorAt(0.0, QColor(255, 210, 30))  # HF Gold
        grad.setColorAt(1.0, QColor(255, 157, 0))  # HF Orange
        
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(2, 2, s - 4, s - 4), s * 0.25, s * 0.25)
        
        # Hugging Face face line details
        painter.setPen(QPen(QColor(50, 40, 0), s * 0.08, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        # Eyes
        painter.drawPoint(QPointF(cx - s * 0.15, cy - s * 0.08))
        painter.drawPoint(QPointF(cx + s * 0.15, cy - s * 0.08))
        # Smile arc
        painter.drawArc(QRectF(cx - s * 0.18, cy - s * 0.1, s * 0.36, s * 0.26), 200 * 16, 140 * 16)

    painter.end()
    return pix


def get_brand_logo_icon(brand: str, size: int = 32) -> QIcon:
    return QIcon(get_brand_logo_pixmap(brand, size))


def create_vector_icon(icon_type: str, color_hex: str = "#96D7E9", size: int = 24) -> QIcon:
    """Create vector QIcon for any toolbar / sidebar button."""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    color = QColor(color_hex)
    pen = QPen(color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)

    s = size
    pad = s * 0.2

    if icon_type == "search":
        # Search magnifying glass
        r = s * 0.28
        cx, cy = s * 0.4, s * 0.4
        painter.drawEllipse(QPointF(cx, cy), r, r)
        painter.drawLine(QPointF(cx + r * 0.707, cy + r * 0.707), QPointF(s * 0.8, s * 0.8))

    elif icon_type == "plus":
        # Plus icon
        painter.drawLine(QPointF(s * 0.5, pad), QPointF(s * 0.5, s - pad))
        painter.drawLine(QPointF(pad, s * 0.5), QPointF(s - pad, s * 0.5))

    elif icon_type == "attachment":
        # Paperclip icon
        path = QPainterPath()
        path.moveTo(s * 0.65, s * 0.3)
        path.lineTo(s * 0.4, s * 0.6)
        path.cubicTo(s * 0.3, s * 0.7, s * 0.3, s * 0.85, s * 0.45, s * 0.85)
        path.cubicTo(s * 0.6, s * 0.85, s * 0.75, s * 0.7, s * 0.75, s * 0.5)
        path.lineTo(s * 0.5, s * 0.2)
        painter.drawPath(path)

    elif icon_type == "mic":
        # Microphone
        mw = s * 0.22
        mh = s * 0.38
        cx = s * 0.5
        cy = s * 0.35
        painter.drawRoundedRect(QRectF(cx - mw/2, cy - mh/2, mw, mh), mw/2, mw/2)
        # Stand arc
        painter.drawArc(QRectF(cx - s * 0.22, cy - s * 0.1, s * 0.44, s * 0.38), 180 * 16, 180 * 16)
        painter.drawLine(QPointF(cx, cy + s * 0.28), QPointF(cx, cy + s * 0.4))

    elif icon_type == "send":
        # Up arrow / Send
        painter.drawLine(QPointF(s * 0.5, s * 0.75), QPointF(s * 0.5, s * 0.25))
        painter.drawLine(QPointF(s * 0.28, s * 0.45), QPointF(s * 0.5, s * 0.25))
        painter.drawLine(QPointF(s * 0.72, s * 0.45), QPointF(s * 0.5, s * 0.25))

    elif icon_type == "settings":
        # Gear icon
        cx, cy = s * 0.5, s * 0.5
        r_out = s * 0.35
        r_in = s * 0.18
        painter.drawEllipse(QPointF(cx, cy), r_in, r_in)
        painter.drawEllipse(QPointF(cx, cy), r_out, r_out)

    elif icon_type == "waveform":
        # Waveform voice mode status icon
        bars = [0.3, 0.6, 0.9, 0.5, 0.8, 0.4]
        bw = s * 0.08
        gap = s * 0.06
        start_x = s * 0.2
        for i, h_ratio in enumerate(bars):
            bx = start_x + i * (bw + gap)
            bh = s * 0.6 * h_ratio
            by = s * 0.5 - bh / 2
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(bx, by, bw, bh), bw/2, bw/2)

    elif icon_type == "panel_toggle":
        # Right panel drawer toggle icon (po #12)
        painter.drawRoundedRect(QRectF(pad, pad, s - 2 * pad, s - 2 * pad), 4, 4)
        painter.drawLine(QPointF(s * 0.65, pad), QPointF(s * 0.65, s - pad))

    elif icon_type == "sidebar_toggle":
        # Left sidebar collapse arrow
        painter.drawLine(QPointF(s * 0.6, pad), QPointF(s * 0.35, s * 0.5))
        painter.drawLine(QPointF(s * 0.35, s * 0.5), QPointF(s * 0.6, s - pad))
        painter.drawLine(QPointF(s * 0.75, pad), QPointF(s * 0.5, s * 0.5))

    elif icon_type == "copy":
        # Copy clipboard
        painter.drawRoundedRect(QRectF(s * 0.2, s * 0.35, s * 0.45, s * 0.45), 3, 3)
        painter.drawRoundedRect(QRectF(s * 0.35, s * 0.2, s * 0.45, s * 0.45), 3, 3)

    elif icon_type == "like":
        # Thumbs up icon
        painter.drawRoundedRect(QRectF(s * 0.2, s * 0.45, s * 0.15, s * 0.35), 2, 2)
        path = QPainterPath()
        path.moveTo(s * 0.38, s * 0.48)
        path.lineTo(s * 0.48, s * 0.25)
        path.lineTo(s * 0.62, s * 0.25)
        path.lineTo(s * 0.58, s * 0.45)
        path.lineTo(s * 0.82, s * 0.45)
        path.lineTo(s * 0.72, s * 0.8)
        path.lineTo(s * 0.38, s * 0.8)
        painter.drawPath(path)

    elif icon_type == "dislike":
        # Thumbs down icon
        painter.drawRoundedRect(QRectF(s * 0.2, s * 0.2, s * 0.15, s * 0.35), 2, 2)
        path = QPainterPath()
        path.moveTo(s * 0.38, s * 0.52)
        path.lineTo(s * 0.48, s * 0.75)
        path.lineTo(s * 0.62, s * 0.75)
        path.lineTo(s * 0.58, s * 0.55)
        path.lineTo(s * 0.82, s * 0.55)
        path.lineTo(s * 0.72, s * 0.2)
        path.lineTo(s * 0.38, s * 0.2)
        painter.drawPath(path)

    elif icon_type == "retry":
        # Refresh / Regenerate icon
        painter.drawArc(QRectF(pad, pad, s - 2*pad, s - 2*pad), 40 * 16, 280 * 16)
        painter.drawLine(QPointF(s * 0.7, s * 0.2), QPointF(s * 0.85, s * 0.25))

    elif icon_type == "dots":
        # 3 dots menu
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        r = s * 0.07
        painter.drawEllipse(QPointF(s * 0.5, s * 0.3), r, r)
        painter.drawEllipse(QPointF(s * 0.5, s * 0.5), r, r)
        painter.drawEllipse(QPointF(s * 0.5, s * 0.7), r, r)

    elif icon_type == "user":
        # User avatar icon
        cx, cy = s * 0.5, s * 0.35
        r = s * 0.2
        painter.drawEllipse(QPointF(cx, cy), r, r)
        painter.drawArc(QRectF(s * 0.2, s * 0.5, s * 0.6, s * 0.4), 0, 180 * 16)

    painter.end()
    return QIcon(pix)
