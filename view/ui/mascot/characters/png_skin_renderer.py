"""PNG Skin Renderer - Renders custom user/community characters from sprite frames & PNG assets."""

import math
import os
import time
from typing import Dict, List, Optional
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPixmap, QColor, QFont
from model.voice_state_model import VoiceState
from view.ui.mascot.characters.base_character_renderer import BaseCharacterRenderer
from view.ui.mascot.mascot_model import MascotModel


class PngSkinRenderer(BaseCharacterRenderer):
    """Renders sprite-based mascot skins with animated frame sequences, breathing physics, and state transitions."""

    def __init__(self, skin_dir: str):
        self.skin_dir = skin_dir
        self._pixmaps: Dict[str, Optional[QPixmap]] = {}
        self._animations: Dict[str, List[QPixmap]] = {}
        self._load_sprites()

    def _load_sprites(self):
        # 1. Load single state files (fallback)
        for state in ("idle", "blink", "talk", "sleep", "dizzy"):
            path = os.path.join(self.skin_dir, f"{state}.png")
            if os.path.isfile(path):
                pm = QPixmap(path)
                if not pm.isNull():
                    self._pixmaps[state] = pm
                else:
                    self._pixmaps[state] = None
            else:
                self._pixmaps[state] = None

        # 2. Load animated frame sequences from frames/<state>/
        frames_base = os.path.join(self.skin_dir, "frames")
        if os.path.isdir(frames_base):
            for state in ("idle", "talk", "dizzy", "sleep", "blink"):
                state_dir = os.path.join(frames_base, state)
                if os.path.isdir(state_dir):
                    frame_files = sorted([
                        f for f in os.listdir(state_dir)
                        if f.lower().endswith(".png")
                    ])
                    loaded_frames = []
                    for f in frame_files:
                        pm = QPixmap(os.path.join(state_dir, f))
                        if not pm.isNull():
                            loaded_frames.append(pm)
                    if loaded_frames:
                        self._animations[state] = loaded_frames

    def _get_active_pixmap(self, model: MascotModel) -> Optional[QPixmap]:
        idle = self._pixmaps.get("idle")
        now = time.time()

        # Xác định trạng thái hiện tại & tốc độ khung hình (FPS)
        if model.is_sleeping:
            state = "sleep"
            fps = 1.8  # Thở chậm khi ngủ
        elif model.is_dragging or now < model.dizzy_end_time:
            state = "dizzy"
            fps = 7.0  # Lắc lư chóng mặt nhanh
        elif model.voice_state == VoiceState.SPEAKING and model.mouth_open > 0.2:
            state = "talk"
            fps = 5.5  # Nhịp nhép miệng khi nói
        else:
            state = "idle"
            fps = 4.0  # Nhai cam / nhún nhảy tự nhiên

        # 1. Kiểm tra chuỗi frames chuyển động
        frames = self._animations.get(state)
        if frames:
            frame_idx = int(now * fps) % len(frames)
            return frames[frame_idx]

        # 2. Fallback sang ảnh đơn
        active_single = self._pixmaps.get(state)
        if active_single:
            return active_single

        # 3. Fallback sang blink nếu có
        if model.is_blinking and self._pixmaps.get("blink"):
            return self._pixmaps.get("blink")

        # 4. Fallback cuối cùng sang idle
        idle_frames = self._animations.get("idle")
        if idle_frames:
            frame_idx = int(now * 4.0) % len(idle_frames)
            return idle_frames[frame_idx]

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

        now = time.time()
        is_dizzy = model.is_dragging or now < model.dizzy_end_time

        # Hiệu ứng lắc lư chóng mặt khi bị kéo hoặc vừa kéo xong
        dizzy_shake = math.sin(now * 18.0) * 3.0 if is_dizzy else 0.0

        float_speed = 0.4 if model.is_sleeping else 1.2
        float_y = math.sin(model.pulse_phase) * float_speed

        cx = base_cx + cling_dx + dizzy_shake
        cy = (height / 2.0) + float_y + cling_dy

        painter.save()
        total_rot = cling_rot + (math.sin(now * 14.0) * 4.0 if is_dizzy else 0.0)
        if abs(total_rot) > 0.01:
            painter.translate(cx, cy)
            painter.rotate(total_rot)
            painter.translate(-cx, -cy)

        pm = self._get_active_pixmap(model)
        target_size = 85.0  # Kích thước vừa vặn trong khung mascot 120x120
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
            # Fallback nếu thiếu hình ảnh
            painter.setBrush(QColor(100, 116, 139))
            painter.drawEllipse(QRectF(cx - 30, cy - 30, 60, 60))

        # Hạt zZz khi ngủ
        if model.is_sleeping and model.zzz_particles:
            font = QFont("Arial", 11, QFont.Weight.Bold)
            painter.setFont(font)
            for p in model.zzz_particles:
                alpha = max(0, min(255, int(p.get("alpha", 200))))
                painter.setPen(QColor(56, 189, 248, alpha))
                painter.drawText(QPointF(p["x"], p["y"]), p.get("char", "z"))

        painter.restore()
