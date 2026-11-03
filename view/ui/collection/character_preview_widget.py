"""
Character Preview Widget - Flat 2D Avatar Frame for Collection Views.
Renders mascot graphics inside a clean flat 2D card with natural muted colors.
"""

from typing import Optional
from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
from PyQt6.QtWidgets import QWidget

from service.collection.character_registry import RARITY_INFO, CharacterDef
from view.ui.mascot.characters import create_renderer_for_character
from view.ui.mascot.characters.base_character_renderer import BaseCharacterRenderer
from view.ui.mascot.mascot_model import MascotModel


class CharacterPreviewWidget(QWidget):
    """Compact flat 2D widget that renders a character's mascot sprite/vector."""

    def __init__(self, char: Optional[CharacterDef] = None, size: int = 64, animated: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._size = size
        is_ex = bool(char and (getattr(char, "is_exclusive", False) or char.id == "aemeath_idol"))
        self._animated = animated or is_ex
        self._char: Optional[CharacterDef] = char
        self._renderer: Optional[BaseCharacterRenderer] = (
            create_renderer_for_character(char) if char else None
        )
        self._model = MascotModel()
        self._model.cling_edge = None
        self._model.cling_ratio = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._timer: Optional[QTimer] = None
        if self._animated:
            self._timer = QTimer(self)
            self._timer.setInterval(33)
            self._timer.timeout.connect(self._on_tick)
            self._timer.start()

    def _on_tick(self):
        if not self.isVisible():
            return
        self._model.pulse_phase += 0.065
        self.update()

    def set_character(self, char: Optional[CharacterDef]) -> None:
        self._char = char
        self._renderer = create_renderer_for_character(char) if char else None
        self.update()

    def paintEvent(self, a0):
        super().paintEvent(a0)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Flat 2D background & subtle natural border
        r_info = RARITY_INFO.get(self._char.rarity, {}) if self._char else {}
        r_color = QColor(r_info.get("color", "#64748B"))

        is_ex = bool(self._char and (getattr(self._char, "is_exclusive", False) or self._char.id == "aemeath_idol"))
        if is_ex:
            bg_color = QColor("#221520")
            border_color = QColor("#F43F5E")
            painter.setPen(QPen(border_color, 1.4))
        else:
            bg_color = QColor("#1C1F26")
            border_color = QColor(r_color.red(), r_color.green(), r_color.blue(), 85)
            painter.setPen(QPen(border_color, 1.0))

        painter.setBrush(QBrush(bg_color))

        radius = 10.0 if self._size >= 70 else 8.0
        rect = QRectF(1.0, 1.0, self._size - 2.0, self._size - 2.0)
        painter.drawRoundedRect(rect, radius, radius)

        if self._renderer:
            pad = 4.0 if self._size < 72 else 5.0
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
