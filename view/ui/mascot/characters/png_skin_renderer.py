"""PNG Skin Renderer - Renders custom user/community characters from PNG assets."""

import math
import os
import time
from typing import Dict, Optional
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPixmap, QColor, QFont
from model.voice_state_model import VoiceState
from view.ui.mascot.characters.base_character_renderer import BaseCharacterRenderer
from view.ui.mascot.mascot_model import MascotModel


class PngSkinRenderer(BaseCharacterRenderer):
    """Renders sprite-based mascot skins with breathing float and state transitions."""

    def __init__(self, skin_dir: str):
        self.skin_dir = skin_dir
        self._pixmaps: Dict[str, Optional[QPixmap]] = {}
        self._load_sprites()

    def _load_sprites(self):
        for state in ("idle", "blink", "talk", "sleep"):
            path = os.path.join(self.skin_dir, f"{state}.png")
            if os.path.isfile(path):
                pm = QPixmap(path)
                if not pm.isNull():
                    self._pixmaps[state] = pm
                else:
                    self._pixmaps[state] = None
            else:
                self._pixmaps[state] = None

    def _get_active_pixmap(self, model: MascotModel) -> Optional[QPixmap]:
        idle = self._pixmaps.get("idle")
        if model.is_sleeping:
            return self._pixmaps.get("sleep") or idle
        if model.voice_state == VoiceState.SPEAKING and model.mouth_open > 0.25:
            return self._pixmaps.get("talk") or idle
        if model.is_blinking:
            return self._pixmaps.get("blink") or idle
        return idle

    def paint(self, painter: QPainter, width: int, height: int, model: MascotModel) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        base_cx = width / 2.0
        cling_dx = 0.0
        cling_dy = 0.0
        cling_rot = 0.0

        if model.cling_edge == "left":
            cling_dx = -12.0 * model.cling_ratio
            cling_rot = -7.0 * model.cling_ratio
        elif model.cling_edge == "right":
            cling_dx = 12.0 * model.cling_ratio
            cling_rot = 7.0 * model.cling_ratio
        elif model.cling_edge == "top":
            cling_dy = -14.0 * model.cling_ratio
            cling_rot = math.sin(model.pulse_phase * 1.3) * 4.5 * model.cling_ratio
        elif model.cling_edge == "bottom":
            cling_dy = 8.0 * model.cling_ratio

        float_speed = 0.4 if model.is_sleeping else 1.2
        float_y = math.sin(model.pulse_phase) * float_speed

        cx = base_cx + cling_dx
        cy = (height / 2.0) + float_y + cling_dy

        painter.save()
        if abs(cling_rot) > 0.01:
            painter.translate(cx, cy)
            painter.rotate(cling_rot)
            painter.translate(-cx, -cy)

        pm = self._get_active_pixmap(model)
        target_size = 80.0  # Fit nicely inside 120x120 mascot frame
        if pm and not pm.isNull():
            scaled = pm.scaled(
                int(target_size), int(target_size),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            draw_x = cx - scaled.width() / 2.0
            draw_y = cy - scaled.height() / 2.0
            painter.drawPixmap(int(draw_x), int(draw_y), scaled)
        else:
            # Fallback placeholder circle if image missing
            painter.setBrush(QColor(100, 116, 139))
            painter.drawEllipse(QRectF(cx - 30, cy - 30, 60, 60))

        # Floating zZz particles if sleeping
        if model.is_sleeping and model.zzz_particles:
            font = QFont("Arial", 11, QFont.Weight.Bold)
            painter.setFont(font)
            for p in model.zzz_particles:
                alpha = max(0, min(255, int(p.get("alpha", 200))))
                painter.setPen(QColor(56, 189, 248, alpha))
                painter.drawText(QPointF(p["x"], p["y"]), p.get("char", "z"))

        painter.restore()
