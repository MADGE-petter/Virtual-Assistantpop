"""Chubby Meme Renderer - Authentic Cube/Mochi Dumpling Renderer for 'Phoebe Chupi' & 'Nono (Phruonuo)'.

Updated Proportions & Details:
- Pure Cube / Squishy Mochi Block silhouette: NO legs/feet! The entire character is a single chunky, rounded-square cube-dumpling sitting low and flat on the ground, with ONLY 2 cute round circle hands ('2 tay hình tròn').
- Phoebe Chupi ('phoebe'):
  * Signature oversized White & Royal-Blue Acolyte Hat (wide brim, gold trim, golden four-point star emblem on the front, and side blue/white ribbons).
  * Blonde hair with side braids framing her ultra-wide squishy cheeks, large expressive blue-violet/amber-gold gradient eyes positioned low on the face, cute ':3' smile, and white/blue/gold collar trim along the bottom of the cube.
- Nono / Phruonuo ('nono'):
  * Single chunky cube-dumpling silhouette with ash-silver twin-tails tied high on the sides with black/crimson gothic ribbons.
  * Blooming Red Spider Lily (Hoa Bỉ Ngạn Đỏ) tucked on the upper left of her head.
  * Signature white cross-stitched medical eyepatch covering her right eye (viewer's left) and a big expressive crimson-ruby eye on the right (with a cute tear drop when dragged), plus gothic crimson/black frill trim at the bottom of the cube.
- Full 45 FPS Animations:
  * Bouncy Cube Physics (squash & stretch), 360° cursor gaze tracking, blinking, floating 'Chupi~!' / 'Nono~!' speech tags, flat pancake sleep in free space, and nodding corner sleep with clickable popping snot bubble ('Póc!').
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


class ChubbyMemeRenderer(BaseCharacterRenderer):
    """Renders Phoebe Chupi and Nono in their authentic legless Cube/Mochi dumpling proportions."""

    def __init__(self, variant: str = "phoebe"):
        self.variant = variant  # "phoebe" | "nono"

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
            cling_rot = math.sin(model.pulse_phase * 1.3) * 4.5 * model.cling_ratio
        elif model.cling_edge == "bottom":
            cling_dy = 8.0 * model.cling_ratio

        now = time.time()
        is_dizzy = model.is_dragging or (now < model.dizzy_end_time)
        is_waking_up = now < model.wake_up_until
        is_popping_bubble = now < model.bubble_pop_until
        is_clinging = model.cling_edge is not None

        # Cube Squash & Stretch Physics (anchored at the flat bottom of the cube, NO legs)
        if model.is_sleeping and not is_clinging:
            # Melted flat mochi cube when sleeping in free space
            breath = math.sin(model.pulse_phase * 1.3)
            squash_x = 1.15 + breath * 0.035
            squash_y = 0.80 - breath * 0.03
            float_y = 6.0
        elif model.is_dragging:
            # Wiggling cube in mid-air when picked up
            wiggle = math.sin(now * 22.0)
            squash_x = 0.93 + wiggle * 0.04
            squash_y = 1.07 - wiggle * 0.04
            float_y = math.sin(now * 18.0) * 2.0
        elif model.voice_state == VoiceState.SPEAKING or is_waking_up or is_popping_bubble:
            # Energetic Cube Hop ("Chupi Chupi!")
            bounce = math.sin(model.pulse_phase * 3.4)
            squash_x = 1.0 - bounce * 0.06
            squash_y = 1.0 + bounce * 0.06
            float_y = -abs(bounce) * 4.2
        else:
            # Soft rhythmic cube breathing
            breath = math.sin(model.pulse_phase * 1.5)
            squash_x = 1.0 + breath * 0.026
            squash_y = 1.0 - breath * 0.024
            float_y = breath * 1.0

        cx = base_cx + cling_dx
        cy = (height / 2.0) + 6.0 + float_y + cling_dy  # Shifted slightly down to leave room for Phoebe's big hat

        painter.save()
        if abs(cling_rot) > 0.01:
            painter.translate(cx, cy)
            painter.rotate(cling_rot)
            painter.translate(-cx, -cy)

        # Anchor squash & stretch at the bottom of the cube (cy + 26)
        bottom_anchor = cy + 26.0
        painter.translate(cx, bottom_anchor)
        painter.scale(squash_x, squash_y)
        painter.translate(-cx, -bottom_anchor)

        # 0. Soft Ground Shadow & Aura (No feet!)
        self._draw_shadow_and_aura(painter, cx, cy, model.pulse_phase)

        # 1. Back Hair / Twin-tails flaring from the sides of the cube
        self._draw_back_hair(painter, cx, cy, model, now)

        # 2. Main Unified Cube / Squishy Mochi Body (No separate torso or legs!)
        self._draw_cube_body(painter, cx, cy, model)

        # 3. Bottom Outfit Trim on the Cube Base (Cleric Gold/Blue for Phoebe, Gothic Red/Black for Nono)
        self._draw_cube_outfit_trim(painter, cx, cy, model)

        # 4. Face Features (Low-set kawaii proportion: big eyes & squishy cheeks)
        head_nod = 0.0
        if model.is_sleeping and is_clinging:
            head_nod = 3.0 + math.sin(model.pulse_phase * 1.1) * 1.8
        elif model.is_drowsy:
            head_nod = ((math.sin(model.pulse_phase * 1.2) + 1.0) / 2.0) * 2.5 * model.drowsy_ratio

        face_cy = cy + 2.0 + head_nod
        self._draw_cheeks(painter, cx, face_cy)
        self._draw_eyes(painter, cx, face_cy, model, is_dizzy, is_waking_up, is_popping_bubble)
        self._draw_mouth(painter, cx, face_cy + 8.0, model, is_dizzy, is_waking_up, is_popping_bubble)

        # 5. Front Bangs, Side Braids & Signature Headgear (Phoebe's Big Hat / Nono's Spider Lily)
        self._draw_front_hair_and_hat(painter, cx, cy, face_cy, model, now)

        # 6. Two Cute Round Circle Hands ('2 tay hình tròn')
        self._draw_round_hands(painter, cx, face_cy, model, now, is_waking_up or is_popping_bubble)

        # 7. Corner/Edge Sleep Snot Bubble ('Bong bóng mũi') OR Pop Burst Effect
        if model.is_sleeping and is_clinging:
            self._draw_snot_bubble(painter, cx + 4.5, face_cy + 6.0, model.pulse_phase)
        elif is_popping_bubble or model.bubble_pop_particles:
            self._draw_bubble_pop_effect(painter, cx + 4.5, face_cy + 6.0, model, now)

        painter.restore()

        # 8. Unscaled Overlays: Floating zZz when sleeping
        if model.is_sleeping and model.zzz_particles:
            self._draw_zzz_particles(painter, model.zzz_particles)

    # ============================================================
    # CUBE & CHARACTER COMPONENTS
    # ============================================================

    def _draw_shadow_and_aura(self, painter: QPainter, cx: float, cy: float, pulse_phase: float):
        pulse = (math.sin(pulse_phase * 1.6) + 1.0) / 2.0
        grad = QRadialGradient(cx, cy - 2.0, 48 + pulse * 4)
        if self.variant == "phoebe":
            grad.setColorAt(0.0, QColor(254, 243, 199, int(75 + pulse * 35)))
            grad.setColorAt(0.6, QColor(96, 165, 250, int(35 + pulse * 20)))
        else:
            grad.setColorAt(0.0, QColor(255, 228, 230, int(75 + pulse * 35)))
            grad.setColorAt(0.6, QColor(225, 29, 72, int(35 + pulse * 20)))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - 50, cy - 48, 100, 96))

        # Flat contact shadow right under the cube base
        sh_grad = QRadialGradient(cx, cy + 26.5, 32)
        sh_grad.setColorAt(0.0, QColor(30, 20, 15, 70))
        sh_grad.setColorAt(0.7, QColor(30, 20, 15, 25))
        sh_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(sh_grad))
        painter.drawEllipse(QRectF(cx - 32, cy + 21.5, 64, 10))

    def _draw_back_hair(self, painter: QPainter, cx: float, cy: float, model: MascotModel, now: float):
        sway = math.sin(model.pulse_phase * 1.6) * (4.0 if model.is_dragging else 1.6)
        outline_col = QColor("#3B231A") if self.variant == "phoebe" else QColor("#27272A")

        if self.variant == "phoebe":
            # Phoebe's fluffy blonde side hair peeking out below her hat brim
            hair_grad = QLinearGradient(cx, cy - 20, cx, cy + 20)
            hair_grad.setColorAt(0.0, QColor("#FFFBEB"))
            hair_grad.setColorAt(0.6, QColor("#FDE68A"))
            hair_grad.setColorAt(1.0, QColor("#F59E0B"))
            painter.setBrush(QBrush(hair_grad))
            painter.setPen(QPen(outline_col, 1.8))

            for sign in (-1.0, 1.0):
                p = QPainterPath()
                bx = cx + sign * 28.0
                by = cy - 6.0
                p.moveTo(bx, by)
                p.cubicTo(
                    bx + sign * (14.0 + sway), by + 2.0,
                    bx + sign * (16.0 + sway), by + 18.0,
                    bx + sign * (6.0 + sway * 0.5), by + 24.0
                )
                p.cubicTo(bx, by + 20.0, bx - sign * 4.0, by + 12.0, bx, by)
                painter.drawPath(p)
        else:
            # Nono's signature big bouncy ash-silver twin-tails on both sides of the cube
            hair_grad = QLinearGradient(cx, cy - 22, cx, cy + 24)
            hair_grad.setColorAt(0.0, QColor("#FFFFFF"))
            hair_grad.setColorAt(0.6, QColor("#CBD5E1"))
            hair_grad.setColorAt(1.0, QColor("#94A3B8"))
            painter.setBrush(QBrush(hair_grad))
            painter.setPen(QPen(outline_col, 1.8))

            for sign in (-1.0, 1.0):
                p = QPainterPath()
                bx = cx + sign * 26.0
                by = cy - 12.0
                p.moveTo(bx, by)
                p.cubicTo(
                    bx + sign * (20.0 + sway), by - 4.0,
                    bx + sign * (22.0 + sway), by + 18.0,
                    bx + sign * (10.0 + sway * 0.6), by + 27.0
                )
                p.cubicTo(bx + sign * 2.0, by + 22.0, bx - sign * 3.0, by + 12.0, bx, by)
                painter.drawPath(p)

                # Gothic black & crimson ribbon bows tying Nono's twin-tails
                self._draw_ribbon_bow(
                    painter, bx + sign * 2.0, by + 1.0, 6.2,
                    QColor("#18181B"), QColor("#E11D48"), sign * 18.0
                )

    def _draw_cube_body(self, painter: QPainter, cx: float, cy: float, model: MascotModel):
        """Draws the single unified Cube-Mochi body (wide rounded square with slightly wider squishy bottom cheeks)."""
        outline_col = QColor("#3B231A") if self.variant == "phoebe" else QColor("#27272A")

        # Custom squishy cube path: slightly narrower at forehead, bulging out at the lower cheeks, flat bottom
        top_w = 56.0
        bot_w = 66.0
        top_y = cy - 22.0
        bot_y = cy + 25.5

        cube_path = QPainterPath()
        cube_path.moveTo(cx - top_w / 2.0 + 10.0, top_y)
        cube_path.lineTo(cx + top_w / 2.0 - 10.0, top_y)
        # Top-right corner & right cheek bulge
        cube_path.quadTo(cx + top_w / 2.0 + 2.0, top_y, cx + bot_w / 2.0 - 2.0, cy + 2.0)
        cube_path.quadTo(cx + bot_w / 2.0 + 3.0, bot_y - 4.0, cx + bot_w / 2.0 - 10.0, bot_y)
        # Flat mochi bottom sitting directly on the ground (no legs!)
        cube_path.lineTo(cx - bot_w / 2.0 + 10.0, bot_y)
        # Bottom-left cheek bulge & top-left corner
        cube_path.quadTo(cx - bot_w / 2.0 - 3.0, bot_y - 4.0, cx - bot_w / 2.0 + 2.0, cy + 2.0)
        cube_path.quadTo(cx - top_w / 2.0 - 2.0, top_y, cx - top_w / 2.0 + 10.0, top_y)
        cube_path.closeSubpath()

        skin_grad = QLinearGradient(cx, top_y, cx, bot_y)
        skin_grad.setColorAt(0.0, QColor("#FFFFFF"))
        skin_grad.setColorAt(0.75, QColor("#FFF9F6"))
        skin_grad.setColorAt(1.0, QColor("#FFE8E2"))

        painter.setBrush(QBrush(skin_grad))
        painter.setPen(QPen(outline_col, 2.1))
        painter.drawPath(cube_path)

    def _draw_cube_outfit_trim(self, painter: QPainter, cx: float, cy: float, model: MascotModel):
        """Draws the miniature collar/capelet trim along the bottom edge of the Cube."""
        bot_y = cy + 25.5
        collar_top = cy + 16.5

        if self.variant == "phoebe":
            # Phoebe's White, Royal-Blue & Gold Cleric Capelet Trim at bottom of cube
            outline = QPen(QColor("#3B231A"), 1.3)
            gold_pen = QPen(QColor("#F59E0B"), 1.5)

            for i, dx in enumerate([-20.0, -10.0, 0.0, 10.0, 20.0]):
                w = 13.0
                h = 8.5
                rect = QRectF(cx + dx - w / 2.0, collar_top, w, h)
                painter.setBrush(QBrush(QColor("#EFF6FF") if i % 2 == 1 else QColor("#FFFFFF")))
                painter.setPen(outline)
                painter.drawEllipse(rect)
                painter.setPen(gold_pen)
                painter.drawArc(QRectF(rect.left() + 1.5, rect.top() + 1.0, rect.width() - 3.0, rect.height() - 2.0), 195 * 16, 150 * 16)

            # Blue & Gold center ribbon tie at bottom chest
            self._draw_ribbon_bow(painter, cx, collar_top + 2.5, 4.8, QColor("#2563EB"), QColor("#1E3A8A"), 0.0)
            painter.setBrush(QBrush(QColor("#FBBF24")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(cx - 1.8, collar_top + 0.7, 3.6, 3.6))
        else:
            # Nono's Gothic Black & Crimson Frill Trim at bottom of cube
            outline = QPen(QColor("#18181B"), 1.3)
            crimson_pen = QPen(QColor("#E11D48"), 1.4)

            for i, dx in enumerate([-20.0, -10.0, 0.0, 10.0, 20.0]):
                w = 13.0
                h = 8.5
                rect = QRectF(cx + dx - w / 2.0, collar_top, w, h)
                painter.setBrush(QBrush(QColor("#27272A") if i % 2 == 0 else QColor("#881337")))
                painter.setPen(outline)
                painter.drawEllipse(rect)
                painter.setPen(crimson_pen)
                painter.drawArc(QRectF(rect.left() + 1.5, rect.top() + 1.0, rect.width() - 3.0, rect.height() - 2.0), 195 * 16, 150 * 16)

            # Center crimson spider-lily gem
            painter.setBrush(QBrush(QColor("#F43F5E")))
            painter.setPen(QPen(QColor("#FFE4E6"), 1.1))
            painter.drawEllipse(QRectF(cx - 3.2, collar_top + 1.0, 6.4, 6.4))

    def _draw_cheeks(self, painter: QPainter, cx: float, face_cy: float):
        """Big wide rosy mochi cheeks with cute diagonal blush ticks."""
        painter.setBrush(QBrush(QColor(251, 113, 133, 135)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - 27.5, face_cy + 1.5, 13.5, 8.0))
        painter.drawEllipse(QRectF(cx + 14.0, face_cy + 1.5, 13.5, 8.0))

        slash_pen = QPen(QColor(225, 29, 72, 175), 1.15, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(slash_pen)
        for base_x in (cx - 21.0, cx + 20.5):
            for offset in (-2.5, 0.0, 2.5):
                painter.drawLine(QPointF(base_x + offset, face_cy + 3.8), QPointF(base_x + offset - 1.2, face_cy + 6.2))

    def _draw_eyes(self, painter: QPainter, cx: float, face_cy: float, model: MascotModel,
                   is_dizzy: bool, is_waking_up: bool, is_popping_bubble: bool):
        blink_ratio = math.sin(model.blink_phase) if model.is_blinking else 0.0
        eye_spacing = 13.5
        left_c = QPointF(cx - eye_spacing, face_cy - 1.0)
        right_c = QPointF(cx + eye_spacing, face_cy - 1.0)

        if self.variant == "phoebe":
            # Phoebe's large kawaii eyes (Deep Violet-Blue top -> Golden-Amber bottom gradient!)
            for pt in (left_c, right_c):
                self._draw_single_eye(
                    painter, pt, blink_ratio, model,
                    is_dizzy, is_waking_up, is_popping_bubble,
                    top_col=QColor("#312E81"), mid_col=QColor("#6366F1"), bot_col=QColor("#FDE047")
                )
        else:
            # Nono: Right eye (viewer's right) is deep Crimson-Ruby; Left eye (viewer's left) has white eyepatch!
            self._draw_single_eye(
                painter, right_c, blink_ratio, model,
                is_dizzy, is_waking_up, is_popping_bubble,
                top_col=QColor("#4C0519"), mid_col=QColor("#E11D48"), bot_col=QColor("#FDA4AF"),
                show_tear=model.is_dragging or is_popping_bubble
            )
            self._draw_nono_eyepatch(painter, left_c)

    def _draw_single_eye(self, painter: QPainter, center: QPointF, blink_ratio: float, model: MascotModel,
                         is_dizzy: bool, is_waking_up: bool, is_popping_bubble: bool,
                         top_col: QColor, mid_col: QColor, bot_col: QColor, show_tear: bool = False):
        outline_col = QColor("#3B231A") if self.variant == "phoebe" else QColor("#27272A")

        # 1. DRAGGING / DIZZY: Swirly '@ @' dizzy eyes + glistening blue tear drop
        if is_dizzy:
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.setPen(QPen(outline_col, 1.8))
            painter.drawEllipse(QRectF(center.x() - 6.8, center.y() - 6.8, 13.6, 13.6))

            spiral_pen = QPen(outline_col, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(spiral_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            sp = QPainterPath()
            steps = 22
            for s in range(steps):
                t = (s / float(steps - 1)) * (math.pi * 2.8)
                r_cur = 0.8 + (s / float(steps - 1)) * 4.8
                px = center.x() + math.cos(t) * r_cur
                py = center.y() + math.sin(t) * r_cur
                if s == 0:
                    sp.moveTo(px, py)
                else:
                    sp.lineTo(px, py)
            painter.drawPath(sp)

            painter.setBrush(QBrush(QColor(56, 189, 248, 235)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(center.x() + 4.0, center.y() + 2.2, 4.4, 6.0))
            return

        # 2. WAKING UP / BUBBLE POP: Wide startled 'O O' eyes with contracted pupil & shine dot
        if is_waking_up or is_popping_bubble:
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.setPen(QPen(outline_col, 1.9))
            painter.drawEllipse(QRectF(center.x() - 6.8, center.y() - 6.8, 13.6, 13.6))

            painter.setBrush(QBrush(mid_col))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(center.x() - 3.2, center.y() - 3.2, 6.4, 6.4))
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.drawEllipse(QRectF(center.x() - 1.6, center.y() - 2.0, 2.3, 2.3))
            return

        # 3. SPEAKING: Happy '^ ^' arches when speaking
        if model.voice_state == VoiceState.SPEAKING:
            pen = QPen(outline_col, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            p = QPainterPath()
            p.moveTo(center.x() - 6.0, center.y() + 1.5)
            p.quadTo(center.x(), center.y() - 5.5, center.x() + 6.0, center.y() + 1.5)
            painter.drawPath(p)
            return

        # Sleeping closed curves
        if model.is_sleeping:
            pen = QPen(outline_col, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            p = QPainterPath()
            p.moveTo(center.x() - 6.0, center.y() - 0.5)
            p.quadTo(center.x(), center.y() + 4.0, center.x() + 6.0, center.y() - 0.5)
            painter.drawPath(p)
            return

        eff_blink = max(blink_ratio, 0.55 * model.drowsy_ratio if model.is_drowsy else 0.0)
        eye_w = 12.8
        eye_h = max(1.2, 13.5 * (1.0 - eff_blink))
        if eff_blink > 0.85:
            painter.setPen(QPen(outline_col, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(QPointF(center.x() - 5.5, center.y()), QPointF(center.x() + 5.5, center.y()))
            return

        # Cute thick upper eyelash + round anime eye
        eye_rect = QRectF(center.x() - eye_w / 2.0, center.y() - eye_h / 2.0, eye_w, eye_h)
        painter.setBrush(QBrush(top_col))
        painter.setPen(QPen(outline_col, 1.8))
        painter.drawEllipse(eye_rect)

        # Iris with 360 cursor gaze tracking
        pupil_w = 9.8
        pupil_h = max(1.0, 10.5 * (1.0 - eff_blink))
        px = center.x() + model.current_eye_x * 0.8
        py = center.y() + model.current_eye_y * 0.8 * (1.0 - eff_blink)

        iris_grad = QLinearGradient(px, py - pupil_h / 2.0, px, py + pupil_h / 2.0)
        iris_grad.setColorAt(0.0, top_col)
        iris_grad.setColorAt(0.5, mid_col)
        iris_grad.setColorAt(1.0, bot_col)
        painter.setBrush(QBrush(iris_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(px - pupil_w / 2.0, py - pupil_h / 2.0, pupil_w, pupil_h))

        # Large glossy kawaii highlights
        if eff_blink < 0.6:
            painter.setBrush(QBrush(QColor(255, 255, 255, 250)))
            painter.drawEllipse(QRectF(px - 3.4, py - 4.0, 3.8, 3.8))
            painter.drawEllipse(QRectF(px + 1.4, py + 1.2, 2.0, 2.0))

    def _draw_nono_eyepatch(self, painter: QPainter, center: QPointF):
        """Draws Nono's signature white medical eyepatch & black strap over her left eye."""
        painter.save()
        strap_pen = QPen(QColor("#27272A"), 1.8)
        painter.setPen(strap_pen)
        painter.drawLine(QPointF(center.x() - 13.0, center.y() - 7.5), QPointF(center.x() + 11.0, center.y() + 4.5))

        patch_rect = QRectF(center.x() - 7.5, center.y() - 6.0, 15.0, 12.0)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.setPen(QPen(QColor("#475569"), 1.5))
        painter.drawRoundedRect(patch_rect, 3.8, 3.8)

        # Subtle pink/red cross mark on Nono's eyepatch
        cross_pen = QPen(QColor("#FDA4AF"), 1.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(cross_pen)
        painter.drawLine(QPointF(center.x() - 3.2, center.y() - 2.2), QPointF(center.x() + 3.2, center.y() + 2.2))
        painter.drawLine(QPointF(center.x() + 3.2, center.y() - 2.2), QPointF(center.x() - 3.2, center.y() + 2.2))
        painter.restore()

    def _draw_mouth(self, painter: QPainter, cx: float, cy: float, model: MascotModel,
                    is_dizzy: bool, is_waking_up: bool, is_popping_bubble: bool):
        outline_col = QColor("#3B231A") if self.variant == "phoebe" else QColor("#27272A")
        pen = QPen(outline_col, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        if is_dizzy:
            # Wavy flustered crying mouth ('﹏') when dragged/dizzy
            wavy = QPainterPath()
            wavy.moveTo(cx - 5.2, cy + 0.5)
            wavy.quadTo(cx - 2.6, cy - 2.2, cx, cy + 0.5)
            wavy.quadTo(cx + 2.6, cy + 3.0, cx + 5.2, cy + 0.2)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(wavy)
        elif is_waking_up or is_popping_bubble:
            # Surprised rounded-triangle mouth ('△' / 'Hơ?!') when woken up
            tri = QPainterPath()
            tri.moveTo(cx, cy - 2.2)
            tri.quadTo(cx + 4.2, cy - 0.2, cx + 3.2, cy + 3.0)
            tri.quadTo(cx, cy + 3.8, cx - 3.2, cy + 3.0)
            tri.quadTo(cx - 4.2, cy - 0.2, cx, cy - 2.2)
            painter.setBrush(QBrush(QColor("#FB7185")))
            painter.drawPath(tri)
        elif model.voice_state == VoiceState.SPEAKING:
            h = 2.5 + model.mouth_open * 5.0
            painter.setBrush(QBrush(QColor("#F43F5E")))
            painter.drawEllipse(QRectF(cx - 4.0, cy - 1.5, 8.0, h))
        elif model.is_sleeping:
            painter.setBrush(QBrush(QColor("#FDA4AF")))
            r = 1.6 + math.sin(model.pulse_phase * 1.1) * 0.4
            painter.drawEllipse(QRectF(cx - r, cy - 0.5, r * 2, r * 1.8))
        else:
            if self.variant == "phoebe":
                # Phoebe's signature cute dimpled smile
                path = QPainterPath()
                path.moveTo(cx - 4.5, cy - 1.2)
                path.quadTo(cx, cy + 2.5, cx + 4.5, cy - 1.2)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(path)
                painter.drawLine(QPointF(cx - 5.2, cy - 0.5), QPointF(cx - 3.8, cy - 1.8))
                painter.drawLine(QPointF(cx + 5.2, cy - 0.5), QPointF(cx + 3.8, cy - 1.8))
            else:
                # Nono's cute ':3' cat/mochi mouth
                path = QPainterPath()
                path.moveTo(cx - 4.0, cy - 0.2)
                path.quadTo(cx - 2.0, cy + 1.8, cx, cy - 0.2)
                path.quadTo(cx + 2.0, cy + 1.8, cx + 4.0, cy - 0.2)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(path)

    def _draw_front_hair_and_hat(self, painter: QPainter, cx: float, cy: float, face_cy: float, model: MascotModel, now: float):
        outline_col = QColor("#3B231A") if self.variant == "phoebe" else QColor("#27272A")
        top_y = cy - 23.0

        # 1. Fluffy Bangs across the top of the Cube
        bangs = QPainterPath()
        bangs.moveTo(cx - 28.0, face_cy - 6.0)
        bangs.cubicTo(cx - 28.0, top_y, cx + 28.0, top_y, cx + 28.0, face_cy - 6.0)
        bangs.quadTo(cx + 19.0, face_cy - 13.0, cx + 12.0, face_cy - 5.0)
        bangs.quadTo(cx + 5.0, face_cy - 14.5, cx, face_cy - 4.5)
        bangs.quadTo(cx - 5.0, face_cy - 14.5, cx - 12.0, face_cy - 5.0)
        bangs.quadTo(cx - 19.0, face_cy - 13.0, cx - 28.0, face_cy - 6.0)

        if self.variant == "phoebe":
            hair_grad = QLinearGradient(cx, top_y, cx, face_cy + 8.0)
            hair_grad.setColorAt(0.0, QColor("#FFFBEB"))
            hair_grad.setColorAt(0.7, QColor("#FEF3C7"))
            hair_grad.setColorAt(1.0, QColor("#FDE68A"))
        else:
            hair_grad = QLinearGradient(cx, top_y, cx, face_cy + 8.0)
            hair_grad.setColorAt(0.0, QColor("#FFFFFF"))
            hair_grad.setColorAt(0.7, QColor("#E2E8F0"))
            hair_grad.setColorAt(1.0, QColor("#CBD5E1"))

        painter.setBrush(QBrush(hair_grad))
        painter.setPen(QPen(outline_col, 1.7))
        painter.drawPath(bangs)

        # Side braids / locks framing the cube face
        for sign in (-1.0, 1.0):
            lock = QPainterPath()
            bx = cx + sign * 26.5
            lock.moveTo(bx, face_cy - 10.0)
            lock.quadTo(bx + sign * 6.5, face_cy + 1.0, bx + sign * 3.0, face_cy + 11.0)
            lock.quadTo(bx - sign * 2.5, face_cy + 5.0, bx - sign * 3.0, face_cy - 6.0)
            lock.closeSubpath()
            painter.drawPath(lock)

        if self.variant == "phoebe":
            # Side hair ribbons (blue & white bows)
            self._draw_ribbon_bow(painter, cx - 27.5, face_cy - 3.5, 4.8, QColor("#60A5FA"), QColor("#1E3A8A"), 16.0)
            self._draw_ribbon_bow(painter, cx + 27.5, face_cy - 3.5, 4.8, QColor("#FFFFFF"), QColor("#3B231A"), -16.0)

            # 2. PHOEBE'S SIGNATURE ACOLYTE BERET / WIDE-BRIM HAT!
            self._draw_phoebe_hat(painter, cx, top_y + 2.0, model.pulse_phase)
        else:
            # Nono's signature blooming Red Spider Lily (Hoa Bỉ Ngạn Đỏ) on upper left forehead
            self._draw_spider_lily(painter, cx - 20.0, face_cy - 14.0, model.pulse_phase)

    def _draw_phoebe_hat(self, painter: QPainter, cx: float, hat_base_y: float, pulse_phase: float):
        """Draws Phoebe's iconic White, Royal-Blue & Gold Acolyte Hat sitting atop the Cube."""
        painter.save()
        outline_col = QColor("#3B231A")

        # 1. Upper Puffy White Beret / Crown of the Hat
        crown_path = QPainterPath()
        crown_path.moveTo(cx - 26.0, hat_base_y)
        crown_path.cubicTo(
            cx - 30.0, hat_base_y - 16.0,
            cx - 12.0, hat_base_y - 22.0,
            cx, hat_base_y - 22.0
        )
        crown_path.cubicTo(
            cx + 12.0, hat_base_y - 22.0,
            cx + 30.0, hat_base_y - 16.0,
            cx + 26.0, hat_base_y
        )
        crown_path.closeSubpath()

        crown_grad = QLinearGradient(cx, hat_base_y - 22.0, cx, hat_base_y)
        crown_grad.setColorAt(0.0, QColor("#FFFFFF"))
        crown_grad.setColorAt(0.8, QColor("#F8FAFC"))
        crown_grad.setColorAt(1.0, QColor("#E2E8F0"))
        painter.setBrush(QBrush(crown_grad))
        painter.setPen(QPen(outline_col, 1.8))
        painter.drawPath(crown_path)

        # Royal-Blue Hat Band with Gold Trim
        band_path = QPainterPath()
        band_path.moveTo(cx - 27.0, hat_base_y + 1.0)
        band_path.quadTo(cx, hat_base_y - 7.0, cx + 27.0, hat_base_y + 1.0)
        band_path.quadTo(cx, hat_base_y - 1.5, cx - 27.0, hat_base_y + 1.0)
        painter.setBrush(QBrush(QColor("#1D4ED8")))
        painter.setPen(QPen(QColor("#F59E0B"), 1.4))
        painter.drawPath(band_path)

        # 2. Wide Curved White & Gold Hat Brim framing the top of her head
        brim_path = QPainterPath()
        brim_path.moveTo(cx - 35.0, hat_base_y + 3.5)
        brim_path.quadTo(cx, hat_base_y - 6.5, cx + 35.0, hat_base_y + 3.5)
        brim_path.quadTo(cx, hat_base_y + 0.5, cx - 35.0, hat_base_y + 3.5)

        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.setPen(QPen(outline_col, 1.7))
        painter.drawPath(brim_path)

        # Golden rim highlight along the hat brim
        painter.setPen(QPen(QColor("#F59E0B"), 1.3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(QRectF(cx - 33.0, hat_base_y - 3.5, 66.0, 9.0), 20 * 16, 140 * 16)

        # 3. Golden 4-Point Star / Cross Emblem on the front center of the hat
        self._draw_sparkle(painter, cx, hat_base_y - 9.5, 6.2, QColor("#FBBF24"), border_col=QColor("#B45309"))
        # Small golden side wing/antler ornaments on the hat
        self._draw_sparkle(painter, cx - 15.0, hat_base_y - 7.5, 3.2, QColor("#FDE047"))
        self._draw_sparkle(painter, cx + 15.0, hat_base_y - 7.5, 3.2, QColor("#FDE047"))

        painter.restore()

    def _draw_round_hands(self, painter: QPainter, cx: float, face_cy: float,
                          model: MascotModel, now: float, is_startled: bool):
        """Draws ONLY 2 cute circular hands ('2 tay hình tròn') pressing cheeks or waving!"""
        outline_col = QColor("#3B231A") if self.variant == "phoebe" else QColor("#27272A")
        hand_grad = QRadialGradient(0, -2, 8.0)
        hand_grad.setColorAt(0.0, QColor("#FFFFFF"))
        hand_grad.setColorAt(1.0, QColor("#FFE4E6"))

        r = 6.8  # Radius of each round ball hand (diameter ~13.6px)

        if model.is_dragging or (now < model.dizzy_end_time):
            # Waving round hands frantically high in the air + flying sweat drops!
            wave = math.sin(now * 24.0) * 4.5
            positions = [
                (cx - 28.0, face_cy - 3.0 + wave),
                (cx + 28.0, face_cy - 3.0 - wave),
            ]
            sweat_bob = (now * 7.0) % 1.0
            painter.save()
            painter.setBrush(QBrush(QColor(56, 189, 248, 210)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(cx - 36.0 - sweat_bob * 3.0, face_cy - 18.0 + sweat_bob * 4.0, 3.8, 5.6))
            painter.drawEllipse(QRectF(cx + 32.0 + sweat_bob * 3.0, face_cy - 18.0 + sweat_bob * 4.0, 3.8, 5.6))
            painter.restore()
        elif is_startled:
            # Waking up: Left round hand rubbing sleepy eye, right hand startled up!
            rub = math.sin(now * 16.0) * 1.8
            positions = [
                (cx - 15.0 + rub, face_cy + 1.5),
                (cx + 23.5, face_cy + 5.0 - abs(rub)),
            ]
        elif model.is_sleeping and model.cling_edge is None:
            # Resting round hands peacefully in front of the cube
            positions = [
                (cx - 13.0, face_cy + 14.0),
                (cx + 13.0, face_cy + 14.0),
            ]
        else:
            # Iconic Chubby Cube pose: 2 round ball hands held right up under/against her squishy cheeks!
            bob = math.sin(model.pulse_phase * 2.4) * (2.2 if model.voice_state == VoiceState.SPEAKING else 0.8)
            positions = [
                (cx - 19.5, face_cy + 9.5 + bob),
                (cx + 19.5, face_cy + 9.5 + bob),
            ]

        for hx, hy in positions:
            painter.save()
            painter.translate(hx, hy)
            painter.setBrush(QBrush(hand_grad))
            painter.setPen(QPen(outline_col, 1.9))
            painter.drawEllipse(QRectF(-r, -r, r * 2.0, r * 2.0))
            painter.restore()

    # ============================================================
    # ACCESSORIES & MEME EFFECTS
    # ============================================================

    def _draw_ribbon_bow(self, painter: QPainter, cx: float, cy: float, size: float,
                         fill_col: QColor, border_col: QColor, angle: float = 0.0):
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(angle)
        painter.setBrush(QBrush(fill_col))
        painter.setPen(QPen(border_col, 1.2))

        left_wing = QPolygonF([QPointF(0, 0), QPointF(-size, -size * 0.65), QPointF(-size, size * 0.65)])
        right_wing = QPolygonF([QPointF(0, 0), QPointF(size, -size * 0.65), QPointF(size, size * 0.65)])
        painter.drawPolygon(left_wing)
        painter.drawPolygon(right_wing)
        painter.drawEllipse(QRectF(-size * 0.28, -size * 0.28, size * 0.56, size * 0.56))
        painter.restore()

    def _draw_spider_lily(self, painter: QPainter, cx: float, cy: float, pulse_phase: float):
        """Draws Nono's blooming Red Spider Lily (Hoa Bỉ Ngạn) hair accessory."""
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(-15.0 + math.sin(pulse_phase * 1.4) * 3.0)

        painter.setBrush(QBrush(QColor("#E11D48")))
        painter.setPen(QPen(QColor("#881337"), 1.0))
        for i in range(6):
            angle = (i / 6.0) * math.pi * 2.0
            px = math.cos(angle) * 7.0
            py = math.sin(angle) * 7.0
            petal = QPainterPath()
            petal.moveTo(0, 0)
            petal.quadTo(px * 0.6 - py * 0.3, py * 0.6 + px * 0.3, px, py)
            petal.quadTo(px * 0.6 + py * 0.3, py * 0.6 - px * 0.3, 0, 0)
            painter.drawPath(petal)

        stamen_pen = QPen(QColor("#FDA4AF"), 0.9)
        painter.setPen(stamen_pen)
        for i in range(5):
            ang = -0.8 + i * 0.4
            painter.drawLine(QPointF(0, 0), QPointF(math.cos(ang) * 9.5, math.sin(ang) * 9.5))

        painter.setBrush(QBrush(QColor("#FECDD3")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(-2.0, -2.0, 4.0, 4.0))
        painter.restore()

    def _draw_sparkle(self, painter: QPainter, cx: float, cy: float, size: float,
                      color: QColor, border_col: QColor | None = None):
        painter.save()
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(border_col, 1.0) if border_col else Qt.PenStyle.NoPen)
        star = QPolygonF([
            QPointF(cx, cy - size),
            QPointF(cx + size * 0.28, cy - size * 0.28),
            QPointF(cx + size, cy),
            QPointF(cx + size * 0.28, cy + size * 0.28),
            QPointF(cx, cy + size),
            QPointF(cx - size * 0.28, cy + size * 0.28),
            QPointF(cx - size, cy),
            QPointF(cx - size * 0.28, cy - size * 0.28),
        ])
        painter.drawPolygon(star)
        painter.restore()

    def _draw_meme_speech_tag(
        self,
        painter: QPainter,
        cx: float,
        top_y: float,
        pulse_phase: float,
        override_text: str | None = None,
        mode: str = "talk",
    ):
        painter.save()
        bob = math.sin(pulse_phase * 4.0) * 2.0
        text = override_text or ("Chupi~!" if self.variant == "phoebe" else "Nono~!")
        if mode == "drag":
            bg_col = QColor(254, 226, 226, 240)
            border_col = QColor("#EF4444")
            text_col = QColor("#991B1B")
        elif mode == "wakeup":
            bg_col = QColor(254, 249, 195, 240)
            border_col = QColor("#F59E0B")
            text_col = QColor("#92400E")
        else:
            bg_col = QColor(254, 243, 199, 235) if self.variant == "phoebe" else QColor(255, 228, 230, 235)
            border_col = QColor("#F59E0B") if self.variant == "phoebe" else QColor("#E11D48")
            text_col = QColor("#92400E") if self.variant == "phoebe" else QColor("#9F1239")

        w = max(52.0, len(text) * 6.0)
        pill_rect = QRectF(cx - w / 2.0, max(2.0, top_y - 8.0 + bob), w, 16.0)
        painter.setBrush(QBrush(bg_col))
        painter.setPen(QPen(border_col, 1.4))
        painter.drawRoundedRect(pill_rect, 8.0, 8.0)

        font = QFont("Arial", 8, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(text_col)
        painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()

    def _draw_snot_bubble(self, painter: QPainter, nx: float, ny: float, pulse_phase: float):
        breath = (math.sin(pulse_phase * 1.2) + 1.0) / 2.0
        radius = 5.5 + breath * 6.5
        bx = nx + radius * 0.78
        by = ny - radius * 0.25

        bubble_grad = QRadialGradient(bx - radius * 0.3, by - radius * 0.3, radius * 1.2)
        bubble_grad.setColorAt(0.0, QColor(255, 255, 255, 215))
        bubble_grad.setColorAt(0.4, QColor(186, 230, 253, 160))
        bubble_grad.setColorAt(0.85, QColor(56, 189, 248, 135))
        bubble_grad.setColorAt(1.0, QColor(244, 114, 182, 165))

        painter.save()
        painter.setBrush(QBrush(bubble_grad))
        painter.setPen(QPen(QColor(125, 211, 252, 225), 1.3))
        painter.drawEllipse(QRectF(bx - radius, by - radius, radius * 2.0, radius * 2.0))

        painter.setBrush(QBrush(QColor(255, 255, 255, 235)))
        painter.setPen(Qt.PenStyle.NoPen)
        hl_r = radius * 0.28
        painter.drawEllipse(QRectF(bx - radius * 0.48, by - radius * 0.52, hl_r * 1.3, hl_r * 0.9))
        painter.restore()

    def _draw_bubble_pop_effect(self, painter: QPainter, nx: float, ny: float, model: MascotModel, now: float):
        painter.save()
        cx = nx + 8.0
        cy = ny - 2.0

        rem = model.bubble_pop_until - now
        if rem > 0:
            prog = 1.0 - (rem / 0.65)
            ring_r = 6.0 + prog * 18.0
            alpha = max(0, min(255, int(240 * (1.0 - prog))))
            painter.setPen(QPen(QColor(56, 189, 248, alpha), 2.0, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(cx - ring_r, cy - ring_r, ring_r * 2.0, ring_r * 2.0))

            font = QFont("Arial", 9, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor(244, 63, 94, alpha))
            painter.drawText(QPointF(cx + 6.0, cy - 8.0 - prog * 8.0), "Póc!")

        painter.setPen(Qt.PenStyle.NoPen)
        for bp in model.bubble_pop_particles:
            alpha = max(0, min(255, int(bp.get("alpha", 200))))
            painter.setBrush(QBrush(QColor(125, 211, 252, alpha)))
            r = bp.get("r", 2.2)
            painter.drawEllipse(QRectF(cx + bp["dx"] - r, cy + bp["dy"] - r, r * 2.0, r * 2.0))

        painter.restore()

    def _draw_zzz_particles(self, painter: QPainter, particles: list):
        painter.save()
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)
        col = QColor("#F59E0B") if self.variant == "phoebe" else QColor("#E11D48")
        for p in particles:
            alpha = max(0, min(255, int(p.get("alpha", 200))))
            painter.setPen(QColor(col.red(), col.green(), col.blue(), alpha))
            painter.drawText(QPointF(p["x"], p["y"]), p.get("char", "z"))
        painter.restore()
