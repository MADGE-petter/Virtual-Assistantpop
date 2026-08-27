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
    """Load high resolution official brand logo PNG image from assets/logos/."""
    b = brand.lower()
    logo_filename = "huggingface.png"

    if "gemma" in b or "google" in b:
        logo_filename = "google.png"
    elif "qwen" in b:
        logo_filename = "qwen.png"
    elif "kimi" in b or "moonshot" in b:
        logo_filename = "kimi.png"
    elif "mimo" in b or "xiaomi" in b:
        logo_filename = "mimo.png"
    elif "lfm" in b or "liquid" in b:
        logo_filename = "lfm.png"
    elif "llama" in b or "meta" in b:
        logo_filename = "meta.png"
    elif "mistral" in b or "mixtral" in b:
        logo_filename = "mistral.png"

    logos_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "logos")
    logo_path = os.path.join(logos_dir, logo_filename)
    if not os.path.exists(logo_path):
        logo_path = os.path.join(logos_dir, "huggingface.png")

    if os.path.exists(logo_path):
        pix = QPixmap(logo_path)
        if not pix.isNull():
            return pix.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    # Fallback blank transparent pixmap
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
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
