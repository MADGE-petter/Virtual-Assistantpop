"""Fox Girl Renderer - Custom vector renderer for 'Hồ Ly Bạch Tâm' (White Fox Kemonomimi Girl).

Features:
- Human-fox hybrid (kemonomimi) with long platinum white hair, fluffy white fox ears & tail with pastel pink tips.
- Oversized white sweater reaching mid-thigh with a glowing red/pink heart emblem on the chest and tiny hearts along the hem.
- Free-floating sleep: Morphs with a magical sakura/smoke poof (~0.6s) into a curled-up snowy white fox ball with a heart-patterned back and tail wrapped over its nose.
- Edge/Corner clinging sleep: Sleeps in humanoid form nodding off with an expanding/contracting snot bubble ('bong bóng mũi') that bursts with droplet splashes and startled wake-up expression when clicked!
"""

import math
import time
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QLinearGradient, QRadialGradient,
    QPainterPath, QPolygonF, QFont
)
from model.voice_state_model import VoiceState
from view.ui.mascot.characters.base_character_renderer import BaseCharacterRenderer
from view.ui.mascot.mascot_model import MascotModel


class FoxGirlRenderer(BaseCharacterRenderer):
    """Pure procedural vector renderer for the White Fox Kemonomimi character."""

    def paint(self, painter: QPainter, width: int, height: int, model: MascotModel) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        base_cx = width / 2.0
        cling_dx = 0.0
        cling_dy = 0.0
        cling_rot = 0.0

        if model.cling_edge == "left":
            cling_dx = -10.0 * model.cling_ratio
            cling_rot = -6.0 * model.cling_ratio
        elif model.cling_edge == "right":
            cling_dx = 10.0 * model.cling_ratio
            cling_rot = 6.0 * model.cling_ratio
        elif model.cling_edge == "top":
            cling_dy = -12.0 * model.cling_ratio
            pendulum = math.sin(model.pulse_phase * 1.3) * 4.0
            cling_rot = pendulum * model.cling_ratio
        elif model.cling_edge == "bottom":
            cling_dy = 8.0 * model.cling_ratio

        float_speed = 0.45 if model.is_sleeping else 1.6
        float_y = math.sin(model.pulse_phase) * float_speed

        cx = base_cx + cling_dx
        cy = (height / 2.0) + float_y + cling_dy

        painter.save()
        if abs(cling_rot) > 0.01:
            painter.translate(cx, cy)
            painter.rotate(cling_rot)
            painter.translate(-cx, -cy)

        now = time.time()
        is_clinging = model.cling_edge is not None

        # Free-floating sleep -> morph into curled white fox!
        if model.is_sleeping and not is_clinging:
            sleep_elapsed = max(0.0, now - model.sleep_enter_time) if model.sleep_enter_time > 0 else 10.0
            morph_duration = 0.65
            if sleep_elapsed < morph_duration:
                progress = sleep_elapsed / morph_duration
                # First half: shrink humanoid, Second half: grow curled fox + poof smoke
                if progress < 0.45:
                    scale = 1.0 - (progress / 0.45) * 0.45
                    painter.save()
                    painter.translate(cx, cy)
                    painter.scale(scale, scale)
                    painter.translate(-cx, -cy)
                    self._paint_humanoid(painter, cx, cy, model, now)
                    painter.restore()
                else:
                    fox_prog = (progress - 0.45) / 0.55
                    scale = 0.55 + fox_prog * 0.45
                    painter.save()
                    painter.translate(cx, cy + 6.0)
                    painter.scale(scale, scale)
                    painter.translate(-cx, -(cy + 6.0))
                    self._paint_curled_fox(painter, cx, cy + 6.0, model, now)
                    painter.restore()
                self._draw_morph_poof(painter, cx, cy + 2.0, progress)
            else:
                self._paint_curled_fox(painter, cx, cy + 6.0, model, now)
                if model.zzz_particles:
                    self._draw_zzz_particles(painter, model.zzz_particles)
            painter.restore()
            return

        # Waking up from free-floating curled fox -> brief poof transition back to humanoid
        is_just_woke = (now < model.wake_up_until) and not is_clinging and (model.wake_up_until - now > 0.75)
        self._paint_humanoid(painter, cx, cy, model, now)
        if is_just_woke:
            wake_prog = 1.0 - ((model.wake_up_until - now - 0.75) / 0.45)
            self._draw_morph_poof(painter, cx, cy, max(0.0, min(1.0, wake_prog)))

        painter.restore()

    # ============================================================
    # 1. HUMANOID KEMONOMIMI FORM (IDLE, TALK, DROWSY, CORNER SLEEP)
    # ============================================================

    def _paint_humanoid(self, painter: QPainter, cx: float, cy: float, model: MascotModel, now: float):
        is_dizzy = model.is_dragging or (now < model.dizzy_end_time)
        is_waking_up = now < model.wake_up_until
        is_popping_bubble = now < model.bubble_pop_until

        # Head nod when sleeping at edge/corner or drowsy
        if model.is_sleeping:
            # Deep rhythmic nodding forward/downward when sleeping at corner/edge
            head_nod = 4.5 + math.sin(model.pulse_phase * 1.1) * 2.5
            head_tilt = math.sin(model.pulse_phase * 0.55) * 4.5
        elif model.is_drowsy:
            bob = (math.sin(model.pulse_phase * 1.2) + 1.0) / 2.0
            head_nod = bob * 4.0 * model.drowsy_ratio
            head_tilt = 0.0
        else:
            head_nod = 0.0
            head_tilt = 0.0

        head_cx = cx
        head_cy = cy - 13.0 + head_nod
        body_cy = cy + 12.0

        # 0. Soft Mythic Heart Aura glow behind character
        self._draw_mythic_aura(painter, cx, cy, model.pulse_phase)

        # 1. Fluffy White Fox Tail (behind body & hair)
        self._draw_fox_tail(painter, cx, body_cy, model)

        # 2. Back Long Platinum White Hair
        self._draw_back_hair(painter, head_cx, head_cy, model.pulse_phase)

        # 3. Bare Chibi Legs & Thighs (mid-thigh down)
        self._draw_legs(painter, cx, body_cy, model)

        # 4. White Oversized Sweater reaching mid-thigh with Heart Pattern
        self._draw_heart_sweater(painter, cx, body_cy, model)

        # 5. Sweater Sleeves / Paws
        self._draw_arms(painter, cx, body_cy, model, is_waking_up or is_popping_bubble)

        # 6. Head & Face (with optional sleepy tilt)
        painter.save()
        if abs(head_tilt) > 0.05:
            painter.translate(head_cx, head_cy)
            painter.rotate(head_tilt)
            painter.translate(-head_cx, -head_cy)

        # Fox Ears
        ear_wiggle = model.ear_wiggle_angle
        if model.is_dragging:
            ear_wiggle = -10.0
        elif is_popping_bubble or is_waking_up:
            ear_wiggle = 7.0 + math.sin(now * 28.0) * 4.0
        self._draw_fox_ears(painter, head_cx, head_cy, ear_wiggle)

        # Humanoid Chibi Face Skin
        self._draw_face_base(painter, head_cx, head_cy, model)

        # Eyes
        self._draw_eyes(painter, head_cx, head_cy, model, is_dizzy, is_waking_up, is_popping_bubble)

        # Cute Fox Nose & Mouth
        self._draw_mouth(painter, head_cx, head_cy + 7.5, model, is_dizzy, is_waking_up, is_popping_bubble)

        # Front Hair Bangs & Side Locks with Heart Hairclips
        self._draw_front_hair(painter, head_cx, head_cy, model.pulse_phase)

        # 7. Corner/Edge Sleep Snot Bubble ('Bong bóng mũi') OR Pop Splash Effect
        if model.is_sleeping and model.cling_edge is not None:
            self._draw_snot_bubble(painter, head_cx + 3.5, head_cy + 5.5, model.pulse_phase)
        elif is_popping_bubble or model.bubble_pop_particles:
            self._draw_bubble_pop_effect(painter, head_cx + 3.5, head_cy + 5.5, model, now)

        painter.restore()

        # 8. Floating zZz when sleeping (toned down if snot bubble is active so bubble stands out)
        if model.is_sleeping and model.zzz_particles:
            self._draw_zzz_particles(painter, model.zzz_particles)

    # ============================================================
    # 2. CURLED WHITE FOX FORM (SLEEPING IN FREE SPACE)
    # ============================================================

    def _paint_curled_fox(self, painter: QPainter, cx: float, cy: float, model: MascotModel, now: float):
        breath = math.sin(model.pulse_phase * 1.4)
        scale_x = 1.0 + breath * 0.028
        scale_y = 1.0 - breath * 0.022

        painter.save()
        painter.translate(cx, cy)
        painter.scale(scale_x, scale_y)
        painter.translate(-cx, -cy)

        # Soft warm shadow cushion underneath
        shadow_grad = QRadialGradient(cx, cy + 18, 36)
        shadow_grad.setColorAt(0.0, QColor(244, 63, 94, 55))
        shadow_grad.setColorAt(0.6, QColor(148, 163, 184, 35))
        shadow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(shadow_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - 36, cy + 8, 72, 20))

        # 1. Curled Fox Body (Snowy White Doughnut/Oval)
        body_rect = QRectF(cx - 30, cy - 14, 60, 36)
        fox_grad = QLinearGradient(cx, body_rect.top(), cx, body_rect.bottom())
        fox_grad.setColorAt(0.0, QColor("#FFFFFF"))
        fox_grad.setColorAt(0.7, QColor("#FFF1F2"))
        fox_grad.setColorAt(1.0, QColor("#FFE4E6"))
        painter.setBrush(QBrush(fox_grad))
        painter.setPen(QPen(QColor("#F43F5E"), 1.5))
        painter.drawEllipse(body_rect)

        # Cute heart-patterned white sweater cape / mark on the fox's back
        self._draw_heart_shape(painter, cx + 10, cy - 3, 5.5, QColor("#F43F5E"))
        self._draw_heart_shape(painter, cx + 18, cy + 3, 3.2, QColor("#FB7185"))

        # 2. Sleeping Fox Head (tucked on the left side)
        head_x = cx - 12
        head_y = cy - 4

        # Back Fox Ear (folded back sleepily)
        ear_twitch = math.sin(model.pulse_phase * 0.9) * 2.5
        self._draw_single_fox_ear(painter, head_x - 8, head_y - 10, is_left=True, angle=-22 + ear_twitch, scale=0.85)

        # Head circle
        head_rect = QRectF(head_x - 16, head_y - 13, 32, 26)
        painter.setBrush(QBrush(fox_grad))
        painter.setPen(QPen(QColor("#FDA4AF"), 1.4))
        painter.drawEllipse(head_rect)

        # Front Fox Ear (folded slightly)
        self._draw_single_fox_ear(painter, head_x + 8, head_y - 10, is_left=False, angle=18 - ear_twitch, scale=0.85)

        # Closed Peaceful Fox Eyes & Blush
        painter.setBrush(QBrush(QColor(251, 113, 133, 95)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(head_x - 12, head_y + 2, 6.0, 3.2))
        painter.drawEllipse(QRectF(head_x + 4, head_y + 2, 6.0, 3.2))

        eye_pen = QPen(QColor("#881337"), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(eye_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for ex in (head_x - 7, head_x + 5):
            ep = QPainterPath()
            ep.moveTo(ex - 3.5, head_y - 1.0)
            ep.quadTo(ex, head_y + 2.2, ex + 3.5, head_y - 1.0)
            painter.drawPath(ep)

        # Little pink fox nose peeking out
        painter.setBrush(QBrush(QColor("#F43F5E")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(head_x - 2.5, head_y + 4.0, 3.5, 2.5))

        # 3. Big Fluffy Fox Tail curling around the front and over the paws/nose
        tail_path = QPainterPath()
        tail_path.moveTo(cx + 24, cy + 6)
        tail_path.cubicTo(cx + 32, cy + 22, cx + 4, cy + 26, cx - 16, cy + 16)
        tail_path.cubicTo(cx - 28, cy + 11, cx - 24, cy + 1, cx - 8, cy + 6)
        tail_path.cubicTo(cx + 6, cy + 10, cx + 18, cy + 12, cx + 24, cy + 6)

        tail_grad = QLinearGradient(cx - 24, cy + 6, cx + 26, cy + 18)
        tail_grad.setColorAt(0.0, QColor("#FDA4AF"))  # Soft pink-tinted tip
        tail_grad.setColorAt(0.35, QColor("#FFFFFF"))
        tail_grad.setColorAt(1.0, QColor("#FFF1F2"))
        painter.setBrush(QBrush(tail_grad))
        painter.setPen(QPen(QColor("#F43F5E"), 1.4))
        painter.drawPath(tail_path)

        painter.restore()

    # ============================================================
    # HUMANOID SUB-COMPONENTS
    # ============================================================

    def _draw_mythic_aura(self, painter: QPainter, cx: float, cy: float, pulse_phase: float):
        pulse = (math.sin(pulse_phase * 1.6) + 1.0) / 2.0
        grad = QRadialGradient(cx, cy + 2, 46 + pulse * 5)
        grad.setColorAt(0.0, QColor(255, 228, 230, int(75 + pulse * 35)))
        grad.setColorAt(0.6, QColor(251, 113, 133, int(35 + pulse * 20)))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - 50, cy - 48, 100, 100))

    def _draw_fox_tail(self, painter: QPainter, cx: float, body_cy: float, model: MascotModel):
        sway_speed = 0.9 if model.is_sleeping else 2.0
        sway_amp = 3.0 if model.is_sleeping else 7.5
        sway = math.sin(model.pulse_phase * sway_speed) * sway_amp

        # Large fluffy fox tail sweeping out to the side
        sign = -1.0 if model.cling_edge == "right" else 1.0
        start_x = cx + sign * 6.0
        start_y = body_cy + 10.0

        tail_path = QPainterPath()
        tail_path.moveTo(start_x, start_y)
        tail_path.cubicTo(
            start_x + sign * 24.0, start_y + 6.0 + sway * 0.4,
            start_x + sign * (38.0 + sway * 0.5), start_y - 10.0 + sway,
            start_x + sign * (30.0 + sway), start_y - 24.0 + sway * 0.8
        )
        tail_path.cubicTo(
            start_x + sign * (18.0 + sway * 0.6), start_y - 20.0 + sway * 0.5,
            start_x + sign * 12.0, start_y - 6.0,
            start_x, start_y
        )

        tail_grad = QLinearGradient(start_x, start_y, start_x + sign * 32.0, start_y - 24.0)
        tail_grad.setColorAt(0.0, QColor("#FFF1F2"))
        tail_grad.setColorAt(0.65, QColor("#FFFFFF"))
        tail_grad.setColorAt(1.0, QColor("#FDA4AF"))  # Pastel pink tip

        painter.setBrush(QBrush(tail_grad))
        painter.setPen(QPen(QColor("#FB7185"), 1.4))
        painter.drawPath(tail_path)

    def _draw_back_hair(self, painter: QPainter, head_cx: float, head_cy: float, pulse_phase: float):
        sway = math.sin(pulse_phase * 1.4) * 2.0
        hair_path = QPainterPath()
        hair_path.moveTo(head_cx - 24, head_cy - 4)
        hair_path.cubicTo(
            head_cx - 32 - sway * 0.5, head_cy + 16,
            head_cx - 28 - sway, head_cy + 34,
            head_cx - 18 - sway * 0.6, head_cy + 38
        )
        hair_path.lineTo(head_cx + 18 - sway * 0.6, head_cy + 38)
        hair_path.cubicTo(
            head_cx + 28 - sway, head_cy + 34,
            head_cx + 32 - sway * 0.5, head_cy + 16,
            head_cx + 24, head_cy - 4
        )
        hair_path.closeSubpath()

        hair_grad = QLinearGradient(head_cx, head_cy - 10, head_cx, head_cy + 38)
        hair_grad.setColorAt(0.0, QColor("#FFFFFF"))
        hair_grad.setColorAt(0.7, QColor("#F8FAFC"))
        hair_grad.setColorAt(1.0, QColor("#FFE4E6"))

        painter.setBrush(QBrush(hair_grad))
        painter.setPen(QPen(QColor("#CBD5E1"), 1.3))
        painter.drawPath(hair_path)

    def _draw_legs(self, painter: QPainter, cx: float, body_cy: float, model: MascotModel):
        # Bare thighs & chibi legs sticking out below the mid-thigh sweater
        skin_color = QColor("#FFF0E6")
        skin_border = QPen(QColor("#F43F5E"), 1.1)

        leg_sway = 0.0 if model.is_sleeping else math.sin(model.pulse_phase * 1.8) * 1.4
        left_x = cx - 7.5
        right_x = cx + 7.5
        top_y = body_cy + 13.0

        # Thighs/legs
        painter.setBrush(QBrush(skin_color))
        painter.setPen(skin_border)
        painter.drawRoundedRect(QRectF(left_x - 3.5, top_y, 7.0, 12.5 + leg_sway), 3.2, 3.2)
        painter.drawRoundedRect(QRectF(right_x - 3.5, top_y, 7.0, 12.5 - leg_sway), 3.2, 3.2)

        # Cute white ankle socks / shoes with tiny pink ribbon
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawRoundedRect(QRectF(left_x - 3.8, top_y + 8.5 + leg_sway, 7.6, 4.5), 2.2, 2.2)
        painter.drawRoundedRect(QRectF(right_x - 3.8, top_y + 8.5 - leg_sway, 7.6, 4.5), 2.2, 2.2)

    def _draw_heart_sweater(self, painter: QPainter, cx: float, body_cy: float, model: MascotModel):
        # Oversized white dress-sweater reaching mid-thigh (covers hip & upper half of thighs)
        top_w = 24.0
        bot_w = 34.0
        top_y = body_cy - 9.0
        bot_y = body_cy + 16.5  # Reaches down to mid-thigh!

        sweater_path = QPainterPath()
        sweater_path.moveTo(cx - top_w / 2.0, top_y)
        sweater_path.cubicTo(
            cx - bot_w / 2.0 - 2.0, body_cy + 4.0,
            cx - bot_w / 2.0, bot_y - 2.0,
            cx - bot_w / 2.0 + 2.0, bot_y
        )
        # Scalloped / soft curved hem at mid-thigh
        sweater_path.quadTo(cx, bot_y + 2.5, cx + bot_w / 2.0 - 2.0, bot_y)
        sweater_path.cubicTo(
            cx + bot_w / 2.0, bot_y - 2.0,
            cx + bot_w / 2.0 + 2.0, body_cy + 4.0,
            cx + top_w / 2.0, top_y
        )
        sweater_path.closeSubpath()

        sw_grad = QLinearGradient(cx, top_y, cx, bot_y)
        sw_grad.setColorAt(0.0, QColor("#FFFFFF"))
        sw_grad.setColorAt(0.8, QColor("#FFF9FA"))
        sw_grad.setColorAt(1.0, QColor("#FFE4E6"))

        painter.setBrush(QBrush(sw_grad))
        painter.setPen(QPen(QColor("#F43F5E"), 1.5))
        painter.drawPath(sweater_path)

        # Cute collar detail
        collar_pen = QPen(QColor("#FDA4AF"), 1.2)
        painter.setPen(collar_pen)
        painter.drawArc(QRectF(cx - 7.0, top_y - 1.5, 14.0, 5.0), 180 * 16, 180 * 16)

        # Center Glowing Heart Emblem on the chest
        heart_pulse = 1.0 + math.sin(model.pulse_phase * 2.2) * 0.08
        self._draw_heart_shape(painter, cx, body_cy + 2.5, 6.2 * heart_pulse, QColor("#F43F5E"), glow=True)

        # Small decorative hearts along the mid-thigh hem
        self._draw_heart_shape(painter, cx - 9.5, bot_y - 3.2, 2.4, QColor("#FB7185"))
        self._draw_heart_shape(painter, cx + 9.5, bot_y - 3.2, 2.4, QColor("#FB7185"))

    def _draw_arms(self, painter: QPainter, cx: float, body_cy: float, model: MascotModel, is_startled: bool):
        # Oversized long white sleeves covering hands ("paw sleeves")
        sleeve_brush = QBrush(QColor("#FFFFFF"))
        sleeve_pen = QPen(QColor("#F43F5E"), 1.3)
        painter.setBrush(sleeve_brush)
        painter.setPen(sleeve_pen)

        if model.is_dragging or is_startled:
            # Raised startled sleeves
            wave = math.sin(model.pulse_phase * 6.0) * 2.5
            painter.drawEllipse(QRectF(cx - 23, body_cy - 8 + wave, 9.0, 12.0))
            painter.drawEllipse(QRectF(cx + 14, body_cy - 8 - wave, 9.0, 12.0))
        else:
            sway = 0.0 if model.is_sleeping else math.sin(model.pulse_phase * 1.5) * 1.2
            painter.drawRoundedRect(QRectF(cx - 20.5, body_cy - 4.0 + sway, 8.0, 15.0), 4.0, 4.0)
            painter.drawRoundedRect(QRectF(cx + 12.5, body_cy - 4.0 - sway, 8.0, 15.0), 4.0, 4.0)

    def _draw_fox_ears(self, painter: QPainter, head_cx: float, head_cy: float, wiggle: float):
        self._draw_single_fox_ear(painter, head_cx - 17, head_cy - 16, is_left=True, angle=wiggle, scale=1.0)
        self._draw_single_fox_ear(painter, head_cx + 17, head_cy - 16, is_left=False, angle=-wiggle, scale=1.0)

    def _draw_single_fox_ear(self, painter: QPainter, base_x: float, base_y: float, is_left: bool, angle: float, scale: float = 1.0):
        painter.save()
        painter.translate(base_x, base_y)
        painter.rotate(angle)
        if abs(scale - 1.0) > 0.01:
            painter.scale(scale, scale)

        sign = -1.0 if is_left else 1.0
        ear_w = 15.0
        ear_h = 22.0

        # Outer white fox ear
        outer = QPolygonF([
            QPointF(-sign * 2.0, 2.0),
            QPointF(sign * (ear_w * 0.85), -ear_h),
            QPointF(sign * (ear_w * 1.15), 4.0)
        ])
        ear_grad = QLinearGradient(0, 2, sign * ear_w * 0.85, -ear_h)
        ear_grad.setColorAt(0.0, QColor("#FFFFFF"))
        ear_grad.setColorAt(0.75, QColor("#FFF1F2"))
        ear_grad.setColorAt(1.0, QColor("#FDA4AF"))  # Pastel pink ear tip

        painter.setBrush(QBrush(ear_grad))
        painter.setPen(QPen(QColor("#F43F5E"), 1.4))
        painter.drawPolygon(outer)

        # Inner pink fluff
        inner = QPolygonF([
            QPointF(sign * 1.0, 1.0),
            QPointF(sign * (ear_w * 0.78), -ear_h + 5.0),
            QPointF(sign * (ear_w * 0.92), 2.5)
        ])
        painter.setBrush(QBrush(QColor(251, 113, 133, 165)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(inner)

        painter.restore()

    def _draw_face_base(self, painter: QPainter, head_cx: float, head_cy: float, model: MascotModel):
        head_w = 50.0
        head_h = 41.0
        head_rect = QRectF(head_cx - head_w / 2.0, head_cy - head_h / 2.0, head_w, head_h)

        skin_grad = QLinearGradient(head_cx, head_rect.top(), head_cx, head_rect.bottom())
        skin_grad.setColorAt(0.0, QColor("#FFF9F5"))
        skin_grad.setColorAt(1.0, QColor("#FFE8DC"))

        painter.setBrush(QBrush(skin_grad))
        painter.setPen(QPen(QColor("#F43F5E"), 1.5))
        painter.drawRoundedRect(head_rect, 21.0, 19.0)

        # Rosy Cheeks
        blush_alpha = 135 if not model.is_sleeping else 95
        painter.setBrush(QBrush(QColor(251, 113, 133, blush_alpha)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(head_cx - 19.5, head_cy + 3.5, 8.0, 4.2))
        painter.drawEllipse(QRectF(head_cx + 11.5, head_cy + 3.5, 8.0, 4.2))

    def _draw_front_hair(self, painter: QPainter, head_cx: float, head_cy: float, pulse_phase: float):
        # Fluffy white anime bangs + side locks framing the face
        hair_grad = QLinearGradient(head_cx, head_cy - 22, head_cx, head_cy + 15)
        hair_grad.setColorAt(0.0, QColor("#FFFFFF"))
        hair_grad.setColorAt(1.0, QColor("#FFF1F2"))

        painter.setBrush(QBrush(hair_grad))
        painter.setPen(QPen(QColor("#FDA4AF"), 1.25))

        bangs = QPainterPath()
        top_y = head_cy - 21.0
        bangs.moveTo(head_cx - 25.0, head_cy - 4.0)
        bangs.quadTo(head_cx - 24.0, top_y, head_cx, top_y - 1.0)
        bangs.quadTo(head_cx + 24.0, top_y, head_cx + 25.0, head_cy - 4.0)

        # Wavy bangs across forehead
        bangs.quadTo(head_cx + 18.0, head_cy - 11.0, head_cx + 11.0, head_cy - 5.0)
        bangs.quadTo(head_cx + 5.0, head_cy - 12.0, head_cx, head_cy - 4.5)
        bangs.quadTo(head_cx - 5.0, head_cy - 12.0, head_cx - 11.0, head_cy - 5.0)
        bangs.quadTo(head_cx - 18.0, head_cy - 11.0, head_cx - 25.0, head_cy - 4.0)
        painter.drawPath(bangs)

        # Side locks hanging down past cheeks
        sway = math.sin(pulse_phase * 1.5) * 1.2
        for sign in (-1.0, 1.0):
            lock = QPainterPath()
            bx = head_cx + sign * 22.0
            lock.moveTo(bx, head_cy - 8.0)
            lock.quadTo(bx + sign * 5.0, head_cy + 6.0, bx + sign * (2.0 + sway), head_cy + 20.0)
            lock.quadTo(bx - sign * 2.0, head_cy + 10.0, bx - sign * 3.0, head_cy - 4.0)
            lock.closeSubpath()
            painter.drawPath(lock)

        # Tiny Red Heart Hairclip on the left bang
        self._draw_heart_shape(painter, head_cx - 16.5, head_cy - 9.5, 3.2, QColor("#F43F5E"))

    def _draw_eyes(self, painter: QPainter, head_cx: float, head_cy: float, model: MascotModel,
                   is_dizzy: bool, is_waking_up: bool, is_popping_bubble: bool):
        blink_ratio = math.sin(model.blink_phase) if model.is_blinking else 0.0
        eye_spacing = 12.0
        left_c = QPointF(head_cx - eye_spacing, head_cy - 0.5)
        right_c = QPointF(head_cx + eye_spacing, head_cy - 0.5)
        ruby_col = QColor("#E11D48")

        # Startled / Shocked eyes right when snot bubble pops or being dragged!
        if model.is_dragging or is_popping_bubble:
            for pt in (left_c, right_c):
                painter.setBrush(QBrush(QColor("#FFFFFF")))
                painter.setPen(QPen(QColor("#881337"), 1.6))
                painter.drawEllipse(QRectF(pt.x() - 5.5, pt.y() - 6.5, 11.0, 13.0))
                # Shrunk startled ruby pupil
                painter.setBrush(QBrush(ruby_col))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(pt.x() - 2.5, pt.y() - 2.5, 5.0, 5.0))
                painter.setBrush(QBrush(QColor("#FFFFFF")))
                painter.drawEllipse(QRectF(pt.x() - 1.2, pt.y() - 1.8, 1.8, 1.8))
            return

        if is_dizzy or is_waking_up or model.voice_state == VoiceState.SPEAKING:
            # Happy smiling arches '^ ^'
            pen = QPen(QColor("#9F1239"), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for pt in (left_c, right_c):
                p = QPainterPath()
                p.moveTo(pt.x() - 5.0, pt.y() + 1.5)
                p.quadTo(pt.x(), pt.y() - 4.5, pt.x() + 5.0, pt.y() + 1.5)
                painter.drawPath(p)
            return

        if model.is_sleeping:
            # Sleeping closed eyelashes
            pen = QPen(QColor("#9F1239"), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for pt in (left_c, right_c):
                p = QPainterPath()
                p.moveTo(pt.x() - 5.0, pt.y() - 0.5)
                p.quadTo(pt.x(), pt.y() + 3.5, pt.x() + 5.0, pt.y() - 0.5)
                painter.drawPath(p)
            return

        if model.is_drowsy:
            # Half-closed sleepy eyes
            for pt in (left_c, right_c):
                self._draw_ruby_anime_eye(painter, pt, 0.55 * model.drowsy_ratio, model)
            return

        for pt in (left_c, right_c):
            self._draw_ruby_anime_eye(painter, pt, blink_ratio, model)

    def _draw_ruby_anime_eye(self, painter: QPainter, center: QPointF, blink_ratio: float, model: MascotModel):
        eye_w = 10.5
        eye_h = max(1.2, 13.5 * (1.0 - blink_ratio))
        if blink_ratio > 0.85:
            painter.setPen(QPen(QColor("#9F1239"), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(QPointF(center.x() - 4.8, center.y()), QPointF(center.x() + 4.8, center.y()))
            return

        eye_rect = QRectF(center.x() - eye_w / 2.0, center.y() - eye_h / 2.0, eye_w, eye_h)
        painter.setBrush(QBrush(QColor("#4C0519")))
        painter.setPen(QPen(QColor("#881337"), 1.2))
        painter.drawEllipse(eye_rect)

        # Ruby/Pink Gradient Iris
        pupil_w = 7.8
        pupil_h = max(1.0, 10.2 * (1.0 - blink_ratio))
        px = center.x() + model.current_eye_x * 0.75
        py = center.y() + model.current_eye_y * 0.75 * (1.0 - blink_ratio)

        iris_grad = QLinearGradient(px, py - pupil_h / 2.0, px, py + pupil_h / 2.0)
        iris_grad.setColorAt(0.0, QColor("#BE123C"))
        iris_grad.setColorAt(0.55, QColor("#F43F5E"))
        iris_grad.setColorAt(1.0, QColor("#FDA4AF"))
        painter.setBrush(QBrush(iris_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(px - pupil_w / 2.0, py - pupil_h / 2.0, pupil_w, pupil_h))

        # Eye highlights (top sparkle + tiny heart highlight)
        if blink_ratio < 0.6:
            painter.setBrush(QBrush(QColor(255, 255, 255, 245)))
            painter.drawEllipse(QRectF(px - 2.6, py - 3.6, 2.8, 3.2))
            painter.drawEllipse(QRectF(px + 1.0, py + 1.0, 1.5, 1.5))

    def _draw_mouth(self, painter: QPainter, cx: float, cy: float, model: MascotModel,
                    is_dizzy: bool, is_waking_up: bool, is_popping_bubble: bool):
        # Cute tiny fox nose dot above mouth
        painter.setBrush(QBrush(QColor("#FB7185")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - 1.2, cy - 4.2, 2.4, 1.8))

        pen = QPen(QColor("#9F1239"), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        if is_popping_bubble or model.is_dragging:
            # Startled 'o' mouth when bubble pops!
            painter.setBrush(QBrush(QColor("#FB7185")))
            painter.drawEllipse(QRectF(cx - 2.8, cy - 1.0, 5.6, 5.2))
        elif model.voice_state == VoiceState.SPEAKING:
            h = 2.0 + model.mouth_open * 4.2
            painter.setBrush(QBrush(QColor("#F43F5E")))
            painter.drawEllipse(QRectF(cx - 3.2, cy - 1.0, 6.4, h))
        elif model.is_sleeping:
            # Soft sleepy 'o' breath mouth
            painter.setBrush(QBrush(QColor(251, 113, 133, 160)))
            r = 1.8 + math.sin(model.pulse_phase * 1.1) * 0.5
            painter.drawEllipse(QRectF(cx - r, cy - 0.5, r * 2, r * 1.8))
        else:
            # Cute ':3' cat/fox ω smile
            path = QPainterPath()
            path.moveTo(cx - 4.0, cy - 0.3)
            path.quadTo(cx - 2.0, cy + 2.2, cx, cy + 0.3)
            path.quadTo(cx + 2.0, cy + 2.2, cx + 4.0, cy - 0.3)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

    # ============================================================
    # 3. SNOT BUBBLE ('BONG BÓNG MŨI') & BURST ANIMATION
    # ============================================================

    def _draw_snot_bubble(self, painter: QPainter, nx: float, ny: float, pulse_phase: float):
        """Draws an expanding & contracting translucent sleep bubble attached to the nose."""
        breath = (math.sin(pulse_phase * 1.2) + 1.0) / 2.0  # 0.0 -> 1.0
        radius = 5.5 + breath * 6.5  # Expands from 5.5px to 12.0px

        # Bubble center shifts slightly outward as it inflates
        bx = nx + radius * 0.78
        by = ny - radius * 0.25

        bubble_grad = QRadialGradient(bx - radius * 0.3, by - radius * 0.3, radius * 1.2)
        bubble_grad.setColorAt(0.0, QColor(255, 255, 255, 210))
        bubble_grad.setColorAt(0.4, QColor(186, 230, 253, 155))
        bubble_grad.setColorAt(0.85, QColor(56, 189, 248, 130))
        bubble_grad.setColorAt(1.0, QColor(244, 114, 182, 165))

        painter.save()
        painter.setBrush(QBrush(bubble_grad))
        painter.setPen(QPen(QColor(125, 211, 252, 220), 1.3))
        painter.drawEllipse(QRectF(bx - radius, by - radius, radius * 2.0, radius * 2.0))

        # Glossy curved reflection highlight on bubble
        painter.setBrush(QBrush(QColor(255, 255, 255, 230)))
        painter.setPen(Qt.PenStyle.NoPen)
        hl_r = radius * 0.28
        painter.drawEllipse(QRectF(bx - radius * 0.48, by - radius * 0.52, hl_r * 1.3, hl_r * 0.9))
        painter.restore()

    def _draw_bubble_pop_effect(self, painter: QPainter, nx: float, ny: float, model: MascotModel, now: float):
        """Draws bursting ring, water droplets and 'Póc!' text when the user clicks to pop the bubble."""
        painter.save()
        cx = nx + 8.0
        cy = ny - 2.0

        # Expanding shockwave ring
        rem = model.bubble_pop_until - now
        if rem > 0:
            prog = 1.0 - (rem / 0.65)
            ring_r = 6.0 + prog * 18.0
            alpha = max(0, min(255, int(240 * (1.0 - prog))))
            painter.setPen(QPen(QColor(56, 189, 248, alpha), 2.0, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(cx - ring_r, cy - ring_r, ring_r * 2.0, ring_r * 2.0))

            # Cute "Póc!" text indicator
            font = QFont("Arial", 9, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor(244, 63, 94, alpha))
            painter.drawText(QPointF(cx + 6.0, cy - 8.0 - prog * 8.0), "Póc!")

        # Flying droplets
        painter.setPen(Qt.PenStyle.NoPen)
        for bp in model.bubble_pop_particles:
            alpha = max(0, min(255, int(bp.get("alpha", 200))))
            painter.setBrush(QBrush(QColor(125, 211, 252, alpha)))
            r = bp.get("r", 2.2)
            painter.drawEllipse(QRectF(cx + bp["dx"] - r, cy + bp["dy"] - r, r * 2.0, r * 2.0))

        painter.restore()

    # ============================================================
    # 4. SHARED HELPERS (HEARTS, MORPH POOF, ZZZ)
    # ============================================================

    def _draw_heart_shape(self, painter: QPainter, cx: float, cy: float, size: float, color: QColor, glow: bool = False):
        painter.save()
        if glow:
            glow_grad = QRadialGradient(cx, cy, size * 1.8)
            glow_grad.setColorAt(0.0, QColor(color.red(), color.green(), color.blue(), 110))
            glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(glow_grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(cx - size * 1.8, cy - size * 1.8, size * 3.6, size * 3.6))

        path = QPainterPath()
        path.moveTo(cx, cy + size * 0.75)
        path.cubicTo(cx - size * 1.2, cy + size * 0.1, cx - size * 0.9, cy - size * 0.85, cx, cy - size * 0.3)
        path.cubicTo(cx + size * 0.9, cy - size * 0.85, cx + size * 1.2, cy + size * 0.1, cx, cy + size * 0.75)

        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(255, 255, 255, 190), 0.8))
        painter.drawPath(path)
        painter.restore()

    def _draw_morph_poof(self, painter: QPainter, cx: float, cy: float, progress: float):
        """Draws a cute white/pink smoke cloud & heart burst during humanoid <-> fox transformation."""
        painter.save()
        alpha = int(math.sin(progress * math.pi) * 235)
        alpha = max(0, min(255, alpha))
        spread = 8.0 + progress * 24.0

        puff_offsets = [
            (0.0, 0.0, 18.0),
            (-0.8, -0.4, 14.0),
            (0.8, -0.4, 14.0),
            (-0.6, 0.6, 13.0),
            (0.6, 0.6, 13.0),
        ]
        painter.setPen(QPen(QColor(251, 113, 133, int(alpha * 0.6)), 1.2))
        painter.setBrush(QBrush(QColor(255, 241, 242, alpha)))
        for ox, oy, r in puff_offsets:
            px = cx + ox * spread
            py = cy + oy * spread
            painter.drawEllipse(QRectF(px - r, py - r, r * 2.0, r * 2.0))

        # Floating mini hearts in the poof
        if alpha > 40:
            self._draw_heart_shape(painter, cx - spread * 0.9, cy - spread * 0.8, 3.5, QColor(244, 63, 94, alpha))
            self._draw_heart_shape(painter, cx + spread * 0.9, cy - spread * 0.7, 3.0, QColor(251, 113, 133, alpha))
        painter.restore()

    def _draw_zzz_particles(self, painter: QPainter, particles: list):
        painter.save()
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)
        for p in particles:
            alpha = max(0, min(255, int(p.get("alpha", 200))))
            painter.setPen(QColor(244, 63, 94, alpha))
            painter.drawText(QPointF(p["x"], p["y"]), p.get("char", "z"))
        painter.restore()

