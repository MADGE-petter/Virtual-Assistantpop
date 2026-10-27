"""
Character Preview Widget - Procedural avatar rendering for collection views.
Renders mascot vector or skin graphics inside a responsive frame with rarity accent glow.
"""

from typing import Optional
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
from PyQt6.QtWidgets import QWidget

from service.collection.character_registry import RARITY_INFO, CharacterDef
from view.ui.mascot.characters import create_renderer_for_character
from view.ui.mascot.characters.base_character_renderer import BaseCharacterRenderer
from view.ui.mascot.mascot_model import MascotModel


class CharacterPreviewWidget(QWidget):
    """Compact widget that renders a character's mascot sprite/vector."""

    def __init__(self, char: Optional[CharacterDef] = None, size: int = 64, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._size = size
        self._char: Optional[CharacterDef] = char
        self._renderer: Optional[BaseCharacterRenderer] = (
            create_renderer_for_character(char) if char else None
        )
        self._model = MascotModel()
        self._model.cling_edge = None
        self._model.cling_ratio = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_character(self, char: Optional[CharacterDef]) -> None:
        self._char = char
        self._renderer = create_renderer_for_character(char) if char else None
        self.update()

    def paintEvent(self, a0):
        super().paintEvent(a0)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Background badge with rarity-tinted glow
        r_info = RARITY_INFO.get(self._char.rarity, {}) if self._char else {}
        r_color_hex = r_info.get("color", "#38BDF8")
        r_color = QColor(r_color_hex)

        bg_color = QColor(r_color)
        bg_color.setAlpha(28)

        border_pen = QPen(QColor(r_color.red(), r_color.green(), r_color.blue(), 120), 1.2)
        painter.setPen(border_pen)
        painter.setBrush(QBrush(bg_color))

        rect = QRectF(1.5, 1.5, self._size - 3.0, self._size - 3.0)
        painter.drawRoundedRect(rect, 10.0, 10.0)

        # Draw Mascot
        if self._renderer:
            # All renderers are designed for standard 120x120 canvas
            pad = 6.0
            avail = max(1.0, float(self._size) - pad * 2.0)
            scale = avail / 120.0

            painter.save()
            painter.translate(pad, pad)
            painter.scale(scale, scale)
            try:
                self._renderer.paint(painter, 120, 120, self._model)
            except Exception as e:
                print(f"[CharacterPreviewWidget] Paint error for {self._char.id if self._char else 'unknown'}: {e}")
            painter.restore()
