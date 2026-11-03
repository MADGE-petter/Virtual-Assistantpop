"""Phrolova Renderer - High-FPS Animated GIF & Sprite Renderer for 'Phrolova (Ponova)'.

Authentic Expressions & Animations per State:
1. IDLE (`idle.gif` - 21 frames):
   - Front-facing Chibi Phrolova with silver-mint hair swaying gently, blinking eyes, and gothic red dress.
2. SPEAKING / TALKING (`talk.gif` - 5 frames):
   - Chibi Phrolova looking slightly to the side, nodding head and talking expressively.
3. PLAYING MUSIC / YOUTUBE (`music.png`):
   - Official emote of Phrolova passionately playing the violin with musical notes floating around!
4. DRAGGING / CHEERING (`drag.gif` - 12 frames):
   - Chibi Phrolova pumping both clenched fists excitedly with happy closed eyes!
5. SLEEPING:
   - Peaceful closed eyes resting pose with floating zZz and breathing bubble.
"""

import math
import os
import time
from typing import Optional, List, Tuple
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QPixmap, QImage, QImageReader, QColor, QBrush, QPen,
    QRadialGradient, QPainterPath
)
from model.voice_state_model import VoiceState
from utils.paths import resource_path
from view.ui.mascot.characters.base_character_renderer import BaseCharacterRenderer
from view.ui.mascot.mascot_model import MascotModel


class PhrolovaRenderer(BaseCharacterRenderer):
    """Renders Phrolova (Ponova) with authentic 100% hand-crafted GIF frame sequences."""

    def __init__(self, skin_dir: Optional[str] = None):
        self.skin_dir = skin_dir or resource_path(os.path.join("skins", "phrolova"))
        self._idle_pm: Optional[QPixmap] = None
        self._talk_pm: Optional[QPixmap] = None
        self._drag_pm: Optional[QPixmap] = None
        self._music_pm: Optional[QPixmap] = None
        self._sleep_pm: Optional[QPixmap] = None
        self._wakeup_pm: Optional[QPixmap] = None

        # Animated GIF sequences
        self._idle_frames: List[QPixmap] = []
        self._idle_delays: List[float] = []
        self._idle_total_time: float = 0.0

        self._talk_frames: List[QPixmap] = []
        self._talk_delays: List[float] = []
        self._talk_total_time: float = 0.0

        self._drag_frames: List[QPixmap] = []
        self._drag_delays: List[float] = []
        self._drag_total_time: float = 0.0

        self._music_frames: List[QPixmap] = []
        self._music_delays: List[float] = []
        self._music_total_time: float = 0.0

        self._load_sprites()

    @staticmethod
    def _load_gif_frames(gif_path: str) -> Tuple[List[QPixmap], List[float], float]:
        frames: List[QPixmap] = []
        delays: List[float] = []
        total_time = 0.0
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
                d_ms = 70
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
        idle_gif = os.path.join(self.skin_dir, "idle.gif")
        talk_gif = os.path.join(self.skin_dir, "talk.gif")
        drag_gif = os.path.join(self.skin_dir, "drag.gif")
        music_gif = os.path.join(self.skin_dir, "music.gif")
        music_png = os.path.join(self.skin_dir, "music.png")

        idle_png = os.path.join(self.skin_dir, "idle.png")
        talk_png = os.path.join(self.skin_dir, "talk.png")
        drag_png = os.path.join(self.skin_dir, "drag.png")

        # 1. Idle frames
        if os.path.isfile(idle_gif):
            self._idle_frames, self._idle_delays, self._idle_total_time = self._load_gif_frames(idle_gif)
            if self._idle_frames:
                self._idle_pm = self._idle_frames[0]
                # Frame 4 has closed eyes for sleeping
                if len(self._idle_frames) > 4:
                    self._sleep_pm = self._idle_frames[4]
                else:
                    self._sleep_pm = self._idle_frames[0]
        elif os.path.isfile(idle_png):
            self._idle_pm = QPixmap(idle_png)
            self._sleep_pm = self._idle_pm

        # 2. Talk frames
        if os.path.isfile(talk_gif):
            self._talk_frames, self._talk_delays, self._talk_total_time = self._load_gif_frames(talk_gif)
            if self._talk_frames:
                self._talk_pm = self._talk_frames[0]
        elif os.path.isfile(talk_png):
            self._talk_pm = QPixmap(talk_png)

        # 3. Drag / Cheer frames
        if os.path.isfile(drag_gif):
            self._drag_frames, self._drag_delays, self._drag_total_time = self._load_gif_frames(drag_gif)
            if self._drag_frames:
                self._drag_pm = self._drag_frames[0]
        elif os.path.isfile(drag_png):
            self._drag_pm = QPixmap(drag_png)

        # 4. Music GIF & PNG (violin performance)
        if os.path.isfile(music_gif):
            self._music_frames, self._music_delays, self._music_total_time = self._load_gif_frames(music_gif)
            if self._music_frames:
                self._music_pm = self._music_frames[0]
        elif os.path.isfile(music_png):
            pm = QPixmap(music_png)
            if not pm.isNull():
                self._music_pm = pm

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

        extra_rot = 0.0
        shake_x = 0.0
        float_y = 0.0
        squash_x = 1.0
        squash_y = 1.0

        if model.is_sleeping and not is_clinging:
            breath = math.sin(model.pulse_phase * 1.3)
            squash_x = 1.05 + breath * 0.02
            squash_y = 0.95 - breath * 0.02
            float_y = 4.0
        elif is_dragging_or_dizzy:
            # Wiggle during drag
            wiggle = math.sin(now * 20.0)
            extra_rot = wiggle * 4.0
            float_y = math.sin(now * 16.0) * 2.0
        elif is_waking_up:
            jump = abs(math.sin(now * 14.0)) * 6.0
            float_y = -jump
        elif is_music:
            # Gentle rhythmic violin sway
            music_bob = math.sin(model.pulse_phase * 3.0)
            float_y = -abs(music_bob) * 2.5
            extra_rot = math.sin(model.pulse_phase * 1.5) * 1.5
        elif is_speaking:
            # Handled by talk.gif frames
            float_y = 0.0
        else:
            # Handled by idle.gif frames
            float_y = 0.0

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

        # 0. Soft Crimson / Gothic Rose Aura & Shadow
        self._draw_shadow_and_aura(
            painter, cx, cy, model.pulse_phase,
            is_speaking, is_music, is_dragging_or_dizzy, is_waking_up
        )

        # 0.5. Background Acoustic Sound Waves (when playing music)
        if is_music:
            self._draw_music_soundwaves(painter, cx, cy, now)

        # 1. Draw Active Sprite
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

        # 1.5. Foreground Floating Notes & Twinkling Sparkles (when playing music)
        if is_music:
            self._draw_music_notes_and_sparkles(painter, cx, cy, now)

        # 2. Sleeping Snot Bubble OR Pop Effect
        nose_x = cx + 2.0
        nose_y = cy + 16.0
        if model.is_sleeping:
            self._draw_snot_bubble(painter, nose_x, nose_y, model.pulse_phase)
        elif is_popping_bubble or model.bubble_pop_particles:
            self._draw_bubble_pop_effect(painter, nose_x, nose_y, model, now)

        painter.restore()

        # 3. Floating zZz when sleeping
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
            # Pumping clenched fists cheer GIF!
            if self._drag_frames:
                frame = self._get_animated_frame(self._drag_frames, self._drag_delays, self._drag_total_time, now)
                if frame:
                    return frame
            return self._drag_pm or self._idle_pm
        if is_music:
            # Animated violin performance GIF!
            if self._music_frames:
                frame = self._get_animated_frame(self._music_frames, self._music_delays, self._music_total_time, now)
                if frame:
                    return frame
            return self._music_pm or self._idle_pm
        if is_speaking:
            # Chibi nodding & talking GIF
            if self._talk_frames:
                frame = self._get_animated_frame(self._talk_frames, self._talk_delays, self._talk_total_time, now)
                if frame:
                    return frame
            return self._talk_pm or self._idle_pm
        # Default Idle: hair sway & blinking GIF
        if self._idle_frames:
            frame = self._get_animated_frame(self._idle_frames, self._idle_delays, self._idle_total_time, now)
            if frame:
                return frame
        return self._idle_pm

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
            grad.setColorAt(0.0, QColor(244, 63, 94, int(85 + pulse * 35)))
            grad.setColorAt(0.6, QColor(251, 146, 60, int(30 + pulse * 20)))
        elif is_music:
            # Gothic crimson-ruby & violet violin aura
            grad.setColorAt(0.0, QColor(225, 29, 72, int(85 + pulse * 30)))
            grad.setColorAt(0.6, QColor(168, 85, 247, int(35 + pulse * 18)))
        elif is_speaking:
            grad.setColorAt(0.0, QColor(244, 63, 94, int(75 + pulse * 30)))
            grad.setColorAt(0.6, QColor(253, 224, 71, int(30 + pulse * 15)))
        else:
            grad.setColorAt(0.0, QColor(244, 63, 94, int(60 + pulse * 20)))
            grad.setColorAt(0.6, QColor(225, 29, 72, int(20 + pulse * 10)))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))

        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - 50, cy - 48, 100, 96))

        # Soft contact ground shadow
        sh_grad = QRadialGradient(cx, cy + 42.0, 26.0)
        sh_grad.setColorAt(0.0, QColor(40, 15, 25, 60))
        sh_grad.setColorAt(0.7, QColor(40, 15, 25, 18))
        sh_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(sh_grad))
        painter.drawEllipse(QRectF(cx - 26, cy + 38.0, 52, 8.0))

    def _draw_snot_bubble(self, painter: QPainter, bx: float, by: float, pulse_phase: float):
        r_scale = 0.55 + 0.45 * (math.sin(pulse_phase * 1.3) + 1.0) / 2.0
        rad = 8.5 * r_scale
        if rad < 2.0:
            return

        b_grad = QRadialGradient(bx - rad * 0.3, by - rad * 0.3, rad)
        b_grad.setColorAt(0.0, QColor(255, 255, 255, 225))
        b_grad.setColorAt(0.6, QColor(225, 29, 72, 110))
        b_grad.setColorAt(1.0, QColor(159, 18, 57, 180))

        painter.setBrush(QBrush(b_grad))
        painter.setPen(QPen(QColor("#BE123C"), 1.0))
        painter.drawEllipse(QPointF(bx, by), rad, rad)

    def _draw_bubble_pop_effect(self, painter: QPainter, bx: float, by: float, model: MascotModel, now: float):
        for p in model.bubble_pop_particles:
            age = now - p.get("created", now)
            dur = p.get("duration", 0.3)
            progress = min(1.0, age / dur) if dur > 0 else 1.0
            alpha = int(220 * (1.0 - progress))
            if alpha <= 0:
                continue

            dist = 4.0 + progress * 16.0
            ang = p.get("angle", 0.0)
            px = bx + math.cos(ang) * dist
            py = by + math.sin(ang) * dist
            sz = p.get("size", 2.5) * (1.0 - progress * 0.5)

            painter.setBrush(QBrush(QColor(225, 29, 72, alpha)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(px - sz, py - sz, sz * 2, sz * 2))

    def _draw_zzz_particles(self, painter: QPainter, particles: list):
        painter.save()
        for p in particles:
            sz = p.get("size", 10.0)
            color = p.get("color", QColor("#F43F5E"))
            painter.setPen(color)
            font = painter.font()
            font.setPointSize(int(sz))
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(int(p["x"]), int(p["y"]), "z")
        painter.restore()

    def _draw_music_soundwaves(self, painter: QPainter, cx: float, cy: float, now: float):
        """Draws concentric acoustic resonant soundwaves expanding from the violin."""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        vx = cx + 8.0
        vy = cy + 12.0
        for i in range(3):
            t = (now * 1.3 + i * 0.33) % 1.0
            rx = 16.0 + t * 46.0
            ry = 10.0 + t * 28.0
            alpha = int(160 * (1.0 - t) * (1.0 - t))
            if alpha > 8:
                pen = QPen(QColor(244, 63, 94, alpha), max(0.8, 2.0 - t * 1.2))
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QPointF(vx, vy), rx, ry)
        painter.restore()

    def _draw_music_notes_and_sparkles(self, painter: QPainter, cx: float, cy: float, now: float):
        """Draws floating animated musical notes and twinkling gothic star sparkles."""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Twinkling 4-point star sparkles
        sparkles = [
            (-44.0, -28.0, 0.0),
            (42.0, -22.0, 0.28),
            (-36.0, 20.0, 0.55),
            (40.0, 14.0, 0.78),
            (-14.0, -42.0, 0.42),
            (16.0, -44.0, 0.88),
        ]
        for sx_off, sy_off, s_phase in sparkles:
            twinkle = (math.sin(now * 4.2 + s_phase * 6.28) + 1.0) / 2.0
            if twinkle > 0.15:
                s_sz = 1.8 + twinkle * 3.6
                s_alpha = int(220 * twinkle)
                px = cx + sx_off
                py = cy + sy_off
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(253, 224, 71, s_alpha)))
                star_path = QPainterPath()
                star_path.moveTo(px, py - s_sz)
                star_path.quadTo(px, py, px + s_sz, py)
                star_path.quadTo(px, py, px, py + s_sz)
                star_path.quadTo(px, py, px - s_sz, py)
                star_path.quadTo(px, py, px, py - s_sz)
                painter.drawPath(star_path)

        # 2. Floating Animated Musical Notes (♪, ♫, ♬, ♩)
        notes = [
            ("♪", -32.0, 0.0, 15, QColor(244, 63, 94)),
            ("♫", 28.0, 0.22, 17, QColor(253, 164, 175)),
            ("♬", -20.0, 0.48, 14, QColor(245, 158, 11)),
            ("♩", 36.0, 0.72, 13, QColor(244, 63, 94)),
            ("♫", -6.0, 0.38, 16, QColor(253, 164, 175)),
            ("♪", 18.0, 0.86, 14, QColor(251, 191, 36)),
        ]
        font = painter.font()
        for glyph, base_dx, time_off, f_size, col in notes:
            t = (now * 0.75 + time_off) % 1.0
            nx = cx + base_dx + math.sin(now * 3.2 + time_off * 6.28) * 8.5
            ny = cy + 12.0 - t * 65.0
            alpha = int(240 * math.sin(t * math.pi))
            if alpha > 12:
                font.setPixelSize(f_size)
                font.setBold(True)
                painter.setFont(font)
                painter.setPen(QColor(255, 255, 255, int(alpha * 0.65)))
                painter.drawText(int(nx - 1), int(ny - 1), glyph)
                painter.setPen(QColor(col.red(), col.green(), col.blue(), alpha))
                painter.drawText(int(nx), int(ny), glyph)

        painter.restore()

