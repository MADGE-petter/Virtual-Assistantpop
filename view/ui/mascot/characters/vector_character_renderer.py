"""Vector Character Renderer - Procedural chibi rendering for all custom vector characters."""

import math
import time
from typing import Any, Dict, List
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QLinearGradient, QRadialGradient,
    QPainterPath, QPolygonF, QFont
)
from model.voice_state_model import VoiceState
from view.ui.mascot.characters.base_character_renderer import BaseCharacterRenderer
from view.ui.mascot.mascot_model import MascotModel


class VectorCharacterRenderer(BaseCharacterRenderer):
    """Procedurally renders characters based on declarative spec attributes."""

    def __init__(self, spec: Dict[str, Any]):
        self.spec = spec or {}

        # Colors
        self.body_col1 = QColor(self.spec.get("body", "#38BDF8"))
        self.body_col2 = QColor(self.spec.get("body2", "#0284C7"))
        self.accent_col = QColor(self.spec.get("accent", "#F0F9FF"))
        self.eye_col = QColor(self.spec.get("eye", "#0284C7"))
        self.outline_col = QColor(self.spec.get("outline", self.accent_col.name()))
        self.is_light_body = bool(self.spec.get("light_body", False))

        self.shape = self.spec.get("shape", "round")
        self.ears = self.spec.get("ears", "none")
        self.tail = self.spec.get("tail", "none")
        self.extras: List[str] = self.spec.get("extras", [])

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
            pendulum = math.sin(model.pulse_phase * 1.3) * 4.5
            cling_rot = pendulum * model.cling_ratio
        elif model.cling_edge == "bottom":
            cling_dy = 8.0 * model.cling_ratio

        float_speed = 0.4 if model.is_sleeping else 1.8
        float_y = math.sin(model.pulse_phase) * float_speed

        cx = base_cx + cling_dx
        cy = (height / 2.0) + float_y + cling_dy

        painter.save()
        if abs(cling_rot) > 0.01:
            painter.translate(cx, cy)
            painter.rotate(cling_rot)
            painter.translate(-cx, -cy)

        now = time.time()
        is_dizzy = now < model.dizzy_end_time
        is_waking_up = now < model.wake_up_until

        # 1. Background Extras (Halo, Rainbow Aura, Cape, Wings)
        self._draw_bg_extras(painter, cx, cy, model)

        # 2. Tail
        self._draw_tail(painter, cx, cy, model)

        # 3. Ears / Horns / Antenna
        self._draw_ears(painter, cx, cy, model)

        # 4. Main Body & Head
        self._draw_body(painter, cx, cy, model)

        # 5. Foreground Extras (Crown, Visor, Beak, Comb, Bun Swirl, etc.)
        self._draw_fg_extras(painter, cx, cy, model)

        # 6. Cheeks
        self._draw_cheeks(painter, cx, cy, model)

        # 7. Eyes
        self._draw_eyes(painter, cx, cy, model, is_dizzy, is_waking_up)

        # 8. Mouth
        self._draw_mouth(painter, cx, cy, model, is_dizzy, is_waking_up)

        # 9. Paws / Limbs
        self._draw_limbs(painter, cx, cy, model)

        # 10. Floating particles (zZz / Orbit stars)
        self._draw_particles(painter, cx, cy, model)

        painter.restore()

    # ============================================================
    # SUB-RENDERERS
    # ============================================================

    def _draw_bg_extras(self, painter: QPainter, cx: float, cy: float, model: MascotModel):
        if "rainbow_aura" in self.extras:
            pulse = (math.sin(model.pulse_phase * 2.0) + 1.0) / 2.0
            grad = QRadialGradient(cx, cy, 48 + pulse * 6)
            grad.setColorAt(0.0, QColor(251, 146, 60, int(120 + pulse * 60)))
            grad.setColorAt(0.5, QColor(236, 72, 153, int(80 + pulse * 40)))
            grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(cx - 52, cy - 52, 104, 104))

        if "halo" in self.extras:
            painter.setPen(QPen(QColor(253, 224, 71, 230), 2.2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(cx - 18, cy - 36, 36, 10))

        if "flame_wings" in self.extras:
            wing_sway = math.sin(model.pulse_phase * 2.5) * 6.0
            painter.setPen(Qt.PenStyle.NoPen)
            # Left flame wing
            grad_l = QLinearGradient(cx - 38, cy - 10, cx - 18, cy + 10)
            grad_l.setColorAt(0.0, QColor(251, 146, 60, 220))
            grad_l.setColorAt(1.0, QColor(239, 68, 68, 160))
            painter.setBrush(QBrush(grad_l))
            p_left = QPolygonF([
                QPointF(cx - 16, cy + 6),
                QPointF(cx - 40 - wing_sway, cy - 14),
                QPointF(cx - 30, cy + 12)
            ])
            painter.drawPolygon(p_left)
            # Right flame wing
            p_right = QPolygonF([
                QPointF(cx + 16, cy + 6),
                QPointF(cx + 40 + wing_sway, cy - 14),
                QPointF(cx + 30, cy + 12)
            ])
            painter.drawPolygon(p_right)

        if "dragon_wings" in self.extras:
            sway = math.sin(model.pulse_phase * 2.0) * 4.0
            painter.setBrush(QBrush(QColor(129, 140, 248, 200)))
            painter.setPen(QPen(QColor(199, 210, 254), 1.2))
            p_l = QPolygonF([
                QPointF(cx - 14, cy + 4),
                QPointF(cx - 36 - sway, cy - 10),
                QPointF(cx - 30, cy + 10)
            ])
            p_r = QPolygonF([
                QPointF(cx + 14, cy + 4),
                QPointF(cx + 36 + sway, cy - 10),
                QPointF(cx + 30, cy + 10)
            ])
            painter.drawPolygon(p_l)
            painter.drawPolygon(p_r)

        if "cape" in self.extras:
            cape_grad = QLinearGradient(cx, cy + 8, cx, cy + 34)
            cape_grad.setColorAt(0.0, QColor(147, 197, 253, 220))
            cape_grad.setColorAt(1.0, QColor(37, 99, 235, 180))
            painter.setBrush(QBrush(cape_grad))
            painter.setPen(Qt.PenStyle.NoPen)
            cape_p = QPolygonF([
                QPointF(cx - 16, cy + 10),
                QPointF(cx + 16, cy + 10),
                QPointF(cx + 22, cy + 34),
                QPointF(cx - 22, cy + 34)
            ])
            painter.drawPolygon(cape_p)

    def _draw_tail(self, painter: QPainter, cx: float, cy: float, model: MascotModel):
        if self.tail == "none":
            return
        sway = math.sin(model.pulse_phase * 1.8) * 6.0
        path = QPainterPath()
        start = QPointF(cx - 10, cy + 24)
        if self.tail in ("cat", "fox"):
            ctrl = QPointF(cx - 26 + sway, cy + 16)
            tip = QPointF(cx - 22 + sway, cy + 2)
            path.moveTo(start)
            path.quadTo(ctrl, tip)
            thick = 6.0 if self.tail == "fox" else 3.2
            painter.setPen(QPen(self.body_col1, thick, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
            # Tip glow
            painter.setBrush(QBrush(self.accent_col))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(tip.x() - 3, tip.y() - 3, 6, 6))
        elif self.tail == "dragon":
            ctrl = QPointF(cx - 28 + sway, cy + 18)
            tip = QPointF(cx - 26 + sway, cy + 8)
            path.moveTo(start)
            path.quadTo(ctrl, tip)
            painter.setPen(QPen(self.body_col1, 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
            # Spade tip
            painter.setBrush(QBrush(self.accent_col))
            painter.setPen(Qt.PenStyle.NoPen)
            spade = QPolygonF([QPointF(tip.x(), tip.y() - 4), QPointF(tip.x() - 4, tip.y() + 4), QPointF(tip.x() + 4, tip.y() + 4)])
            painter.drawPolygon(spade)
        elif self.tail == "phoenix":
            for i, offset in enumerate([-4.0, 0.0, 4.0]):
                p = QPainterPath()
                t_tip = QPointF(cx - 20 + sway + offset, cy + 10 + i * 4)
                p.moveTo(start)
                p.quadTo(QPointF(cx - 28 + sway, cy + 26), t_tip)
                painter.setPen(QPen(self.accent_col, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawPath(p)

    def _draw_ears(self, painter: QPainter, cx: float, cy: float, model: MascotModel):
        if self.ears == "none":
            return
        wiggle = model.ear_wiggle_angle

        if self.ears in ("cat", "fox"):
            ear_w = 12.0 if self.ears == "cat" else 15.0
            ear_h = 16.0 if self.ears == "cat" else 20.0
            for is_left, base_x in [(True, cx - 18), (False, cx + 18)]:
                painter.save()
                painter.translate(base_x, cy - 14)
                painter.rotate(wiggle if is_left else -wiggle)
                sign = -1.0 if is_left else 1.0
                outer = QPolygonF([QPointF(0, 0), QPointF(sign * ear_w, -ear_h), QPointF(sign * (ear_w * 1.2), 2)])
                painter.setBrush(QBrush(self.body_col1))
                painter.setPen(QPen(self.outline_col, 1.4))
                painter.drawPolygon(outer)
                inner = QPolygonF([QPointF(sign * 2, -1), QPointF(sign * (ear_w * 0.8), -ear_h + 5), QPointF(sign * (ear_w * 0.9), 0)])
                painter.setBrush(QBrush(self.accent_col))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPolygon(inner)
                painter.restore()

        elif self.ears == "bolts":
            painter.setBrush(QBrush(self.body_col2))
            painter.setPen(QPen(self.accent_col, 1.2))
            painter.drawRect(QRectF(cx - 30, cy - 6, 6, 12))
            painter.drawRect(QRectF(cx + 24, cy - 6, 6, 12))

        elif self.ears == "horns":
            painter.setBrush(QBrush(self.accent_col))
            painter.setPen(Qt.PenStyle.NoPen)
            h_l = QPolygonF([QPointF(cx - 16, cy - 14), QPointF(cx - 26, cy - 28), QPointF(cx - 10, cy - 16)])
            h_r = QPolygonF([QPointF(cx + 16, cy - 14), QPointF(cx + 26, cy - 28), QPointF(cx + 10, cy - 16)])
            painter.drawPolygon(h_l)
            painter.drawPolygon(h_r)

        elif self.ears == "crest":
            painter.setBrush(QBrush(self.accent_col))
            painter.setPen(Qt.PenStyle.NoPen)
            crest = QPolygonF([QPointF(cx - 4, cy - 18), QPointF(cx, cy - 32), QPointF(cx + 4, cy - 18)])
            painter.drawPolygon(crest)

    def _draw_body(self, painter: QPainter, cx: float, cy: float, model: MascotModel):
        body_grad = QLinearGradient(cx, cy - 24, cx, cy + 24)
        body_grad.setColorAt(0.0, self.body_col1)
        body_grad.setColorAt(1.0, self.body_col2)
        painter.setBrush(QBrush(body_grad))
        pen = QPen(self.outline_col, 1.8)
        painter.setPen(pen)

        if self.shape == "round":
            head_rect = QRectF(cx - 26, cy - 20, 52, 44)
            painter.drawRoundedRect(head_rect, 22.0, 20.0)
        elif self.shape == "square":
            rect = QRectF(cx - 25, cy - 20, 50, 42)
            painter.drawRoundedRect(rect, 10.0, 10.0)
        elif self.shape == "blob":
            # Soft bun shape
            path = QPainterPath()
            path.moveTo(cx - 26, cy + 12)
            path.quadTo(cx - 28, cy - 16, cx, cy - 20)
            path.quadTo(cx + 28, cy - 16, cx + 26, cy + 12)
            path.quadTo(cx, cy + 22, cx - 26, cy + 12)
            painter.drawPath(path)
        elif self.shape == "slime":
            # Wobbly jelly droplet
            wobble = math.sin(model.pulse_phase * 2.2) * 2.0
            path = QPainterPath()
            path.moveTo(cx - 26, cy + 16)
            path.cubicTo(cx - 30 + wobble, cy - 6, cx - 14, cy - 24, cx, cy - 24)
            path.cubicTo(cx + 14, cy - 24, cx + 30 - wobble, cy - 6, cx + 26, cy + 16)
            path.quadTo(cx, cy + 22, cx - 26, cy + 16)
            painter.drawPath(path)

    def _draw_fg_extras(self, painter: QPainter, cx: float, cy: float, model: MascotModel):
        if "bun_swirl" in self.extras:
            painter.setPen(QPen(QColor("#D9B48A"), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            p = QPainterPath()
            p.moveTo(cx - 4, cy - 18)
            p.quadTo(cx, cy - 22, cx + 4, cy - 18)
            painter.drawPath(p)

        if "comb" in self.extras:
            painter.setBrush(QBrush(QColor(239, 68, 68)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(cx - 5, cy - 27, 10, 8))

        if "beak" in self.extras:
            painter.setBrush(QBrush(QColor(249, 115, 22)))
            painter.setPen(Qt.PenStyle.NoPen)
            beak = QPolygonF([QPointF(cx - 4, cy + 2), QPointF(cx + 4, cy + 2), QPointF(cx, cy + 7)])
            painter.drawPolygon(beak)

        if "antenna" in self.extras:
            painter.setPen(QPen(self.accent_col, 2.0))
            painter.drawLine(QPointF(cx, cy - 20), QPointF(cx, cy - 30))
            painter.setBrush(QBrush(self.accent_col))
            painter.drawEllipse(QRectF(cx - 3, cy - 34, 6, 6))

        if "ice_crown" in self.extras:
            painter.setBrush(QBrush(QColor(224, 242, 254, 240)))
            painter.setPen(QPen(QColor(59, 130, 246), 1.2))
            crown = QPolygonF([
                QPointF(cx - 14, cy - 18),
                QPointF(cx - 14, cy - 27),
                QPointF(cx - 7, cy - 22),
                QPointF(cx, cy - 30),
                QPointF(cx + 7, cy - 22),
                QPointF(cx + 14, cy - 27),
                QPointF(cx + 14, cy - 18)
            ])
            painter.drawPolygon(crown)

        if "visor" in self.extras:
            painter.setBrush(QBrush(QColor(56, 189, 248, 230)))
            painter.setPen(QPen(QColor(251, 191, 36), 1.2))
            painter.drawRoundedRect(QRectF(cx - 20, cy - 8, 40, 10), 4.0, 4.0)

        if "shine" in self.extras:
            painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(cx - 18, cy - 16, 7, 4))

        if "whiskers" in self.extras:
            painter.setPen(QPen(self.accent_col, 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            # Left whiskers
            painter.drawLine(QPointF(cx - 16, cy + 4), QPointF(cx - 28, cy + 2))
            painter.drawLine(QPointF(cx - 16, cy + 8), QPointF(cx - 28, cy + 9))
            # Right whiskers
            painter.drawLine(QPointF(cx + 16, cy + 4), QPointF(cx + 28, cy + 2))
            painter.drawLine(QPointF(cx + 16, cy + 8), QPointF(cx + 28, cy + 9))

    def _draw_cheeks(self, painter: QPainter, cx: float, cy: float, model: MascotModel):
        alpha = 80 if model.is_sleeping else 130
        col = QColor(255, 120, 150, alpha)
        painter.setBrush(QBrush(col))
        painter.setPen(Qt.PenStyle.NoPen)
        r_w = 9.0 if "big_blush" in self.extras else 6.5
        painter.drawEllipse(QRectF(cx - 18, cy + 4, r_w, 4.0))
        painter.drawEllipse(QRectF(cx + 18 - r_w, cy + 4, r_w, 4.0))

    def _draw_eyes(self, painter: QPainter, cx: float, cy: float, model: MascotModel, is_dizzy: bool, is_waking_up: bool):
        blink = math.sin(model.blink_phase) if model.is_blinking else 0.0
        eye_y = cy - 2
        spacing = 13.0
        left = QPointF(cx - spacing, eye_y)
        right = QPointF(cx + spacing, eye_y)

        if "led_eyes" in self.extras:
            # Matrix / digital eye bar
            painter.setBrush(QBrush(self.accent_col))
            painter.setPen(Qt.PenStyle.NoPen)
            if model.is_sleeping or blink > 0.8:
                painter.drawRect(QRectF(left.x() - 5, left.y(), 10, 2))
                painter.drawRect(QRectF(right.x() - 5, right.y(), 10, 2))
            else:
                painter.drawRoundedRect(QRectF(left.x() - 5, left.y() - 4, 10, 8), 2, 2)
                painter.drawRoundedRect(QRectF(right.x() - 5, right.y() - 4, 10, 8), 2, 2)
            return

        if "visor" in self.extras:
            return  # Visor covers eyes

        if model.is_sleeping:
            pen = QPen(self.eye_col if self.is_light_body else self.accent_col, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for pt in [left, right]:
                p = QPainterPath()
                p.moveTo(pt.x() - 5, pt.y())
                p.quadTo(pt.x(), pt.y() + 3.5, pt.x() + 5, pt.y())
                painter.drawPath(p)
            return

        if is_dizzy or is_waking_up or model.voice_state == VoiceState.SPEAKING:
            # Happy smiling eyes '^ ^'
            pen = QPen(self.eye_col if self.is_light_body else self.accent_col, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for pt in [left, right]:
                p = QPainterPath()
                p.moveTo(pt.x() - 5, pt.y() + 2)
                p.quadTo(pt.x(), pt.y() - 4, pt.x() + 5, pt.y() + 2)
                painter.drawPath(p)
            return

        # Anime Eyes with pupil & glint
        eye_w = 9.5
        eye_h = max(1.2, 13.0 * (1.0 - blink))
        if blink > 0.85:
            painter.setPen(QPen(self.eye_col, 2.0))
            painter.drawLine(QPointF(left.x() - 4, left.y()), QPointF(left.x() + 4, left.y()))
            painter.drawLine(QPointF(right.x() - 4, right.y()), QPointF(right.x() + 4, right.y()))
            return

        for pt in [left, right]:
            rect = QRectF(pt.x() - eye_w / 2.0, pt.y() - eye_h / 2.0, eye_w, eye_h)
            painter.setBrush(QBrush(QColor(15, 23, 42) if self.is_light_body else QColor(6, 10, 18)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(rect)

            # Iris
            iris_col = self.eye_col
            painter.setBrush(QBrush(iris_col))
            iris_rect = QRectF(pt.x() - eye_w * 0.35 + model.current_eye_x * 0.5,
                               pt.y() - eye_h * 0.35 + model.current_eye_y * 0.5,
                               eye_w * 0.7, eye_h * 0.7)
            painter.drawEllipse(iris_rect)

            # White sparkle
            if blink < 0.6:
                painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
                painter.drawEllipse(QRectF(pt.x() - 2.0, pt.y() - eye_h * 0.3, 2.5, 2.8))

    def _draw_mouth(self, painter: QPainter, cx: float, cy: float, model: MascotModel, is_dizzy: bool, is_waking_up: bool):
        if "beak" in self.extras:
            return
        pen = QPen(self.eye_col if self.is_light_body else self.accent_col, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        mouth_y = cy + 8
        if model.voice_state == VoiceState.SPEAKING:
            h = 2.0 + model.mouth_open * 4.0
            painter.setBrush(QBrush(QColor(255, 100, 140, 220)))
            painter.drawEllipse(QRectF(cx - 3.0, mouth_y - 1.0, 6.0, h))
        elif is_dizzy or is_waking_up:
            p = QPainterPath()
            p.moveTo(cx - 4, mouth_y - 1)
            p.quadTo(cx, mouth_y + 3, cx + 4, mouth_y - 1)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(p)
        else:
            # Cute small smile
            p = QPainterPath()
            p.moveTo(cx - 3.5, mouth_y)
            p.quadTo(cx - 1.8, mouth_y + 1.8, cx, mouth_y + 0.5)
            p.quadTo(cx + 1.8, mouth_y + 1.8, cx + 3.5, mouth_y)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(p)

    def _draw_limbs(self, painter: QPainter, cx: float, cy: float, model: MascotModel):
        if self.shape in ("slime", "blob"):
            return  # Slime and bao don't have detached feet
        paw_col = self.body_col2
        painter.setBrush(QBrush(paw_col))
        painter.setPen(QPen(self.outline_col, 1.0))

        # Feet
        foot_sway = 0.0 if model.is_sleeping else math.sin(model.pulse_phase * 1.8) * 1.4
        painter.drawRoundedRect(QRectF(cx - 14, cy + 20 + foot_sway, 9, 6), 3, 3)
        painter.drawRoundedRect(QRectF(cx + 5, cy + 20 - foot_sway, 9, 6), 3, 3)

    def _draw_particles(self, painter: QPainter, cx: float, cy: float, model: MascotModel):
        if "orbit_stars" in self.extras:
            painter.setPen(Qt.PenStyle.NoPen)
            for i in range(3):
                angle = model.pulse_phase * 1.5 + (i * 2.094)
                star_x = cx + math.cos(angle) * 38
                star_y = cy + math.sin(angle) * 18
                painter.setBrush(QBrush(QColor(253, 224, 71, 220)))
                painter.drawEllipse(QRectF(star_x - 2, star_y - 2, 4, 4))

        if model.is_sleeping and model.zzz_particles:
            font = QFont("Arial", 11, QFont.Weight.Bold)
            painter.setFont(font)
            for p in model.zzz_particles:
                alpha = max(0, min(255, int(p.get("alpha", 200))))
                painter.setPen(QColor(self.accent_col.red(), self.accent_col.green(), self.accent_col.blue(), alpha))
                painter.drawText(QPointF(p["x"], p["y"]), p.get("char", "z"))
