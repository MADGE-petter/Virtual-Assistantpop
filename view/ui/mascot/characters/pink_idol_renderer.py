"""Pink Idol Renderer - High-FPS Hybrid Sprite & Procedural Renderer for 'Aemeath (Thiên Thần Idol)'.

Distinct Expressions & Animations per State:
1. IDLE (`idle.png` — Image 1):
   - Starry golden-amber eyes (`✦` pupils), cute `v` smile, soft mochi breathing squash & stretch,
     periodic natural blinking (`_blink_pm`), and twinkling 4-point angel stars (`✦`).
2. SPEAKING / TALKING (`VoiceState.SPEAKING` — based on Image 1 `idle.png`):
   - Keeps her starry golden-amber eyes (`✦` pupils) from Image 1 while animating a natural
     lip-sync talking mouth (`_talk_half_pm` & `_talk_open_pm` synthesized from `idle.png` with
     a cute pink open cat-fang mouth), gentle talking bounce, and 'Aemeath~✦' speech tag.
3. PLAYING MUSIC / YOUTUBE (`model.is_playing_music` — Image 2 `talk.png` / `music.png`):
   - Triggered when playing music or YouTube audio: switches to Image 2 with happy `> <` closed eyes,
     open cheering mouth, and 2 cute round paw hands waving 2 glowing concert lightsticks
     (Left: Purple `#D946EF`, Right: Coral-Pink `#F43F5E`), neon lightstick bloom, floating
     musical notes (`♪ ♫`), and '♪ Quẩy Nhạc~♫' tag!
4. DRAGGING / DIZZY (`_drag_pm`):
   - Swirly dizzy eyes (`@ @`) with glistening tear drops (`💧`), flushed red cheeks, wavy flustered
     mouth (`﹏`), frantically waving round hands, flying sweat drops (`💦`), and 'Áaa~ Thả ra!' tag.
5. WAKING UP / BUBBLE POP (`_wakeup_pm`):
   - Wide-open startled golden eyes with tiny shocked pupils (`O O`), surprised triangular mouth (`△`),
     one round paw rubbing her eye while the other flinches up, shock rays, and 'Hơ?! Tỉnh rồi!' tag.
6. SLEEPING (`_sleep_pm`):
   - Peaceful curved closed eyelashes (`︶ ︶`), tiny breathing mouth, expanding/contracting
     Snot Bubble ('Bong bóng mũi'), and floating pink `zZz` particles.
"""

import math
import os
import time
from typing import Optional, List, Tuple
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QPixmap, QImage, QImageReader, QColor, QBrush, QPen,
    QLinearGradient, QRadialGradient, QPainterPath, QPolygonF, QFont
)
from model.voice_state_model import VoiceState
from utils.paths import resource_path
from view.ui.mascot.characters.base_character_renderer import BaseCharacterRenderer
from view.ui.mascot.mascot_model import MascotModel


class PinkIdolRenderer(BaseCharacterRenderer):
    """Renders Aemeath (Thiên Thần Idol) with distinct Idle, Talking (Image 1), Music/YT (Image 2), Drag, Wake-Up, and Sleep states."""

    def __init__(self, skin_dir: Optional[str] = None):
        self.skin_dir = skin_dir or resource_path(os.path.join("skins", "aemeath_idol"))
        self._idle_pm: Optional[QPixmap] = None
        self._talk_half_pm: Optional[QPixmap] = None
        self._talk_open_pm: Optional[QPixmap] = None
        self._music_pm: Optional[QPixmap] = None
        self._blink_pm: Optional[QPixmap] = None
        self._sleep_pm: Optional[QPixmap] = None
        self._drag_pm: Optional[QPixmap] = None
        self._wakeup_pm: Optional[QPixmap] = None

        # Animated GIF sequences (exact frames & delays from original animated GIFs!)
        self._music_frames: List[QPixmap] = []
        self._music_delays: List[float] = []
        self._music_total_time: float = 0.0

        self._talk_frames: List[QPixmap] = []
        self._talk_delays: List[float] = []
        self._talk_total_time: float = 0.0

        self._load_sprites()

    @staticmethod
    def _load_gif_frames(gif_path: str) -> Tuple[List[QPixmap], List[float], float]:
        frames: List[QPixmap] = []
        delays: List[float] = []
        total_time: float = 0.0
        if not os.path.isfile(gif_path):
            return frames, delays, total_time

        reader = QImageReader(gif_path)
        reader.setAutoDetectImageFormat(True)
        while True:
            img = reader.read()
            if img.isNull():
                break
            d_ms = reader.nextImageDelay()
            if d_ms <= 0:
                d_ms = 50
            delay_sec = d_ms / 1000.0
            delays.append(delay_sec)
            total_time += delay_sec
            frames.append(QPixmap.fromImage(img))

        return frames, delays, total_time

    @staticmethod
    def _get_animated_frame(
        frames: List[QPixmap], delays: List[float], total_time: float, now: float
    ) -> Optional[QPixmap]:
        if not frames:
            return None
        if len(frames) == 1 or total_time <= 0.0:
            return frames[0]

        t = now % total_time
        accum = 0.0
        for frame, delay in zip(frames, delays):
            accum += delay
            if t < accum:
                return frame
        return frames[-1]

    def _load_sprites(self):
        idle_path = os.path.join(self.skin_dir, "idle.png")
        music_png = os.path.join(self.skin_dir, "music.png")
        talk_png = os.path.join(self.skin_dir, "talk.png")

        music_gif = os.path.join(self.skin_dir, "music.gif")
        talk_gif = os.path.join(self.skin_dir, "talk.gif")

        # 1. Load authentic animated GIF sequences if present
        if os.path.isfile(music_gif):
            self._music_frames, self._music_delays, self._music_total_time = self._load_gif_frames(music_gif)
            if self._music_frames:
                self._music_pm = self._music_frames[0]

        if os.path.isfile(talk_gif):
            self._talk_frames, self._talk_delays, self._talk_total_time = self._load_gif_frames(talk_gif)

        # 2. Load static sprites (or synthesize if missing)
        if os.path.isfile(idle_path):
            pm = QPixmap(idle_path)
            if not pm.isNull():
                self._idle_pm = pm
                self._talk_half_pm = self._build_talking_mouth_pixmap(pm, openness=0.55)
                self._talk_open_pm = self._build_talking_mouth_pixmap(pm, openness=1.0)
                self._blink_pm = self._build_face_variant_pixmap(pm, mode="blink")
                self._sleep_pm = self._build_face_variant_pixmap(pm, mode="sleep")
                self._drag_pm = self._build_face_variant_pixmap(pm, mode="drag")
                self._wakeup_pm = self._build_face_variant_pixmap(pm, mode="wakeup")
        elif self._talk_frames:
            pm = self._talk_frames[0]
            self._idle_pm = pm
            self._talk_half_pm = self._build_talking_mouth_pixmap(pm, openness=0.55)
            self._talk_open_pm = self._build_talking_mouth_pixmap(pm, openness=1.0)
            self._blink_pm = self._build_face_variant_pixmap(pm, mode="blink")
            self._sleep_pm = self._build_face_variant_pixmap(pm, mode="sleep")
            self._drag_pm = self._build_face_variant_pixmap(pm, mode="drag")
            self._wakeup_pm = self._build_face_variant_pixmap(pm, mode="wakeup")

        # 3. Static fallback for music
        if self._music_pm is None:
            lightstick_file = music_png if os.path.isfile(music_png) else talk_png
            if os.path.isfile(lightstick_file):
                pm = QPixmap(lightstick_file)
                if not pm.isNull():
                    self._music_pm = pm

    @classmethod
    def _build_talking_mouth_pixmap(cls, idle_pm: QPixmap, openness: float = 1.0) -> QPixmap:
        """
        Synthesizes natural talking frames from Image 1 (`idle.png`):
        Keeps her starry golden-amber eyes open and replaces the tiny `v` smile
        with a cute open pink talking mouth (with a little cat-fang notch at the top).
        """
        img = idle_pm.toImage().convertToFormat(QImage.Format.Format_ARGB32)
        w, h = img.width(), img.height()
        sx = w / 200.0
        sy = h / 200.0
        skin_color = QColor(253, 235, 237, 255)

        # Clear the tiny `v` smile in idle.png (around x=84..104, y=151..161)
        for y in range(int(151 * sy), min(h, int(162 * sy))):
            for x in range(int(84 * sx), min(w, int(104 * sx))):
                img.setPixelColor(x, y, skin_color)

        result = QPixmap.fromImage(img)
        p = QPainter(result)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        mcx = 94.0 * sx
        mcy = 155.5 * sy
        mw = (6.8 + openness * 3.4) * sx
        mh = (4.2 + openness * 5.8) * sy

        # Cute open pink anime mouth with subtle top cat-fang curve (matching her sticker style)
        mouth_path = QPainterPath()
        mouth_path.moveTo(mcx - mw, mcy - mh * 0.35)
        mouth_path.quadTo(mcx - mw * 0.4, mcy - mh * 0.55, mcx, mcy - mh * 0.25)
        mouth_path.quadTo(mcx + mw * 0.4, mcy - mh * 0.55, mcx + mw, mcy - mh * 0.35)
        mouth_path.quadTo(mcx + mw * 0.85, mcy + mh * 0.85, mcx, mcy + mh * 0.90)
        mouth_path.quadTo(mcx - mw * 0.85, mcy + mh * 0.85, mcx - mw, mcy - mh * 0.35)
        mouth_path.closeSubpath()

        p.setBrush(QBrush(QColor("#F699A6")))
        p.setPen(QPen(QColor("#D96B7D"), 1.6 * sx))
        p.drawPath(mouth_path)

        p.end()
        return result

    @staticmethod
    def _clean_face_canvas(idle_pm: QPixmap, clear_mouth: bool = False) -> QImage:
        """Clears the open eyes (and optionally the small smile) to skin tone while preserving pink bangs strands."""
        img = idle_pm.toImage().convertToFormat(QImage.Format.Format_ARGB32)
        w, h = img.width(), img.height()
        skin_color = QColor(253, 235, 237, 255)

        sx = w / 200.0
        sy = h / 200.0
        eyes = [(64.0 * sx, 134.5 * sy, 24.0 * sx, 22.5 * sy), (125.0 * sx, 135.5 * sy, 24.0 * sx, 22.5 * sy)]

        for y in range(int(107 * sy), min(h, int(163 * sy))):
            for x in range(int(35 * sx), min(w, int(155 * sx))):
                in_eye = False
                for ecx, ecy, rx, ry in eyes:
                    if ((x - ecx) / rx) ** 2 + ((y - ecy) / ry) ** 2 <= 1.0:
                        in_eye = True
                        break
                if not in_eye:
                    continue

                c = img.pixelColor(x, y)
                if c.alpha() < 180:
                    continue
                r, g, b = c.red(), c.green(), c.blue()
                # Preserve pastel pink hair strands overlapping the upper eye
                is_pink_bangs = (r > 215 and 165 <= g <= 222 and 175 <= b <= 230 and (r - g) > 18 and abs(g - b) < 22)
                if not is_pink_bangs:
                    img.setPixelColor(x, y, skin_color)

        if clear_mouth:
            for y in range(int(151 * sy), min(h, int(162 * sy))):
                for x in range(int(84 * sx), min(w, int(104 * sx))):
                    img.setPixelColor(x, y, skin_color)

        return img

    @classmethod
    def _build_face_variant_pixmap(cls, idle_pm: QPixmap, mode: str) -> QPixmap:
        """
        Synthesizes distinct face expressions from `idle.png`:
        - 'blink': natural closed eyelashes with cute smile
        - 'sleep': peaceful sleeping eyelashes + tiny breathing 'o' mouth
        - 'drag': swirly dizzy/crying eyes (`@ @` + tear drops) + wavy flustered mouth (`﹏`)
        - 'wakeup': wide-open startled eyes (`O O` with tiny shocked pupils) + surprised cat mouth (`△`)
        """
        clear_mouth = mode in ("sleep", "drag", "wakeup")
        img = cls._clean_face_canvas(idle_pm, clear_mouth=clear_mouth)
        w, h = img.width(), img.height()
        sx = w / 200.0
        sy = h / 200.0

        result = QPixmap.fromImage(img)
        p = QPainter(result)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        eye_centers = [(64.0 * sx, 134.5 * sy), (125.0 * sx, 135.5 * sy)]
        mouth_cx, mouth_cy = 94.0 * sx, 155.5 * sy

        if mode in ("blink", "sleep"):
            lash_pen = QPen(QColor("#481B16"), max(3.5, 4.2 * sx), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            p.setPen(lash_pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            for ecx, ecy in eye_centers:
                path = QPainterPath()
                path.moveTo(ecx - 15.5 * sx, ecy + 1.0 * sy)
                path.quadTo(ecx, ecy + (10.5 if mode == "sleep" else 8.0) * sy, ecx + 15.5 * sx, ecy + 1.0 * sy)
                p.drawPath(path)
                p.drawLine(QPointF(ecx - 15.5 * sx, ecy + 1.0 * sy), QPointF(ecx - 18.5 * sx, ecy + 4.0 * sy))
                p.drawLine(QPointF(ecx + 15.5 * sx, ecy + 1.0 * sy), QPointF(ecx + 18.5 * sx, ecy + 4.0 * sy))

            if mode == "sleep":
                p.setBrush(QBrush(QColor("#F48B9A")))
                p.setPen(QPen(QColor("#C86475"), 1.6 * sx))
                p.drawEllipse(QRectF(mouth_cx - 3.2 * sx, mouth_cy - 2.5 * sy, 6.4 * sx, 5.2 * sy))

        elif mode == "drag":
            # DRAGGING / DIZZY: Flushed blush + Swirly '@ @' dizzy eyes + Tear drops + Wavy flustered mouth
            p.setBrush(QBrush(QColor(251, 113, 133, 115)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(36 * sx, 142 * sy, 22 * sx, 12 * sy))
            p.drawEllipse(QRectF(130 * sx, 142 * sy, 22 * sx, 12 * sy))

            for idx, (ecx, ecy) in enumerate(eye_centers):
                p.setBrush(QBrush(QColor("#FFF9F5")))
                p.setPen(QPen(QColor("#481B16"), 3.2 * sx))
                p.drawEllipse(QRectF(ecx - 15.0 * sx, ecy - 14.0 * sy, 30.0 * sx, 28.0 * sy))

                spiral_pen = QPen(QColor("#5C2418"), 2.8 * sx, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
                p.setPen(spiral_pen)
                p.setBrush(Qt.BrushStyle.NoBrush)
                sp = QPainterPath()
                steps = 28
                for s in range(steps):
                    t = (s / float(steps - 1)) * (math.pi * 3.1)
                    r_cur = (1.5 + (s / float(steps - 1)) * 10.5) * sx
                    ang = t if idx == 0 else -t
                    px = ecx + math.cos(ang) * r_cur
                    py = ecy + math.sin(ang) * r_cur * 0.92
                    if s == 0:
                        sp.moveTo(px, py)
                    else:
                        sp.lineTo(px, py)
                p.drawPath(sp)

                tx = ecx - 14.0 * sx if idx == 0 else ecx + 8.0 * sx
                ty = ecy + 6.0 * sy
                p.setBrush(QBrush(QColor(56, 189, 248, 235)))
                p.setPen(QPen(QColor("#0284C7"), 1.4 * sx))
                p.drawEllipse(QRectF(tx, ty, 7.5 * sx, 10.5 * sy))
                p.setBrush(QBrush(QColor(255, 255, 255, 240)))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QRectF(tx + 1.8 * sx, ty + 2.0 * sy, 2.5 * sx, 2.5 * sy))

            wavy = QPainterPath()
            wavy.moveTo(mouth_cx - 11.0 * sx, mouth_cy + 1.0 * sy)
            wavy.quadTo(mouth_cx - 5.5 * sx, mouth_cy - 5.0 * sy, mouth_cx, mouth_cy + 1.0 * sy)
            wavy.quadTo(mouth_cx + 5.5 * sx, mouth_cy + 6.5 * sy, mouth_cx + 11.0 * sx, mouth_cy + 0.5 * sy)
            p.setPen(QPen(QColor("#881337"), 2.8 * sx, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(wavy)

        elif mode == "wakeup":
            # WAKING UP / BUBBLE POP: Startled wide-open golden eyes with tiny shocked star pupils + surprised '△' mouth
            p.setBrush(QBrush(QColor(251, 113, 133, 95)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(38 * sx, 143 * sy, 20 * sx, 10 * sy))
            p.drawEllipse(QRectF(130 * sx, 143 * sy, 20 * sx, 10 * sy))

            for ecx, ecy in eye_centers:
                p.setBrush(QBrush(QColor("#FFFFFF")))
                p.setPen(QPen(QColor("#481B16"), 3.4 * sx))
                p.drawEllipse(QRectF(ecx - 15.5 * sx, ecy - 15.0 * sy, 31.0 * sx, 30.0 * sy))

                iris_grad = QRadialGradient(ecx, ecy, 10.0 * sx)
                iris_grad.setColorAt(0.0, QColor("#FDE68A"))
                iris_grad.setColorAt(0.6, QColor("#D97706"))
                iris_grad.setColorAt(1.0, QColor("#78350F"))
                p.setBrush(QBrush(iris_grad))
                p.setPen(QPen(QColor("#481B16"), 1.6 * sx))
                p.drawEllipse(QRectF(ecx - 9.0 * sx, ecy - 9.0 * sy, 18.0 * sx, 18.0 * sy))

                cls._draw_four_point_star(p, ecx, ecy, 5.2 * sx, QColor("#FEF08A"))
                p.setBrush(QBrush(QColor("#FFFFFF")))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QRectF(ecx - 6.0 * sx, ecy - 7.5 * sy, 4.5 * sx, 4.5 * sy))

            mouth_path = QPainterPath()
            mouth_path.moveTo(mouth_cx, mouth_cy - 5.0 * sy)
            mouth_path.quadTo(mouth_cx + 8.5 * sx, mouth_cy - 1.0 * sy, mouth_cx + 6.5 * sx, mouth_cy + 5.5 * sy)
            mouth_path.quadTo(mouth_cx, mouth_cy + 7.0 * sy, mouth_cx - 6.5 * sx, mouth_cy + 5.5 * sy)
            mouth_path.quadTo(mouth_cx - 8.5 * sx, mouth_cy - 1.0 * sy, mouth_cx, mouth_cy - 5.0 * sy)
            p.setBrush(QBrush(QColor("#FB7185")))
            p.setPen(QPen(QColor("#881337"), 2.2 * sx))
            p.drawPath(mouth_path)

        p.end()
        return result

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
        # Separate all 6 states cleanly:
        is_dragging_or_dizzy = model.is_dragging or (now < model.dizzy_end_time)
        is_popping_bubble = now < model.bubble_pop_until
        is_waking_up = (now < model.wake_up_until) or is_popping_bubble
        is_speaking = (model.voice_state == VoiceState.SPEAKING) and not is_dragging_or_dizzy and not is_waking_up
        is_music = (
            getattr(model, "is_playing_music", False)
            and not is_speaking
            and not is_dragging_or_dizzy
            and not is_waking_up
            and not model.is_sleeping
        )
        is_clinging = model.cling_edge is not None

        # Distinct Squash & Stretch + Motion Physics per State
        extra_rot = 0.0
        shake_x = 0.0
        if model.is_sleeping and not is_clinging:
            breath = math.sin(model.pulse_phase * 1.3)
            squash_x = 1.08 + breath * 0.03
            squash_y = 0.90 - breath * 0.025
            float_y = 5.0
        elif is_dragging_or_dizzy:
            # Frantic mid-air wiggle & shake when picked up / dizzy!
            wiggle = math.sin(now * 24.0)
            squash_x = 0.93 + wiggle * 0.045
            squash_y = 1.07 - wiggle * 0.045
            float_y = math.sin(now * 18.0) * 3.0
            shake_x = math.cos(now * 28.0) * 2.5
            extra_rot = wiggle * 8.5
        elif is_waking_up:
            # Startled vertical jump & shudder when woken up or bubble popped!
            rem = max(0.0, max(model.wake_up_until - now, model.bubble_pop_until - now))
            jump_wave = abs(math.sin(rem * 14.0))
            squash_x = 0.94 + (1.0 - jump_wave) * 0.06
            squash_y = 1.08 - (1.0 - jump_wave) * 0.06
            float_y = -jump_wave * 7.5
            extra_rot = math.sin(now * 20.0) * 3.2
        elif is_music:
            # When animated GIF is active, preserve 100% authentic hand-crafted animation frames
            if self._music_frames:
                squash_x = 1.0
                squash_y = 1.0
                float_y = 0.0
                extra_rot = 0.0
            else:
                music_bob = math.sin(model.pulse_phase * 3.2)
                squash_x = 1.0 + music_bob * 0.012
                squash_y = 1.0 - music_bob * 0.012
                float_y = -abs(music_bob) * 3.0
                extra_rot = 0.0
        elif is_speaking:
            # When animated GIF is active, preserve 100% authentic hand-crafted animation frames
            if self._talk_frames:
                squash_x = 1.0
                squash_y = 1.0
                float_y = 0.0
                extra_rot = 0.0
            else:
                talk_bob = math.sin(model.pulse_phase * 2.8)
                squash_x = 1.0 - talk_bob * 0.032
                squash_y = 1.0 + talk_bob * 0.032
                float_y = -abs(talk_bob) * 2.4
                extra_rot = math.sin(model.pulse_phase * 1.4) * 1.8
        else:
            # Calm rhythmic breathing
            breath = math.sin(model.pulse_phase * 1.5)
            squash_x = 1.0 + breath * 0.024
            squash_y = 1.0 - breath * 0.022
            float_y = breath * 1.4

        cx = base_cx + cling_dx + shake_x
        cy = (height / 2.0) + 2.0 + float_y + cling_dy

        painter.save()
        total_rot = cling_rot + extra_rot
        if abs(total_rot) > 0.01:
            painter.translate(cx, cy)
            painter.rotate(total_rot)
            painter.translate(-cx, -cy)

        bottom_anchor = cy + 42.0
        painter.translate(cx, bottom_anchor)
        painter.scale(squash_x, squash_y)
        painter.translate(-cx, -bottom_anchor)

        # 0. Soft Angel Halo & State-Specific Aura
        self._draw_shadow_and_aura(
            painter, cx, cy, model.pulse_phase,
            is_speaking, is_music, is_dragging_or_dizzy, is_waking_up
        )

        # 1. Draw Main Character Sprite (distinct per state!)
        active_pm = self._select_active_pixmap(
            model, is_speaking, is_music, is_dragging_or_dizzy, is_waking_up, now
        )
        if active_pm is not None and not active_pm.isNull():
            target_size = 98.0
            scaled = active_pm.scaled(
                int(target_size), int(target_size),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            draw_x = cx - scaled.width() / 2.0
            draw_y = cy - scaled.height() / 2.0
            painter.drawPixmap(int(draw_x), int(draw_y), scaled)

            # State-specific animated hands & props overlays:
            if is_dragging_or_dizzy:
                self._draw_dragging_hands_and_sweat(painter, cx, cy, now)
            elif is_waking_up:
                self._draw_wakeup_hands_and_shock(painter, cx, cy, now)
        else:
            self._draw_vector_fallback(painter, cx, cy, model, is_speaking, is_music, is_dragging_or_dizzy, is_waking_up)

        # 2. Floating Angel & Star Sparkles around her Halo & Wing Hairpin
        if not model.is_sleeping and not is_dragging_or_dizzy:
            self._draw_idol_sparkles(painter, cx, cy, model.pulse_phase, is_music or is_speaking)

        # 3. Sleeping Snot Bubble ('Bong bóng mũi') OR 'Póc!' Pop Burst Effect
        nose_x = cx + 2.0
        nose_y = cy + 16.0
        if model.is_sleeping:
            self._draw_snot_bubble(painter, nose_x, nose_y, model.pulse_phase)
        elif is_popping_bubble or model.bubble_pop_particles:
            self._draw_bubble_pop_effect(painter, nose_x, nose_y, model, now)

        painter.restore()

        # 4. Unscaled Overlays: Floating zZz when sleeping
        if model.is_sleeping and model.zzz_particles:
            self._draw_zzz_particles(painter, model.zzz_particles)

    def _select_active_pixmap(
        self,
        model: MascotModel,
        is_speaking: bool,
        is_music: bool,
        is_dragging_or_dizzy: bool,
        is_waking_up: bool,
        now: float = 0.0,
    ) -> Optional[QPixmap]:
        if model.is_sleeping:
            return self._sleep_pm or self._idle_pm
        if is_dragging_or_dizzy:
            return self._drag_pm or self._idle_pm
        if is_waking_up:
            return self._wakeup_pm or self._idle_pm
        if is_music:
            # Animated GIF: `> <` eyes + waving 2 glowing concert lightsticks when music/YT plays!
            if self._music_frames:
                frame = self._get_animated_frame(self._music_frames, self._music_delays, self._music_total_time, now)
                if frame is not None:
                    return frame
            return self._music_pm or self._idle_pm
        if is_speaking:
            # Animated GIF: Starry golden eyes with talking mouth and motion!
            if self._talk_frames:
                frame = self._get_animated_frame(self._talk_frames, self._talk_delays, self._talk_total_time, now)
                if frame is not None:
                    return frame
            if model.is_blinking and math.sin(model.blink_phase) > 0.65:
                return self._blink_pm or self._idle_pm
            if model.mouth_open > 0.58:
                return self._talk_open_pm or self._idle_pm
            if model.mouth_open > 0.22:
                return self._talk_half_pm or self._idle_pm
            return self._idle_pm
        if model.is_blinking and math.sin(model.blink_phase) > 0.55:
            return self._blink_pm or self._idle_pm
        if model.is_drowsy and model.drowsy_ratio > 0.65:
            return self._blink_pm or self._idle_pm
        return self._idle_pm

    # ============================================================
    # DISTINCT HANDS & EFFECTS FOR DRAGGING & WAKING UP
    # ============================================================

    def _draw_dragging_hands_and_sweat(self, painter: QPainter, cx: float, cy: float, now: float):
        """Draws 2 round Chibi paw hands flailing in mid-air + flying panic sweat drops when dragged."""
        painter.save()
        wave = math.sin(now * 26.0) * 5.5
        hand_positions = [
            (cx - 28.0, cy + 16.0 + wave),
            (cx + 28.0, cy + 16.0 - wave),
        ]
        for hx, hy in hand_positions:
            painter.setBrush(QBrush(QColor("#FDECE6")))
            painter.setPen(QPen(QColor("#E16B7C"), 2.0))
            painter.drawEllipse(QRectF(hx - 6.5, hy - 6.5, 13.0, 13.0))

        sweat_bob = (now * 8.0) % 1.0
        painter.setBrush(QBrush(QColor(56, 189, 248, int(230 * (1.0 - sweat_bob * 0.5)))))
        painter.setPen(QPen(QColor("#0284C7"), 1.1))
        painter.drawEllipse(QRectF(cx - 38.0 - sweat_bob * 4.0, cy - 10.0 + sweat_bob * 5.0, 4.5, 6.8))
        painter.drawEllipse(QRectF(cx + 34.0 + sweat_bob * 4.0, cy - 14.0 + sweat_bob * 5.0, 4.5, 6.8))
        painter.restore()

    def _draw_wakeup_hands_and_shock(self, painter: QPainter, cx: float, cy: float, now: float):
        """Draws one round paw rubbing her sleepy eye and one startled paw + '!' shock rays when woken up."""
        painter.save()
        rub = math.sin(now * 16.0) * 2.2
        hands = [
            (cx - 19.0 + rub, cy + 15.0),
            (cx + 25.0, cy + 20.0 - abs(rub)),
        ]
        for hx, hy in hands:
            painter.setBrush(QBrush(QColor("#FDECE6")))
            painter.setPen(QPen(QColor("#E16B7C"), 2.0))
            painter.drawEllipse(QRectF(hx - 6.2, hy - 6.2, 12.4, 12.4))

        ray_pen = QPen(QColor("#F59E0B"), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(ray_pen)
        painter.drawLine(QPointF(cx - 10.0, cy - 36.0), QPointF(cx - 14.0, cy - 42.0))
        painter.drawLine(QPointF(cx, cy - 38.0), QPointF(cx, cy - 45.0))
        painter.drawLine(QPointF(cx + 10.0, cy - 36.0), QPointF(cx + 14.0, cy - 42.0))
        painter.restore()

    # ============================================================
    # AURA, LIGHTSTICK GLOW & SPARKLE EFFECTS
    # ============================================================

    def _draw_shadow_and_aura(
        self,
        painter: QPainter,
        cx: float,
        cy: float,
        pulse_phase: float,
        is_speaking: bool,
        is_music: bool,
        is_dragging_or_dizzy: bool,
        is_waking_up: bool,
    ):
        pulse = (math.sin(pulse_phase * (3.6 if is_music else 1.8)) + 1.0) / 2.0
        grad = QRadialGradient(cx, cy, 48.0 + pulse * 5.0)
        if is_dragging_or_dizzy:
            grad.setColorAt(0.0, QColor(251, 113, 133, int(90 + pulse * 40)))
            grad.setColorAt(0.6, QColor(251, 191, 36, int(35 + pulse * 20)))
        elif is_waking_up:
            grad.setColorAt(0.0, QColor(253, 224, 71, int(95 + pulse * 40)))
            grad.setColorAt(0.6, QColor(56, 189, 248, int(40 + pulse * 25)))
        elif is_music:
            grad.setColorAt(0.0, QColor(251, 207, 232, int(80 + pulse * 28)))
            grad.setColorAt(0.6, QColor(244, 114, 182, int(35 + pulse * 18)))
        elif is_speaking:
            # Warm golden-star & pastel pink aura when speaking
            grad.setColorAt(0.0, QColor(251, 207, 232, int(90 + pulse * 35)))
            grad.setColorAt(0.6, QColor(253, 224, 71, int(45 + pulse * 25)))
        else:
            grad.setColorAt(0.0, QColor(251, 207, 232, int(75 + pulse * 30)))
            grad.setColorAt(0.6, QColor(125, 211, 252, int(35 + pulse * 20)))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))

        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - 52, cy - 50, 104, 100))

        sh_grad = QRadialGradient(cx, cy + 43.0, 28.0)
        sh_grad.setColorAt(0.0, QColor(45, 20, 30, 65))
        sh_grad.setColorAt(0.7, QColor(45, 20, 30, 20))
        sh_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(sh_grad))
        painter.drawEllipse(QRectF(cx - 28, cy + 39.0, 56, 8.5))

    def _draw_idol_sparkles(self, painter: QPainter, cx: float, cy: float,
                            pulse_phase: float, is_active: bool):
        """Twinkling 4-point golden & sky-blue stars around her angel halo and wing hairpin."""
        s1 = 2.8 + (math.sin(pulse_phase * 2.8) + 1.0) * 1.1
        s2 = 2.4 + (math.cos(pulse_phase * 3.1) + 1.0) * 1.0
        self._draw_four_point_star(painter, cx + 34.0, cy - 12.0, s1, QColor("#FBBF24"))
        self._draw_four_point_star(painter, cx - 35.0, cy - 22.0, s2, QColor("#7DD3FC"))
        if is_active:
            s3 = 3.2 + (math.sin(pulse_phase * 4.5 + 1.0) + 1.0) * 1.2
            self._draw_four_point_star(painter, cx - 32.0, cy - 2.0, s3, QColor("#E879F9"))
            self._draw_four_point_star(painter, cx + 36.0, cy + 2.0, s3, QColor("#FB7185"))

    @staticmethod
    def _draw_four_point_star(painter: QPainter, cx: float, cy: float, size: float, color: QColor):
        painter.save()
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
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

    def _draw_state_speech_tag(
        self,
        painter: QPainter,
        cx: float,
        top_y: float,
        pulse_phase: float,
        text: str,
        bg_col: QColor,
        border_col: QColor,
        text_col: QColor,
    ):
        painter.save()
        bob = math.sin(pulse_phase * 4.2) * 2.0
        w = max(56.0, len(text) * 6.4)
        pill_rect = QRectF(cx - w / 2.0, max(2.0, top_y - 6.0 + bob), w, 16.0)
        painter.setBrush(QBrush(bg_col))
        painter.setPen(QPen(border_col, 1.4))
        painter.drawRoundedRect(pill_rect, 8.0, 8.0)

        font = QFont("Arial", 8, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(text_col)
        painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()

    # ============================================================
    # SLEEP SNOT BUBBLE & POP EFFECTS
    # ============================================================

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
            painter.setPen(QPen(QColor(236, 72, 153, alpha), 2.0, Qt.PenStyle.DashLine))
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
        for p in particles:
            alpha = max(0, min(255, int(p.get("alpha", 200))))
            painter.setPen(QColor(236, 72, 153, alpha))
            painter.drawText(QPointF(p["x"], p["y"]), p.get("char", "z"))
        painter.restore()

    # ============================================================
    # PROCEDURAL VECTOR FALLBACK (IF PNG FILES ARE MISSING)
    # ============================================================

    def _draw_vector_fallback(
        self,
        painter: QPainter,
        cx: float,
        cy: float,
        model: MascotModel,
        is_speaking: bool,
        is_music: bool,
        is_dragging_or_dizzy: bool,
        is_waking_up: bool,
    ):
        """Procedural fallback matching the Chibi Pink Angel Idol design across states."""
        outline = QColor("#A85865")
        painter.setBrush(QBrush(QColor(186, 230, 253, 210)))
        painter.setPen(QPen(QColor("#5A9BD5"), 1.6))
        painter.drawEllipse(QRectF(cx - 34, cy - 42, 68, 22))

        painter.setBrush(QBrush(QColor("#F5B8C4")))
        painter.setPen(QPen(outline, 1.8))
        painter.drawEllipse(QRectF(cx - 32, cy - 32, 64, 58))

        painter.setBrush(QBrush(QColor("#FDECE6")))
        painter.setPen(QPen(QColor("#E16B7C"), 1.8))
        painter.drawEllipse(QRectF(cx - 26, cy - 16, 52, 42))

        if is_music:
            lash_pen = QPen(QColor("#481B16"), 2.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(lash_pen)
            painter.drawLine(QPointF(cx - 18, cy + 1), QPointF(cx - 8, cy + 6))
            painter.drawLine(QPointF(cx - 18, cy + 11), QPointF(cx - 8, cy + 6))
            painter.drawLine(QPointF(cx + 18, cy + 1), QPointF(cx + 8, cy + 6))
            painter.drawLine(QPointF(cx + 18, cy + 11), QPointF(cx + 8, cy + 6))
        elif is_dragging_or_dizzy:
            for ex in (cx - 13, cx + 13):
                painter.setBrush(QBrush(QColor("#FFFFFF")))
                painter.setPen(QPen(QColor("#481B16"), 2.0))
                painter.drawEllipse(QRectF(ex - 7, cy - 2, 14, 14))
        elif is_waking_up:
            for ex in (cx - 13, cx + 13):
                painter.setBrush(QBrush(QColor("#FFFFFF")))
                painter.setPen(QPen(QColor("#481B16"), 2.2))
                painter.drawEllipse(QRectF(ex - 7.5, cy - 2.5, 15, 15))
                self._draw_four_point_star(painter, ex, cy + 5, 3.5, QColor("#F59E0B"))
        else:
            for ex in (cx - 13, cx + 13):
                painter.setBrush(QBrush(QColor("#9A6B32")))
                painter.setPen(QPen(QColor("#481B16"), 2.0))
                painter.drawEllipse(QRectF(ex - 7, cy - 2, 14, 15))
                self._draw_four_point_star(painter, ex, cy + 6, 4.5, QColor("#FDE68A"))
