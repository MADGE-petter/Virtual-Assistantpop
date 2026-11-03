"""Pop Renderer - Original Cyber-Pet Desktop Mascot vector renderer."""

import math
import time
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QLinearGradient,
    QPainterPath, QPolygonF, QFont
)
from model.voice_state_model import VoiceState
from view.ui.mascot.characters.base_character_renderer import BaseCharacterRenderer
from view.ui.mascot.mascot_model import MascotModel


class PopRenderer(BaseCharacterRenderer):
    """Pure vector rendering for the original Chibi Cyber-Pet 'Pop'."""

    def paint(self, painter: QPainter, width: int, height: int, model: MascotModel):
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

        if model.cling_edge in ("left", "right", "bottom"):
            float_speed = 0.4 if model.is_sleeping else 0.8
            float_y = math.sin(model.pulse_phase) * float_speed
        else:
            float_speed = 1.0 if model.is_sleeping else 2.2
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

        if model.voice_state == VoiceState.READY:
            neon_primary = QColor(0, 255, 170)
            neon_secondary = QColor(0, 142, 255)
        elif model.voice_state == VoiceState.LISTENING:
            neon_primary = QColor(0, 229, 255)
            neon_secondary = QColor(56, 189, 248)
        elif model.voice_state == VoiceState.THINKING:
            neon_primary = QColor(245, 158, 11)
            neon_secondary = QColor(249, 115, 22)
        elif model.voice_state == VoiceState.SPEAKING:
            neon_primary = QColor(168, 85, 247)
            neon_secondary = QColor(236, 72, 153)
        else:
            neon_primary = QColor(100, 116, 139)
            neon_secondary = QColor(51, 65, 85)

        if model.is_sleeping:
            neon_primary = QColor(
                int(neon_primary.red() * 0.75),
                int(neon_primary.green() * 0.75 + 30),
                int(neon_primary.blue() * 0.85 + 30)
            )

        if model.is_sleeping:
            head_nod = math.sin(model.pulse_phase * 0.9) * 3.0
        elif model.is_drowsy:
            bob = (math.sin(model.pulse_phase * 1.1) + 1.0) / 2.0
            head_nod = bob * 4.2 * model.drowsy_ratio
        else:
            head_nod = 0.0

        head_cx = cx
        head_cy = cy - 8.0 + head_nod

        self._draw_cyber_tail(painter, head_cx, head_cy, neon_primary, model)

        ear_wiggle = model.ear_wiggle_angle
        if model.is_dragging:
            ear_wiggle = -8.0
        elif is_waking_up:
            ear_wiggle = 5.0 + math.sin(model.pulse_phase * 4.0) * 3.0

        self._draw_cyber_ear(painter, head_cx - 20, head_cy - 16, is_left=True, wiggle=ear_wiggle, primary=neon_primary)
        self._draw_cyber_ear(painter, head_cx + 20, head_cy - 16, is_left=False, wiggle=-ear_wiggle, primary=neon_primary)

        if model.cling_edge == "left":
            foot_l_x = head_cx - 16
            foot_l_y = head_cy + 30
            foot_r_x = head_cx - 2
            foot_r_y = head_cy + 34
            self._draw_cyber_foot(painter, foot_l_x, foot_l_y, neon_primary)
            self._draw_cyber_foot(painter, foot_r_x, foot_r_y, neon_primary)
            self._draw_magnetic_grip(painter, foot_l_x - 3.5, foot_l_y, neon_primary, model.pulse_phase)
        elif model.cling_edge == "right":
            foot_r_x = head_cx + 16
            foot_r_y = head_cy + 30
            foot_l_x = head_cx + 2
            foot_l_y = head_cy + 34
            self._draw_cyber_foot(painter, foot_l_x, foot_l_y, neon_primary)
            self._draw_cyber_foot(painter, foot_r_x, foot_r_y, neon_primary)
            self._draw_magnetic_grip(painter, foot_r_x + 3.5, foot_r_y, neon_primary, model.pulse_phase)
        elif model.cling_edge == "top":
            foot_sway = math.sin(model.pulse_phase * 1.8) * 1.8
            self._draw_cyber_foot(painter, head_cx - 9 + foot_sway, head_cy + 33, neon_primary)
            self._draw_cyber_foot(painter, head_cx + 9 - foot_sway, head_cy + 33, neon_primary)
        elif model.cling_edge == "bottom":
            self._draw_cyber_foot(painter, head_cx - 12, head_cy + 33, neon_primary)
            self._draw_cyber_foot(painter, head_cx + 12, head_cy + 33, neon_primary)
        else:
            leg_l_sway = 0.0
            leg_r_sway = 0.0
            if not model.is_sleeping:
                leg_l_sway = math.sin(model.pulse_phase * 1.8) * 1.6
                leg_r_sway = math.sin(model.pulse_phase * 1.8 + math.pi) * 1.6
            if model.is_dragging:
                leg_l_sway = 2.5
                leg_r_sway = 2.5
            self._draw_cyber_foot(painter, head_cx - 10, head_cy + 33 + leg_l_sway, neon_primary)
            self._draw_cyber_foot(painter, head_cx + 10, head_cy + 33 + leg_r_sway, neon_primary)

        self._draw_cyber_body(painter, head_cx, head_cy, neon_primary, neon_secondary, model.pulse_phase)

        head_w = 54.0
        head_h = 44.0
        head_rect = QRectF(head_cx - head_w / 2.0, head_cy - head_h / 2.0, head_w, head_h)
        helmet_grad = QLinearGradient(head_cx, head_rect.top(), head_cx, head_rect.bottom())
        helmet_grad.setColorAt(0.0, QColor(24, 34, 54))
        helmet_grad.setColorAt(0.6, QColor(14, 20, 34))
        helmet_grad.setColorAt(1.0, QColor(8, 12, 22))
        painter.setBrush(QBrush(helmet_grad))
        painter.setPen(QPen(QColor(neon_primary.red(), neon_primary.green(), neon_primary.blue(), 180), 1.8))
        painter.drawRoundedRect(head_rect, 22.0, 20.0)

        highlight_path = QPainterPath()
        highlight_path.moveTo(head_cx - 18, head_cy - 15)
        highlight_path.quadTo(head_cx, head_cy - 21, head_cx + 18, head_cy - 15)
        painter.setPen(QPen(QColor(255, 255, 255, 75), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(highlight_path)

        blush_color = QColor(255, 95, 140, 70 if model.is_sleeping else 110)
        painter.setBrush(QBrush(blush_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(head_cx - 20, head_cy + 4, 8.0, 4.0))
        painter.drawEllipse(QRectF(head_cx + 12, head_cy + 4, 8.0, 4.0))

        blink_ratio = math.sin(model.blink_phase) if model.is_blinking else 0.0
        eye_spacing = 13.0
        left_eye_center = QPointF(head_cx - eye_spacing, head_cy - 2)
        right_eye_center = QPointF(head_cx + eye_spacing, head_cy - 2)

        if model.is_dragging:
            self._draw_shocked_eyes(painter, left_eye_center, right_eye_center, neon_primary)
        elif is_dizzy or is_waking_up or model.voice_state == VoiceState.SPEAKING:
            self._draw_happy_eyes(painter, left_eye_center, right_eye_center, neon_primary)
        elif model.is_sleeping:
            if model.peek_eye == 1:
                self._draw_anime_eye(painter, left_eye_center, 0.0, neon_primary, model)
                self._draw_sleeping_eye(painter, right_eye_center, neon_primary)
            elif model.peek_eye == 2:
                self._draw_sleeping_eye(painter, left_eye_center, neon_primary)
                self._draw_anime_eye(painter, right_eye_center, 0.0, neon_primary, model)
            else:
                self._draw_sleeping_eye(painter, left_eye_center, neon_primary)
                self._draw_sleeping_eye(painter, right_eye_center, neon_primary)
        elif model.is_drowsy:
            self._draw_drowsy_eye(painter, left_eye_center, model.drowsy_ratio, neon_primary, model)
            self._draw_drowsy_eye(painter, right_eye_center, model.drowsy_ratio, neon_primary, model)
        else:
            self._draw_anime_eye(painter, left_eye_center, blink_ratio, neon_primary, model)
            self._draw_anime_eye(painter, right_eye_center, blink_ratio, neon_primary, model)

        self._draw_mouth(painter, head_cx, head_cy + 8, is_dizzy or is_waking_up, neon_primary, model)
        self._draw_cyber_arms(painter, head_cx, head_cy, neon_primary, is_waking_up, model)

        if model.is_sleeping and model.zzz_particles:
            self._draw_zzz_particles(painter, neon_primary, model.zzz_particles)

        painter.restore()

    def _draw_magnetic_grip(self, painter: QPainter, gx: float, gy: float, primary: QColor, pulse_phase: float):
        pulse = (math.sin(pulse_phase * 3.5) + 1.0) / 2.0
        alpha = int(140 + pulse * 110)
        glow_color = QColor(primary.red(), primary.green(), primary.blue(), int(alpha * 0.45))
        painter.setBrush(QBrush(glow_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(gx - 3.5, gy - 3.5, 7.0, 7.0))
        spark_color = QColor(primary.red(), primary.green(), primary.blue(), alpha)
        painter.setBrush(QBrush(spark_color))
        painter.drawEllipse(QRectF(gx - 2.0, gy - 2.0, 4.0, 4.0))

    def _draw_cyber_tail(self, painter: QPainter, head_cx: float, head_cy: float, primary: QColor, model: MascotModel):
        sway_speed = 0.8 if model.is_sleeping else 1.8
        sway_amp = 3.5 if model.is_sleeping else 8.0
        tail_sway = math.sin(model.pulse_phase * sway_speed) * sway_amp

        if model.cling_edge == "left":
            start_pt = QPointF(head_cx + 4, head_cy + 26)
            ctrl1 = QPointF(head_cx + 16, head_cy + 30 + tail_sway * 0.4)
            ctrl2 = QPointF(head_cx + 24 + tail_sway * 0.7, head_cy + 18)
            tip_pt = QPointF(head_cx + 18 + tail_sway, head_cy + 6)
        elif model.cling_edge == "right":
            start_pt = QPointF(head_cx - 4, head_cy + 26)
            ctrl1 = QPointF(head_cx - 16, head_cy + 30 + tail_sway * 0.4)
            ctrl2 = QPointF(head_cx - 24 + tail_sway * 0.7, head_cy + 18)
            tip_pt = QPointF(head_cx - 18 + tail_sway, head_cy + 6)
        elif model.cling_edge == "top":
            start_pt = QPointF(head_cx, head_cy + 28)
            ctrl1 = QPointF(head_cx + tail_sway * 0.5, head_cy + 36)
            ctrl2 = QPointF(head_cx + tail_sway * 0.9, head_cy + 42)
            tip_pt = QPointF(head_cx + tail_sway * 1.2, head_cy + 48)
        else:
            start_pt = QPointF(head_cx - 8, head_cy + 28)
            ctrl1 = QPointF(head_cx - 20 + tail_sway * 0.7, head_cy + 30)
            ctrl2 = QPointF(head_cx - 28 + tail_sway * 1.3, head_cy + 18)
            tip_pt = QPointF(head_cx - 22 + tail_sway, head_cy + 8)

        tail_path = QPainterPath()
        tail_path.moveTo(start_pt)
        tail_path.cubicTo(ctrl1, ctrl2, tip_pt)

        painter.setPen(QPen(QColor(18, 26, 42), 3.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(tail_path)
        painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 180), 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawPath(tail_path)
        painter.setBrush(QBrush(primary))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(tip_pt.x() - 3.2, tip_pt.y() - 3.2, 6.4, 6.4))

    def _draw_cyber_body(self, painter: QPainter, head_cx: float, head_cy: float, primary: QColor, secondary: QColor, pulse_phase: float):
        torso_w = 34.0
        torso_h = 24.0
        torso_rect = QRectF(head_cx - torso_w / 2.0, head_cy + 14.0, torso_w, torso_h)
        body_grad = QLinearGradient(head_cx, torso_rect.top(), head_cx, torso_rect.bottom())
        body_grad.setColorAt(0.0, QColor(20, 28, 46))
        body_grad.setColorAt(1.0, QColor(10, 16, 28))
        painter.setBrush(QBrush(body_grad))
        painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 140), 1.5))
        painter.drawRoundedRect(torso_rect, 11.0, 10.0)

        core_cx = head_cx
        core_cy = head_cy + 24.0
        core_r = 3.8
        core_pulse = (math.sin(pulse_phase * 2.0) + 1.0) / 2.0
        core_alpha = int(120 + core_pulse * 130)
        core_glow = QColor(primary.red(), primary.green(), primary.blue(), int(core_alpha * 0.4))
        painter.setBrush(QBrush(core_glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(core_cx - core_r - 2.5, core_cy - core_r - 2.5, (core_r + 2.5) * 2, (core_r + 2.5) * 2))
        core_color = QColor(primary.red(), primary.green(), primary.blue(), core_alpha)
        painter.setBrush(QBrush(core_color))
        painter.drawEllipse(QRectF(core_cx - core_r, core_cy - core_r, core_r * 2, core_r * 2))

    def _draw_cyber_foot(self, painter: QPainter, foot_cx: float, foot_cy: float, primary: QColor):
        foot_w = 11.0
        foot_h = 8.0
        foot_rect = QRectF(foot_cx - foot_w / 2.0, foot_cy - foot_h / 2.0, foot_w, foot_h)
        painter.setBrush(QBrush(QColor(16, 24, 38)))
        painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 160), 1.2))
        painter.drawRoundedRect(foot_rect, 4.0, 4.0)

    def _draw_cyber_arms(self, painter: QPainter, head_cx: float, head_cy: float, primary: QColor, is_waking_up: bool, model: MascotModel):
        paw_color = QColor(18, 26, 42)
        paw_border = QPen(primary, 1.2)
        painter.setBrush(QBrush(paw_color))
        painter.setPen(paw_border)
        paw_w = 9.5
        paw_h = 7.5

        if model.is_dragging:
            l_y = head_cy + 2.0 + math.sin(model.pulse_phase * 6.0) * 3.0
            r_y = head_cy + 2.0 - math.sin(model.pulse_phase * 6.0) * 3.0
            painter.drawEllipse(QRectF(head_cx - 24 - paw_w / 2.0, l_y - paw_h / 2.0, paw_w, paw_h))
            painter.drawEllipse(QRectF(head_cx + 24 - paw_w / 2.0, r_y - paw_h / 2.0, paw_w, paw_h))
        elif is_waking_up:
            painter.drawEllipse(QRectF(head_cx - 21 - paw_w / 2.0, head_cy + 10 - paw_h / 2.0, paw_w, paw_h))
            painter.drawEllipse(QRectF(head_cx + 21 - paw_w / 2.0, head_cy + 10 - paw_h / 2.0, paw_w, paw_h))
        elif model.cling_edge == "left":
            l_grip_x = head_cx - 28
            l_grip_y = head_cy + 8
            r_grip_x = head_cx - 22
            r_grip_y = head_cy + 22
            painter.drawEllipse(QRectF(l_grip_x - paw_w / 2.0, l_grip_y - paw_h / 2.0, paw_w, paw_h))
            painter.drawEllipse(QRectF(r_grip_x - paw_w / 2.0, r_grip_y - paw_h / 2.0, paw_w, paw_h))
            self._draw_magnetic_grip(painter, l_grip_x - 3.5, l_grip_y, primary, model.pulse_phase)
            self._draw_magnetic_grip(painter, r_grip_x - 3.5, r_grip_y, primary, model.pulse_phase)
        elif model.cling_edge == "right":
            r_grip_x = head_cx + 28
            r_grip_y = head_cy + 8
            l_grip_x = head_cx + 22
            l_grip_y = head_cy + 22
            painter.drawEllipse(QRectF(r_grip_x - paw_w / 2.0, r_grip_y - paw_h / 2.0, paw_w, paw_h))
            painter.drawEllipse(QRectF(l_grip_x - paw_w / 2.0, l_grip_y - paw_h / 2.0, paw_w, paw_h))
            self._draw_magnetic_grip(painter, r_grip_x + 3.5, r_grip_y, primary, model.pulse_phase)
            self._draw_magnetic_grip(painter, l_grip_x + 3.5, l_grip_y, primary, model.pulse_phase)
        elif model.cling_edge == "top":
            painter.drawEllipse(QRectF(head_cx - 15 - paw_w / 2.0, head_cy - 18 - paw_h / 2.0, paw_w, paw_h))
            painter.drawEllipse(QRectF(head_cx + 15 - paw_w / 2.0, head_cy - 18 - paw_h / 2.0, paw_w, paw_h))
            self._draw_magnetic_grip(painter, head_cx - 15, head_cy - 20, primary, model.pulse_phase)
            self._draw_magnetic_grip(painter, head_cx + 15, head_cy - 20, primary, model.pulse_phase)
        else:
            float_paw = math.sin(model.pulse_phase * 1.5) * 1.2
            painter.drawEllipse(QRectF(head_cx - 17 - paw_w / 2.0, head_cy + 22 + float_paw - paw_h / 2.0, paw_w, paw_h))
            painter.drawEllipse(QRectF(head_cx + 17 - paw_w / 2.0, head_cy + 22 - float_paw - paw_h / 2.0, paw_w, paw_h))

    def _draw_cyber_ear(self, painter: QPainter, base_x: float, base_y: float, is_left: bool, wiggle: float, primary: QColor):
        painter.save()
        painter.translate(base_x, base_y)
        painter.rotate(wiggle if is_left else -wiggle)
        ear_w = 14.0
        ear_h = 18.0
        sign = -1.0 if is_left else 1.0
        outer_ear = QPolygonF([QPointF(0, 0), QPointF(sign * (ear_w * 0.9), -ear_h), QPointF(sign * (ear_w * 1.2), 2)])
        painter.setBrush(QBrush(QColor(18, 25, 40)))
        painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 190), 1.4))
        painter.drawPolygon(outer_ear)
        inner_ear = QPolygonF([QPointF(sign * 2.5, -1), QPointF(sign * (ear_w * 0.85), -ear_h + 4.5), QPointF(sign * (ear_w * 0.95), 0)])
        c_inner = QColor(primary)
        c_inner.setAlpha(170)
        painter.setBrush(QBrush(c_inner))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(inner_ear)
        painter.restore()

    def _draw_anime_eye(self, painter: QPainter, center: QPointF, blink_ratio: float, primary: QColor, model: MascotModel):
        eye_w = 11.5
        eye_h = max(1.2, 16.0 * (1.0 - blink_ratio))
        if blink_ratio > 0.85:
            painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 230), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(QPointF(center.x() - 5, center.y()), QPointF(center.x() + 5, center.y()))
            return
        eye_rect = QRectF(center.x() - eye_w / 2.0, center.y() - eye_h / 2.0, eye_w, eye_h)
        painter.setBrush(QBrush(QColor(6, 10, 18)))
        painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 140), 1.0))
        painter.drawEllipse(eye_rect)

        pupil_w = 8.5
        pupil_h = max(1.0, 12.0 * (1.0 - blink_ratio))
        pupil_cx = center.x() + model.current_eye_x
        pupil_cy = center.y() + (model.current_eye_y * (1.0 - blink_ratio))
        pupil_grad = QLinearGradient(pupil_cx, pupil_cy - pupil_h / 2.0, pupil_cx, pupil_cy + pupil_h / 2.0)
        pupil_grad.setColorAt(0.0, QColor(primary.red(), primary.green(), primary.blue(), 255))
        pupil_grad.setColorAt(0.7, QColor(0, 142, 255, 230))
        pupil_grad.setColorAt(1.0, QColor(2, 40, 80, 200))
        painter.setBrush(QBrush(pupil_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        pupil_rect = QRectF(pupil_cx - pupil_w / 2.0, pupil_cy - pupil_h / 2.0, pupil_w, pupil_h)
        painter.drawEllipse(pupil_rect)
        if blink_ratio < 0.6:
            painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
            painter.drawEllipse(QRectF(pupil_cx - 2.8, pupil_cy - 4.2, 3.2, 3.8))

    def _draw_drowsy_eye(self, painter: QPainter, center: QPointF, drowsy_ratio: float, primary: QColor, model: MascotModel):
        eye_w = 11.5
        eye_h = 16.0
        eye_rect = QRectF(center.x() - eye_w / 2.0, center.y() - eye_h / 2.0, eye_w, eye_h)
        painter.setBrush(QBrush(QColor(6, 10, 18)))
        painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 130), 1.0))
        painter.drawEllipse(eye_rect)
        drop_fraction = 0.35 + 0.45 * drowsy_ratio
        lid_drop = eye_h * drop_fraction
        lid_y = (center.y() - eye_h / 2.0) + lid_drop
        painter.save()
        painter.setClipRect(eye_rect)
        painter.setBrush(QBrush(QColor(18, 26, 42)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(QRectF(center.x() - eye_w, center.y() - eye_h, eye_w * 2, (eye_h / 2.0) + lid_drop))
        painter.restore()
        painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 230), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(center.x() - 6.0, lid_y), QPointF(center.x() + 6.0, lid_y + 0.6))

    def _draw_sleeping_eye(self, painter: QPainter, center: QPointF, primary: QColor):
        pen = QPen(QColor(primary.red(), primary.green(), primary.blue(), 230), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        path.moveTo(center.x() - 6.0, center.y() - 1.0)
        path.quadTo(center.x(), center.y() + 3.5, center.x() + 6.0, center.y() - 1.0)
        painter.drawPath(path)

    def _draw_shocked_eyes(self, painter: QPainter, left: QPointF, right: QPointF, color: QColor):
        pen = QPen(color, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        p_left = QPainterPath()
        p_left.moveTo(left.x() - 4.5, left.y() - 4.5)
        p_left.lineTo(left.x() + 2.5, left.y())
        p_left.lineTo(left.x() - 4.5, left.y() + 4.5)
        painter.drawPath(p_left)
        p_right = QPainterPath()
        p_right.moveTo(right.x() + 4.5, right.y() - 4.5)
        p_right.lineTo(right.x() - 2.5, right.y())
        p_right.lineTo(right.x() + 4.5, right.y() + 4.5)
        painter.drawPath(p_right)

    def _draw_happy_eyes(self, painter: QPainter, left: QPointF, right: QPointF, color: QColor):
        pen = QPen(color, 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for pt in [left, right]:
            path = QPainterPath()
            path.moveTo(pt.x() - 5.5, pt.y() + 1.5)
            path.quadTo(pt.x(), pt.y() - 5.0, pt.x() + 5.5, pt.y() + 1.5)
            painter.drawPath(path)

    def _draw_mouth(self, painter: QPainter, cx: float, cy: float, is_happy: bool, color: QColor, model: MascotModel):
        pen = QPen(color, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        if model.is_dragging:
            painter.setBrush(QBrush(QColor(10, 16, 28)))
            painter.drawEllipse(QRectF(cx - 3.0, cy - 1.5, 6.0, 5.5))
        elif is_happy:
            path = QPainterPath()
            path.moveTo(cx - 4.5, cy - 1.0)
            path.quadTo(cx, cy + 3.0, cx + 4.5, cy - 1.0)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
        elif model.voice_state == VoiceState.SPEAKING:
            h = 2.0 + model.mouth_open * 4.5
            painter.setBrush(QBrush(QColor(255, 95, 140, 180)))
            painter.drawEllipse(QRectF(cx - 3.5, cy - 1.0, 7.0, h))
        elif model.is_sleeping:
            path = QPainterPath()
            path.moveTo(cx - 3.0, cy)
            path.quadTo(cx, cy + 2.0, cx + 3.0, cy)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
        else:
            path = QPainterPath()
            path.moveTo(cx - 4.0, cy - 0.5)
            path.quadTo(cx - 2.0, cy + 2.0, cx, cy + 0.5)
            path.quadTo(cx + 2.0, cy + 2.0, cx + 4.0, cy - 0.5)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

    def _draw_zzz_particles(self, painter: QPainter, primary: QColor, particles: list):
        painter.save()
        font = QFont("Arial", 11, QFont.Weight.Bold)
        painter.setFont(font)
        for p in particles:
            alpha = max(0, min(255, int(p["alpha"])))
            z_color = QColor(primary.red(), primary.green(), primary.blue(), alpha)
            painter.setPen(z_color)
            painter.drawText(QPointF(p["x"], p["y"]), p["char"])
        painter.restore()
