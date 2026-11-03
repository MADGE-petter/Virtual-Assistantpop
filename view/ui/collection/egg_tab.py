"""
Egg Tab - 2-Page Banner Poster System & Full-Screen 3D Atomic Core Summon Stage.
- Default View: 2 switchable Banner Pages (Paper 1: Phoebe Chupi, Paper 2: Nono Phruonuo)
  with a clean unified Bottom Action Toolbar (Điểm Danh, Nạp Lõi +1/+5, Triệu Hồi x1/x5).
- Summon View: When rolling x1 or x5, switches to a 100% Full-Screen stage featuring the
  original 3D spinning atomic core (3D perspective orbitals + half-white/half-blue Rasengan sphere).
"""

import math
from datetime import date
from typing import Optional, List, Dict, Any
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QLinearGradient, QRadialGradient, QFont
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFrame, QMessageBox, QStackedWidget
)
from service.collection.character_registry import RARITY_INFO, RARITY_ORDER, CharacterDef
from service.collection.collection_service import CollectionService, OpenResult, EGG_PRICE
from view.ui.collection.character_preview_widget import CharacterPreviewWidget
from view.ui.mascot.characters import create_renderer_for_character
from view.ui.mascot.characters.base_character_renderer import BaseCharacterRenderer
from view.ui.mascot.mascot_model import MascotModel


class GachaStageWidget(QWidget):
    """
    Full-Screen 3D Atomic Core Summon Stage (Hidden until the user triggers a summon).
    Preserves the original 3D perspective atomic core with 4 3D orbitals,
    half-white/half-blue rotating Rasengan core, white-hot energy flash, and full-screen character reveal.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 420)
        self.phase: float = 0.0

        # State machine: "IDLE" | "SPINNING" | "FLASH" | "REVEALED"
        self.state: str = "IDLE"
        self.aura_color: QColor = QColor(0, 210, 255)  # Màu xanh Rasengan chuẩn anime

        # Animation timers
        self.spin_timer: float = 0.0
        self.spin_duration: float = 1.5   # 1.5s fast spin
        self.flash_timer: float = 0.0
        self.flash_duration: float = 0.32 # 0.32s bright flash
        self.reveal_bounce: float = 0.0

        self._current_results: List[OpenResult] = []
        self._renderers: List[BaseCharacterRenderer] = []
        self._mascot_model: MascotModel = MascotModel()
        self._on_finish_callback = None

        # 4 Quỹ đạo 3D phân bổ đều 4 hướng (Ngang, Dọc, Chéo 1, Chéo 2)
        self.orbitals: List[Dict[str, Any]] = [
            {"type": "horizontal", "speed": 1.25, "offset": 0.0,           "radius": 76.0},
            {"type": "vertical",   "speed": 1.25, "offset": math.pi * 0.5, "radius": 84.0},
            {"type": "diag_a",     "speed": 1.25, "offset": math.pi * 1.0, "radius": 72.0},
            {"type": "diag_b",     "speed": 1.25, "offset": math.pi * 1.5, "radius": 78.0},
        ]

        self._timer = QTimer(self)
        self._timer.setInterval(25)  # 40 fps
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    @property
    def is_cracking(self) -> bool:
        return self.state in ("SPINNING", "FLASH")

    @property
    def last_single_result(self) -> Optional[OpenResult]:
        if len(self._current_results) == 1:
            return self._current_results[0]
        return None

    def set_aura_color(self, hex_color: str):
        self.aura_color = QColor(hex_color)
        self.update()

    def start_open_sequence(self, results: List[OpenResult] | OpenResult, on_finish):
        if isinstance(results, OpenResult):
            results = [results]
        self._current_results = results
        self._renderers = [create_renderer_for_character(r.character) for r in results]
        self._on_finish_callback = on_finish

        best_rarity = "common"
        for r in results:
            if RARITY_ORDER.index(r.character.rarity) > RARITY_ORDER.index(best_rarity):
                best_rarity = r.character.rarity

        r_info = RARITY_INFO.get(best_rarity, {})
        self.set_aura_color(r_info.get("color", "#00D2FF"))

        self.state = "SPINNING"
        self.spin_timer = 0.0
        self.flash_timer = 0.0
        self.reveal_bounce = 0.0
        self.update()

    def skip_to_reveal(self):
        if self.state in ("SPINNING", "FLASH"):
            self.state = "REVEALED"
            self.reveal_bounce = 1.0
            if self._on_finish_callback and callable(self._on_finish_callback):
                self._on_finish_callback()
            self.update()

    def reset_to_atom(self):
        self.state = "IDLE"
        self._current_results = []
        self._renderers = []
        self.aura_color = QColor(0, 210, 255)
        self.update()

    def _on_tick(self):
        if not self.isVisible():
            return
        dt = 0.025
        self._mascot_model.pulse_phase += 0.065

        if self.state == "IDLE":
            self.phase += 0.045
        elif self.state == "SPINNING":
            self.spin_timer += dt
            prog = min(1.0, self.spin_timer / self.spin_duration)
            speed_mult = 1.0 + (prog ** 2.2) * 9.0
            self.phase += 0.045 * speed_mult

            if self.spin_timer >= self.spin_duration:
                self.state = "FLASH"
                self.flash_timer = 0.0
        elif self.state == "FLASH":
            self.flash_timer += dt
            self.phase += 0.35
            if self.flash_timer >= self.flash_duration:
                self.state = "REVEALED"
                self.reveal_bounce = 0.0
                if self._on_finish_callback and callable(self._on_finish_callback):
                    self._on_finish_callback()
        elif self.state == "REVEALED":
            self.phase += 0.05
            if self.reveal_bounce < 1.0:
                self.reveal_bounce = min(1.0, self.reveal_bounce + 0.08)

        self.update()

    def paintEvent(self, a0):
        super().paintEvent(a0)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w = float(self.width())
        h = float(self.height())
        cx = w / 2.0
        cy = h / 2.0 - 12.0

        # Full-screen dark backdrop
        painter.setBrush(QBrush(QColor("#181A20")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(QRectF(0.0, 0.0, w, h))

        if self.state in ("IDLE", "SPINNING", "FLASH"):
            self._paint_atomic_core(painter, cx, cy)
            if self.state == "FLASH":
                self._paint_flash(painter, cx, cy)
        elif self.state == "REVEALED":
            if len(self._current_results) == 1:
                self._paint_single_reveal(painter, cx, cy)
            else:
                self._paint_multi_reveal(painter, cx, cy, w, h)

    # ============================================================
    # 1. ORIGINAL 3D ATOMIC CORE WITH AFTERIMAGES & 3D PERSPECTIVE
    # ============================================================
    def _paint_atomic_core(self, painter: QPainter, cx: float, cy: float):
        is_fast = (self.state == "SPINNING")
        speed_mult = 2.2 if is_fast else 1.0

        ar, ag, ab = self.aura_color.red(), self.aura_color.green(), self.aura_color.blue()

        rasengan_r = 25.0
        meteor_head_r = 10.5
        trail_count = 18 if is_fast else 14
        trail_step = 0.05 if is_fast else 0.065
        cam_dist = 250.0

        def calc_meteor_3d(orb_idx: int, theta: float):
            orb = self.orbitals[orb_idx]
            r = orb.get("radius", 76.0)
            orb_type = orb.get("type", "horizontal")

            ct = math.cos(theta)
            st = math.sin(theta)

            if orb_type == "horizontal":
                xw = r * ct
                yw = r * st * 0.38
                zw = r * st * 0.92
            elif orb_type == "vertical":
                xw = r * ct * 0.38
                yw = r * st
                zw = r * ct * 0.92
            elif orb_type == "diag_a":
                xw = r * (ct * 0.7071 + st * 0.27)
                yw = r * (ct * 0.7071 - st * 0.27)
                zw = r * st * 0.92
            else:  # diag_b
                xw = r * (ct * 0.7071 + st * 0.27)
                yw = r * (-ct * 0.7071 + st * 0.27)
                zw = r * st * 0.92

            p_scale = cam_dist / max(40.0, (cam_dist - zw))
            screen_x = cx + xw * p_scale
            screen_y = cy + yw * p_scale
            return (screen_x, screen_y, zw, p_scale)

        meteor_points = []
        for orb_idx, orb in enumerate(self.orbitals):
            head_theta = self.phase * orb["speed"] * speed_mult + orb["offset"]
            for k in range(trail_count, -1, -1):
                t_theta = head_theta - k * trail_step
                px, py, zw, p_scale = calc_meteor_3d(orb_idx, t_theta)
                meteor_points.append((px, py, zw, p_scale, k, orb_idx))

        behind_points = [p for p in meteor_points if p[2] < 0]
        front_points = [p for p in meteor_points if p[2] >= 0]
        behind_points.sort(key=lambda item: item[2])
        front_points.sort(key=lambda item: item[2])

        def draw_meteor_point(px: float, py: float, zw: float, p_scale: float, k: int, in_front: bool):
            if k == 0:
                hr = meteor_head_r * p_scale
                halo_rad = hr * 2.2
                h_grad = QRadialGradient(px, py, halo_rad)
                alpha_core = 250 if in_front else 150
                h_grad.setColorAt(0.0, QColor(255, 255, 255, alpha_core))
                h_grad.setColorAt(0.4, QColor(ar, ag, ab, int(alpha_core * 0.85)))
                h_grad.setColorAt(1.0, QColor(0, 100, 255, 0))
                painter.setBrush(QBrush(h_grad))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(px - halo_rad, py - halo_rad, halo_rad * 2, halo_rad * 2))

                s_grad = QRadialGradient(px - hr * 0.3, py - hr * 0.3, hr * 1.25)
                s_grad.setColorAt(0.0, QColor(255, 255, 255, 255))
                s_grad.setColorAt(0.45, QColor(ar, ag, ab, 240 if in_front else 160))
                s_grad.setColorAt(0.9, QColor(0, 90, 220, 200 if in_front else 130))
                s_grad.setColorAt(1.0, QColor(0, 40, 120, 180 if in_front else 100))
                painter.setBrush(QBrush(s_grad))
                painter.setPen(QPen(QColor(255, 255, 255, 200 if in_front else 120), 0.8))
                painter.drawEllipse(QRectF(px - hr, py - hr, hr * 2, hr * 2))

                painter.setBrush(QBrush(QColor(255, 255, 255, 250 if in_front else 150)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(px - hr * 0.35, py - hr * 0.35, hr * 0.7, hr * 0.7))
            else:
                decay = 1.0 - (k / float(trail_count))
                tr = max(1.0, meteor_head_r * (decay ** 0.8) * p_scale)

                if decay > 0.5:
                    tf = (decay - 0.5) / 0.5
                    cr = int(255 * tf + ar * (1.0 - tf))
                    cg = int(255 * tf + ag * (1.0 - tf))
                    cb = int(255 * tf + ab * (1.0 - tf))
                else:
                    tf = decay / 0.5
                    cr = int(ar * tf + 0 * (1.0 - tf))
                    cg = int(ag * tf + 100 * (1.0 - tf))
                    cb = int(ab * tf + 240 * (1.0 - tf))

                alpha_base = (220 if is_fast else 170) if in_front else 110
                alpha = int(alpha_base * (decay ** 1.3))
                painter.setBrush(QBrush(QColor(cr, cg, cb, alpha)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(px - tr, py - tr, tr * 2, tr * 2))

        # BƯỚC 1: Vẽ các quả cầu / đuôi bay sau lưng (ZW < 0)
        for px, py, zw, p_scale, k, orb_idx in behind_points:
            draw_meteor_point(px, py, zw, p_scale, k, in_front=False)

        # BƯỚC 2: Vẽ quả cầu 3D nửa trắng nửa xanh ở tâm
        aura_rad = rasengan_r * 1.65
        aura_grad = QRadialGradient(cx, cy, aura_rad)
        aura_grad.setColorAt(0.0, QColor(ar, ag, ab, 65 if is_fast else 40))
        aura_grad.setColorAt(0.6, QColor(0, 140, 255, 20))
        aura_grad.setColorAt(1.0, QColor(0, 50, 200, 0))
        painter.setBrush(QBrush(aura_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - aura_rad, cy - aura_rad, aura_rad * 2, aura_rad * 2))

        center_speed = 3.4 * (1.8 if is_fast else 1.0)
        rot_ang = -0.785 + self.phase * center_speed
        cos_rot = math.cos(rot_ang)
        sin_rot = math.sin(rot_ang)

        diag_x1 = cx - rasengan_r * cos_rot
        diag_y1 = cy - rasengan_r * sin_rot
        diag_x2 = cx + rasengan_r * cos_rot
        diag_y2 = cy + rasengan_r * sin_rot

        dual_grad = QLinearGradient(diag_x1, diag_y1, diag_x2, diag_y2)
        dual_grad.setColorAt(0.0, QColor(255, 255, 255, 255))
        dual_grad.setColorAt(0.40, QColor(245, 250, 255, 250))
        dual_grad.setColorAt(0.48, QColor(190, 235, 255, 245))
        dual_grad.setColorAt(0.52, QColor(ar, ag, ab, 245))
        dual_grad.setColorAt(0.82, QColor(0, 110, 240, 230))
        dual_grad.setColorAt(1.0, QColor(10, 30, 80, 220))

        painter.setBrush(QBrush(dual_grad))
        painter.setPen(QPen(QColor(255, 255, 255, 190), 0.8))
        painter.drawEllipse(QRectF(cx - rasengan_r, cy - rasengan_r, rasengan_r * 2, rasengan_r * 2))

        spec_x = cx - rasengan_r * 0.38 * cos_rot
        spec_y = cy - rasengan_r * 0.38 * sin_rot
        spec_r = rasengan_r * 0.62
        spec_grad = QRadialGradient(spec_x, spec_y, spec_r)
        spec_grad.setColorAt(0.0, QColor(255, 255, 255, 220))
        spec_grad.setColorAt(0.5, QColor(255, 255, 255, 70))
        spec_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(spec_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(spec_x - spec_r, spec_y - spec_r, spec_r * 2, spec_r * 2))

        core_r = 5.5
        core_grad = QRadialGradient(cx, cy, core_r)
        core_grad.setColorAt(0.0, QColor(255, 255, 255, 220))
        core_grad.setColorAt(1.0, QColor(ar, ag, ab, 0))
        painter.setBrush(QBrush(core_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - core_r, cy - core_r, core_r * 2, core_r * 2))

        # BƯỚC 3: Vẽ các quả cầu / đuôi bay phía trước (ZW >= 0)
        for px, py, zw, p_scale, k, orb_idx in front_points:
            draw_meteor_point(px, py, zw, p_scale, k, in_front=True)

    # ============================================================
    # 2. ENERGY FLASH (SÁNG BỪNG LÊN KHI MỞ)
    # ============================================================
    def _paint_flash(self, painter: QPainter, cx: float, cy: float):
        t = min(1.0, self.flash_timer / self.flash_duration)
        if t < 0.3:
            intensity = t / 0.3
        else:
            intensity = 1.0 - ((t - 0.3) / 0.7)

        flash_rad = 40.0 + t * 220.0
        grad = QRadialGradient(cx, cy, flash_rad)
        white_alpha = int(255 * intensity)
        aura_alpha = int(220 * intensity)

        grad.setColorAt(0.0, QColor(255, 255, 255, white_alpha))
        grad.setColorAt(0.4, QColor(self.aura_color.red(), self.aura_color.green(), self.aura_color.blue(), aura_alpha))
        grad.setColorAt(1.0, QColor(self.aura_color.red(), self.aura_color.green(), self.aura_color.blue(), 0))

        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - flash_rad, cy - flash_rad, flash_rad * 2, flash_rad * 2))

    # ============================================================
    # 3. REVEALED CHARACTER ON FULL-SCREEN STAGE
    # ============================================================
    def _paint_single_reveal(self, painter: QPainter, cx: float, cy: float):
        res = self._current_results[0]
        char = res.character
        is_new = res.is_new
        shards_gained = res.shards_gained

        r_info = RARITY_INFO.get(char.rarity, {})
        r_col = QColor(r_info.get("color", "#6BA3BE"))
        r_label = r_info.get("label", "Thường")

        float_y = math.sin(self.phase * 2.2) * 3.5
        bounce_scale = 0.75 + 0.25 * math.sin(self.reveal_bounce * math.pi / 2.0)

        halo_rad = 95.0
        h_grad = QRadialGradient(cx, cy - 32.0 + float_y, halo_rad)
        h_grad.setColorAt(0.0, QColor(r_col.red(), r_col.green(), r_col.blue(), 95))
        h_grad.setColorAt(0.6, QColor(r_col.red(), r_col.green(), r_col.blue(), 25))
        h_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(h_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - halo_rad, (cy - 32.0 + float_y) - halo_rad, halo_rad * 2, halo_rad * 2))

        if self._renderers:
            mascot_size = 144.0 * bounce_scale
            scale = mascot_size / 120.0
            painter.save()
            painter.translate(cx - mascot_size / 2.0, (cy - 106.0 + float_y))
            painter.scale(scale, scale)
            try:
                self._renderers[0].paint(painter, 120, 120, self._mascot_model)
            except Exception as e:
                print(f"[GachaStageWidget] Paint mascot error: {e}")
            painter.restore()

        card_w = min(440.0, float(self.width()) - 40.0)
        card_h = 82.0
        card_x = cx - card_w / 2.0
        card_y = cy + 68.0

        painter.setBrush(QBrush(QColor("#22252E")))
        painter.setPen(QPen(QColor(r_col.red(), r_col.green(), r_col.blue(), 120), 1.2))
        painter.drawRoundedRect(QRectF(card_x, card_y, card_w, card_h), 10.0, 10.0)

        tag_str = "NHÂN VẬT MỚI" if is_new else f"TRÙNG (+{shards_gained} MẢNH)"
        title_str = f"[{r_label.upper()}] {char.name}  •  {tag_str}"
        painter.setPen(r_col)
        title_font = QFont("Arial", 12, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.drawText(QRectF(card_x + 14, card_y + 10, card_w - 28, 24), Qt.AlignmentFlag.AlignCenter, title_str)

        painter.setPen(QColor("#9CA3AF"))
        desc_font = QFont("Arial", 10)
        painter.setFont(desc_font)
        painter.drawText(
            QRectF(card_x + 16, card_y + 38, card_w - 32, 36),
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            char.description
        )

    def _paint_multi_reveal(self, painter: QPainter, cx: float, cy: float, w: float, h: float):
        count = len(self._current_results)
        if count == 0:
            return

        bounce_scale = 0.80 + 0.20 * math.sin(self.reveal_bounce * math.pi / 2.0)
        card_w = min(130.0, (w - 72.0) / count - 10.0)
        card_h = 198.0
        total_w = count * card_w + (count - 1) * 12.0
        start_x = cx - total_w / 2.0
        card_y = cy - card_h / 2.0 - 4.0

        painter.setPen(QColor("#E5E7EB"))
        hdr_font = QFont("Arial", 13, QFont.Weight.Bold)
        painter.setFont(hdr_font)
        hdr_title = "KẾT QUẢ QUAY x5 + 1 BONUS RATE NGẪU NHIÊN" if count == 6 else f"KẾT QUẢ TRIỆU HỒI (x{count})"
        painter.drawText(QRectF(0, 26, w, 28), Qt.AlignmentFlag.AlignCenter, hdr_title)

        total_shards = 0
        for idx, res in enumerate(self._current_results):
            char = res.character
            total_shards += res.shards_gained
            r_info = RARITY_INFO.get(char.rarity, {})
            r_col = QColor(r_info.get("color", "#6BA3BE"))
            r_label = r_info.get("label", "Thường")
            is_bonus = getattr(res, "is_bonus", False)

            ix = start_x + idx * (card_w + 12.0)
            iy = card_y

            painter.setBrush(QBrush(QColor("#241622" if char.rarity == "mythic" else ("#28241E" if is_bonus else "#22252E"))))
            border_c = QColor("#D4A359") if is_bonus else QColor(r_col.red(), r_col.green(), r_col.blue(), 145)
            painter.setPen(QPen(border_c, 1.8 if is_bonus else 1.4))
            painter.drawRoundedRect(QRectF(ix, iy, card_w, card_h), 10.0, 10.0)

            if is_bonus:
                badge_text = "★ +1 RATE" if res.is_new else f"★ +{res.shards_gained} Mảnh"
                painter.setPen(QColor("#D4A359"))
            else:
                badge_text = "MỚI" if res.is_new else f"+{res.shards_gained} Mảnh"
                painter.setPen(QColor("#7AA2C4") if res.is_new else QColor("#A78BFA"))
            b_font = QFont("Arial", 8, QFont.Weight.Bold)
            painter.setFont(b_font)
            painter.drawText(QRectF(ix + 4, iy + 8, card_w - 8, 16), Qt.AlignmentFlag.AlignCenter, badge_text)

            if idx < len(self._renderers) and self._renderers[idx]:
                m_size = min(104.0, (card_w - 20.0)) * bounce_scale
                sc = m_size / 120.0
                painter.save()
                painter.translate(ix + (card_w - m_size) / 2.0, iy + 32.0)
                painter.scale(sc, sc)
                try:
                    self._renderers[idx].paint(painter, 120, 120, self._mascot_model)
                except Exception:
                    pass
                painter.restore()

            painter.setPen(QColor("#E5E7EB"))
            n_font = QFont("Arial", 9, QFont.Weight.Bold)
            painter.setFont(n_font)
            painter.drawText(
                QRectF(ix + 6, iy + card_h - 46, card_w - 12, 24),
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                char.name
            )
            painter.setPen(r_col)
            r_font = QFont("Arial", 8, QFont.Weight.Bold)
            painter.setFont(r_font)
            painter.drawText(QRectF(ix + 4, iy + card_h - 20, card_w - 8, 14), Qt.AlignmentFlag.AlignCenter, r_label.upper())

        if total_shards > 0:
            painter.setPen(QColor("#A78BFA"))
            s_font = QFont("Arial", 10, QFont.Weight.Bold)
            painter.setFont(s_font)
            painter.drawText(
                QRectF(0, card_y + card_h + 18, w, 22),
                Qt.AlignmentFlag.AlignCenter,
                f"Nhận thêm từ nhân vật trùng: +{total_shards} Mảnh Nhân Vật"
            )


AnimatedEggWidget = GachaStageWidget
AtomicCoreWidget = GachaStageWidget


class BannerSelectorCard(QFrame):
    """Clickable flat 2D Banner Tab Card in the left sidebar for switching between Banner Paper 1 & 2."""

    clicked = pyqtSignal(int)

    def __init__(self, index: int, title: str, subtitle: str, char: Optional[CharacterDef], parent=None):
        super().__init__(parent)
        self.index = index
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(74)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        self.preview = CharacterPreviewWidget(char, size=54, animated=False)
        layout.addWidget(self.preview)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.tag_lbl = QLabel(f"TRANG BANNER 0{index + 1}")
        self.tag_lbl.setStyleSheet("font-size: 9px; font-weight: 700; color: #D4A359;")
        text_col.addWidget(self.tag_lbl)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("font-size: 13px; font-weight: 800; color: #F3F4F6;")
        text_col.addWidget(self.title_lbl)

        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setStyleSheet("font-size: 10px; color: #9CA3AF;")
        text_col.addWidget(self.sub_lbl)

        layout.addLayout(text_col, stretch=1)
        self.set_active(False)

    def set_active(self, active: bool):
        if active:
            self.setStyleSheet("""
                BannerSelectorCard {
                    background: #282D3A;
                    border: 1.5px solid #5B8BB2;
                    border-radius: 9px;
                }
                BannerSelectorCard QLabel {
                    background: transparent;
                    border: none;
                }
            """)
        else:
            self.setStyleSheet("""
                BannerSelectorCard {
                    background: #1C1F26;
                    border: 1px solid #2A2E39;
                    border-radius: 9px;
                }
                BannerSelectorCard:hover {
                    background: #242832;
                    border: 1px solid #3A3F4D;
                }
                BannerSelectorCard QLabel {
                    background: transparent;
                    border: none;
                }
            """)

    def mousePressEvent(self, a0):
        if a0 is not None and a0.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.index)
            a0.accept()
        super().mousePressEvent(a0)


class EggTab(QWidget):
    """
    2-Page Banner Poster System with Hidden Full-Screen 3D Atomic Core Summon Stage.
    - No redundant inner top toolbar above the Banner Poster.
    - Unified Bottom Action Bar combining:
      Left (Tiếp Tế): [Điểm Danh Hằng Ngày] + [Nạp +1 Lõi] + [Nạp +5 Lõi]
      Right (Triệu Hồi): [Triệu Hồi x1] + [Triệu Hồi x5]
    """

    eggOpened = pyqtSignal()
    buyEggRequested = pyqtSignal()
    equipRequested = pyqtSignal(str)
    fullscreenModeChanged = pyqtSignal(bool)

    def __init__(self, service: CollectionService, parent=None):
        super().__init__(parent)
        self.service = service
        self.current_banner_idx: int = 0
        self.banner_cards: List[BannerSelectorCard] = []
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.view_stack = QStackedWidget()
        root_layout.addWidget(self.view_stack)

        # ====================================================================
        # VIEW 0: 2-PAGE BANNER POSTER SCREEN
        # ====================================================================
        banner_screen = QWidget()
        bs_layout = QHBoxLayout(banner_screen)
        bs_layout.setContentsMargins(0, 0, 0, 0)
        bs_layout.setSpacing(12)

        # ---------------- LEFT SIDEBAR: 2 BANNER TABS + RATES + PITY ----------------
        left_sidebar = QFrame()
        left_sidebar.setObjectName("bannerSidebar")
        left_sidebar.setFixedWidth(245)
        left_sidebar.setStyleSheet("""
            QFrame#bannerSidebar {
                background: #22252E;
                border: 1px solid #2E323E;
                border-radius: 10px;
            }
            QFrame#bannerSidebar QLabel {
                border: none;
                background: transparent;
            }
        """)
        left_layout = QVBoxLayout(left_sidebar)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        sb_hdr = QLabel("DANH SÁCH BANNER RATE-UP")
        sb_hdr.setStyleSheet("font-size: 10px; font-weight: 700; color: #9CA3AF; letter-spacing: 0.4px;")
        left_layout.addWidget(sb_hdr)

        phoebe_char = self.service.registry.get("phoebe_chuby")
        nono_char = self.service.registry.get("nono_chubby")
        aemeath_char = self.service.registry.get("aemeath_idol")

        card1 = BannerSelectorCard(0, "Phoebe Chupi", "Ước Nguyện Ánh Sáng", phoebe_char)
        card1.clicked.connect(self._switch_banner_page)
        left_layout.addWidget(card1)
        self.banner_cards.append(card1)

        card2 = BannerSelectorCard(1, "Nono (Phruonuo)", "Đóa Bỉ Ngạn Đỏ", nono_char)
        card2.clicked.connect(self._switch_banner_page)
        left_layout.addWidget(card2)
        self.banner_cards.append(card2)

        card3 = BannerSelectorCard(2, "Aemeath Idol", "Thiên Thần Ánh Sao", aemeath_char)
        card3.clicked.connect(self._switch_banner_page)
        left_layout.addWidget(card3)
        self.banner_cards.append(card3)

        # Drop Rates Breakdown Card
        rates_card = QFrame()
        rates_card.setObjectName("ratesCard")
        rates_card.setStyleSheet("""
            QFrame#ratesCard {
                background: #1C1F26;
                border: 1px solid #2A2E39;
                border-radius: 8px;
            }
        """)
        rates_layout = QVBoxLayout(rates_card)
        rates_layout.setContentsMargins(12, 8, 12, 8)
        rates_layout.setSpacing(4)

        rates_title = QLabel("TỶ LỆ RƠI THEO PHẨM CHẤT")
        rates_title.setStyleSheet("font-size: 10px; font-weight: 700; color: #6B7280;")
        rates_layout.addWidget(rates_title)

        for r_key in reversed(RARITY_ORDER):
            r_info = RARITY_INFO[r_key]
            row = QHBoxLayout()
            dot_lbl = QLabel(f"•  {r_info['label']}")
            dot_lbl.setStyleSheet(f"color: {r_info['color']}; font-size: 11px; font-weight: 600;")
            row.addWidget(dot_lbl)
            row.addStretch()
            pct_lbl = QLabel(f"{r_info['rate'] * 100:.0f}%")
            pct_lbl.setStyleSheet("color: #D1D5DB; font-size: 11px; font-weight: 600;")
            row.addWidget(pct_lbl)
            rates_layout.addLayout(row)

        left_layout.addWidget(rates_card)
        left_layout.addStretch()

        # Pity Progress Box (120 pulls guaranteed Rate-Up)
        pity_box = QFrame()
        pity_box.setObjectName("pityBox")
        pity_box.setStyleSheet("""
            QFrame#pityBox {
                background: #1C1F26;
                border: 1px solid #2A2E39;
                border-radius: 8px;
            }
        """)
        pity_layout = QVBoxLayout(pity_box)
        pity_layout.setContentsMargins(12, 8, 12, 8)
        pity_layout.setSpacing(4)

        self.pity_label = QLabel("Bảo hiểm Trúng Rate: 0/120")
        self.pity_label.setStyleSheet("font-size: 11px; color: #D4A359; font-weight: 700;")
        pity_layout.addWidget(self.pity_label)

        pity_sub = QLabel("Tối đa 120 lần quay chắc chắn trúng Rate")
        pity_sub.setStyleSheet("font-size: 10px; color: #9CA3AF;")
        pity_layout.addWidget(pity_sub)

        self.pity_bar = QProgressBar()
        self.pity_bar.setRange(0, 120)
        self.pity_bar.setValue(0)
        self.pity_bar.setFixedHeight(6)
        self.pity_bar.setTextVisible(False)
        self.pity_bar.setStyleSheet("""
            QProgressBar {
                background: #14161B;
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background: #3D6B8E;
                border-radius: 3px;
            }
        """)
        pity_layout.addWidget(self.pity_bar)
        left_layout.addWidget(pity_box)

        bs_layout.addWidget(left_sidebar)

        # ---------------- RIGHT MAIN AREA: FULL POSTER + UNIFIED BOTTOM TOOLBAR ----------------
        right_card = QFrame()
        right_card.setObjectName("rightBannerCard")
        right_card.setStyleSheet("""
            QFrame#rightBannerCard {
                background: #22252E;
                border: 1px solid #2E323E;
                border-radius: 10px;
            }
            QFrame#rightBannerCard QLabel {
                border: none;
                background: transparent;
            }
        """)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(14, 14, 14, 14)
        right_layout.setSpacing(12)

        # 1. Full Banner Poster Stack (Takes all upper space — no cluttered top toolbar!)
        self.banner_pages_stack = QStackedWidget()

        page1 = self._create_banner_poster_page(
            page_num=1,
            tag_text="TRANG BANNER 01 / 03  •  THẦN THOẠI",
            tag_bg="#2B2720",
            tag_col="#D4A359",
            tag_border="#453B2B",
            title="ƯỚC NGUYỆN ÁNH SÁNG\nPHOEBE CHUPI",
            subtitle="Cô bé Pháp Sư Cube Mochi đội mũ trắng núng nính, mang theo giọng nói Chibi trong trẻo cùng hiệu ứng ngủ bong bóng mũi đáng yêu.",
            featured_char=phoebe_char,
            companion_ids=["star_dragon", "ice_princess", "snow_fox"],
            voice_sample="phoebe_chupi.wav",
        )
        self.banner_pages_stack.addWidget(page1)

        page2 = self._create_banner_poster_page(
            page_num=2,
            tag_text="TRANG BANNER 02 / 03  •  THẦN THOẠI",
            tag_bg="#2D2226",
            tag_col="#D98A94",
            tag_border="#4A3238",
            title="ĐÓA BỈ NGẠN ĐỎ\nNONO (PHRUONUO)",
            subtitle="Nhân vật Cube Mochi bí ẩn với băng bịt mắt hoa Bỉ Ngạn Đỏ, sở hữu tông giọng Loli đặc trưng và biểu cảm chọc nổ bong bóng mũi.",
            featured_char=nono_char,
            companion_ids=["transform_warrior", "robo_mini", "jelly_slime"],
            voice_sample="nono_chubby.wav",
        )
        self.banner_pages_stack.addWidget(page2)

        page3 = self._create_banner_poster_page(
            page_num=3,
            tag_text="TRANG BANNER 03 / 03  •  THẦN THOẠI",
            tag_bg="#2E222B",
            tag_col="#EC8CB8",
            tag_border="#4E3446",
            title="THIÊN THẦN ÁNH SAO\nAEMEATH IDOL",
            subtitle="Thiên thần Idol tóc hồng phấn đáng yêu với vòng hào quang băng lam, đôi mắt sao vàng lấp lánh và 2 gậy cổ vũ phát sáng rực rỡ khi trò chuyện.",
            featured_char=aemeath_char,
            companion_ids=["ice_princess", "neon_cat", "bun_bao"],
            voice_sample="phoebe_chupi.wav",
        )
        self.banner_pages_stack.addWidget(page3)

        right_layout.addWidget(self.banner_pages_stack, stretch=1)

        # 2. Unified Bottom Toolbar: [Điểm Danh | +1 Lõi | +5 Lõi] (Left) + [Triệu Hồi x1 | Triệu Hồi x5] (Right)
        bottom_toolbar = QFrame()
        bottom_toolbar.setObjectName("bannerBottomToolbar")
        bottom_toolbar.setStyleSheet("""
            QFrame#bannerBottomToolbar {
                background: #1C1F26;
                border: 1px solid #2A2E39;
                border-radius: 9px;
            }
        """)
        bot_layout = QHBoxLayout(bottom_toolbar)
        bot_layout.setContentsMargins(10, 8, 10, 8)
        bot_layout.setSpacing(8)

        # Left Group: Daily Check-In + Bonus Info (No more Core Top-Up buttons!)
        self.daily_btn = QPushButton("Điểm Danh (+50 Xu)")
        self.daily_btn.setFixedHeight(36)
        self.daily_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.daily_btn.setStyleSheet("""
            QPushButton {
                background: #3A6B5C;
                border: none;
                color: #F3F4F6;
                font-size: 11px;
                font-weight: 700;
                border-radius: 6px;
                padding: 0 14px;
            }
            QPushButton:hover {
                background: #467E6D;
            }
            QPushButton:pressed {
                background: #315B4E;
            }
            QPushButton:disabled {
                background: #22252E;
                border: 1px solid #2E323E;
                color: #6B7280;
            }
        """)
        self.daily_btn.clicked.connect(self._on_daily_claim_clicked)
        bot_layout.addWidget(self.daily_btn)

        bonus_note = QLabel("Ưu đãi: Quay 5 lần tặng thêm +1 Rate ngẫu nhiên")
        bonus_note.setStyleSheet("font-size: 11px; font-weight: 600; color: #9CA3AF; padding-left: 6px;")
        bot_layout.addWidget(bonus_note)

        # Hidden compatibility widgets
        self.buy_btn = QPushButton("")
        self.buy_btn.setVisible(False)
        self.buy5_btn = QPushButton("")
        self.buy5_btn.setVisible(False)
        self.eggs_label = QLabel("")
        self.eggs_label.setVisible(False)

        bot_layout.addStretch()

        # Right Group: Direct Coin Summon x1 (200 Xu) & x5 + 1 Rate (1,000 Xu)
        self.open_btn = QPushButton("Quay x1 (200 Xu)")
        self.open_btn.setFixedHeight(36)
        self.open_btn.setMinimumWidth(145)
        self.open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_btn.setStyleSheet("""
            QPushButton {
                background: #3D6B8E;
                color: #F3F4F6;
                font-size: 12px;
                font-weight: 700;
                border-radius: 6px;
                border: none;
                padding: 0 16px;
            }
            QPushButton:hover {
                background: #487CA3;
            }
            QPushButton:pressed {
                background: #335978;
            }
            QPushButton:disabled {
                background: #22252E;
                color: #6B7280;
                border: 1px solid #2E323E;
            }
        """)
        self.open_btn.clicked.connect(lambda: self._on_open_clicked(1))
        bot_layout.addWidget(self.open_btn)

        self.open5_btn = QPushButton("Quay x5 + 1 Rate (1,000 Xu)")
        self.open5_btn.setFixedHeight(36)
        self.open5_btn.setMinimumWidth(190)
        self.open5_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open5_btn.setStyleSheet("""
            QPushButton {
                background: #B57B42;
                color: #F3F4F6;
                font-size: 12px;
                font-weight: 700;
                border-radius: 6px;
                border: none;
                padding: 0 16px;
            }
            QPushButton:hover {
                background: #C4884E;
            }
            QPushButton:pressed {
                background: #9E6936;
            }
            QPushButton:disabled {
                background: #22252E;
                color: #6B7280;
                border: 1px solid #2E323E;
            }
        """)
        self.open5_btn.clicked.connect(lambda: self._on_open_clicked(5))
        bot_layout.addWidget(self.open5_btn)

        right_layout.addWidget(bottom_toolbar)
        bs_layout.addWidget(right_card, stretch=1)

        self.view_stack.addWidget(banner_screen)

        # ====================================================================
        # VIEW 1: FULL-SCREEN 3D SUMMON & REVEAL OVERLAY
        # ====================================================================
        fs_screen = QFrame()
        fs_screen.setObjectName("fullscreenSummonFrame")
        fs_screen.setStyleSheet("""
            QFrame#fullscreenSummonFrame {
                background: #181A20;
                border: none;
            }
        """)
        fs_layout = QVBoxLayout(fs_screen)
        fs_layout.setContentsMargins(18, 14, 18, 16)
        fs_layout.setSpacing(10)

        # Top Bar of Fullscreen Summon
        fs_top = QHBoxLayout()
        self.fs_banner_lbl = QLabel("ĐANG TRIỆU HỒI...")
        self.fs_banner_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #9CA3AF;")
        fs_top.addWidget(self.fs_banner_lbl)
        fs_top.addStretch()

        self.skip_btn = QPushButton("Bỏ Qua Hoạt Ảnh ⏭")
        self.skip_btn.setFixedHeight(30)
        self.skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.skip_btn.setStyleSheet("""
            QPushButton {
                background: #22252E;
                color: #D1D5DB;
                font-size: 11px;
                font-weight: 600;
                border-radius: 6px;
                border: 1px solid #2E323E;
                padding: 0 12px;
            }
            QPushButton:hover {
                background: #2B2F3A;
                color: #F3F4F6;
            }
        """)
        self.skip_btn.clicked.connect(self._on_skip_or_close_fullscreen)
        fs_top.addWidget(self.skip_btn)
        fs_layout.addLayout(fs_top)

        # Center: Fullscreen 3D Atomic Summon & Reveal Stage
        self.gacha_stage = GachaStageWidget()
        self.egg_widget = self.gacha_stage
        fs_layout.addWidget(self.gacha_stage, stretch=1)

        # Bottom Controls on Fullscreen Reveal
        self.fs_bottom_bar = QWidget()
        fs_bot_layout = QHBoxLayout(self.fs_bottom_bar)
        fs_bot_layout.setContentsMargins(0, 0, 0, 0)
        fs_bot_layout.setSpacing(10)

        self.back_banner_btn = QPushButton("◀ Quay Lại Banner")
        self.back_banner_btn.setFixedHeight(40)
        self.back_banner_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_banner_btn.setStyleSheet("""
            QPushButton {
                background: #2B2F3A;
                color: #F3F4F6;
                font-size: 13px;
                font-weight: 700;
                border-radius: 7px;
                border: 1px solid #383D4B;
                padding: 0 20px;
            }
            QPushButton:hover {
                background: #353A47;
            }
        """)
        self.back_banner_btn.clicked.connect(self._exit_fullscreen_summon)
        fs_bot_layout.addWidget(self.back_banner_btn, stretch=1)

        self.roll_again_1_btn = QPushButton("Triệu Hồi Tiếp x1")
        self.roll_again_1_btn.setFixedHeight(40)
        self.roll_again_1_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.roll_again_1_btn.setStyleSheet("""
            QPushButton {
                background: #3D6B8E;
                color: #F3F4F6;
                font-size: 13px;
                font-weight: 700;
                border-radius: 7px;
                border: none;
                padding: 0 18px;
            }
            QPushButton:hover {
                background: #487CA3;
            }
            QPushButton:disabled {
                background: #1C1F26;
                color: #6B7280;
            }
        """)
        self.roll_again_1_btn.clicked.connect(lambda: self._on_open_clicked(1))
        fs_bot_layout.addWidget(self.roll_again_1_btn, stretch=1)

        self.roll_again_5_btn = QPushButton("Triệu Hồi Tiếp x5")
        self.roll_again_5_btn.setFixedHeight(40)
        self.roll_again_5_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.roll_again_5_btn.setStyleSheet("""
            QPushButton {
                background: #B57B42;
                color: #F3F4F6;
                font-size: 13px;
                font-weight: 700;
                border-radius: 7px;
                border: none;
                padding: 0 18px;
            }
            QPushButton:hover {
                background: #C4884E;
            }
            QPushButton:disabled {
                background: #1C1F26;
                color: #6B7280;
            }
        """)
        self.roll_again_5_btn.clicked.connect(lambda: self._on_open_clicked(5))
        fs_bot_layout.addWidget(self.roll_again_5_btn, stretch=1)

        self.equip_now_btn = QPushButton("Trang Bị Ngay")
        self.equip_now_btn.setFixedHeight(40)
        self.equip_now_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.equip_now_btn.setStyleSheet("""
            QPushButton {
                background: #3A6B5C;
                color: #F3F4F6;
                font-size: 13px;
                font-weight: 700;
                border-radius: 7px;
                border: none;
                padding: 0 18px;
            }
            QPushButton:hover {
                background: #467E6D;
            }
        """)
        self.equip_now_btn.clicked.connect(self._on_equip_now_clicked)
        fs_bot_layout.addWidget(self.equip_now_btn, stretch=1)

        fs_layout.addWidget(self.fs_bottom_bar)
        self.view_stack.addWidget(fs_screen)

        self._switch_banner_page(0)

    def _create_banner_poster_page(
        self,
        page_num: int,
        tag_text: str,
        tag_bg: str,
        tag_col: str,
        tag_border: str,
        title: str,
        subtitle: str,
        featured_char: Optional[CharacterDef],
        companion_ids: List[str],
        voice_sample: str,
    ) -> QFrame:
        """Builds one full 2D Banner Poster Page (Paper 1 or Paper 2)."""
        poster = QFrame()
        poster.setObjectName(f"bannerPosterPage{page_num}")
        poster.setStyleSheet(f"""
            QFrame#bannerPosterPage{page_num} {{
                background: #1C1F26;
                border: 1px solid #2A2E39;
                border-radius: 10px;
            }}
            QFrame#bannerPosterPage{page_num} QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        layout = QHBoxLayout(poster)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(22)

        # Left Info Column of Poster
        info_col = QVBoxLayout()
        info_col.setSpacing(10)

        # Top row inside poster: Banner Tag + Compact Page Switcher (< 1/2 >)
        poster_top_row = QHBoxLayout()
        poster_top_row.setSpacing(6)

        tag_lbl = QLabel(tag_text)
        tag_lbl.setStyleSheet(f"""
            background: {tag_bg};
            color: {tag_col};
            border: 1px solid {tag_border};
            border-radius: 5px;
            padding: 4px 10px;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.5px;
        """)
        poster_top_row.addWidget(tag_lbl)
        poster_top_row.addStretch()

        switch_btn_style = """
            QPushButton {
                background: #22252E;
                color: #9CA3AF;
                font-size: 10px;
                font-weight: 700;
                border-radius: 5px;
                border: 1px solid #2E323E;
                padding: 0 8px;
            }
            QPushButton:hover {
                background: #2B2F3A;
                color: #F3F4F6;
            }
        """
        prev_btn = QPushButton("◀")
        prev_btn.setFixedSize(26, 24)
        prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        prev_btn.setStyleSheet(switch_btn_style)
        prev_btn.setToolTip("Chuyển trang Banner")
        prev_btn.clicked.connect(lambda: self._switch_banner_page((self.current_banner_idx - 1) % len(self.banner_cards)))
        poster_top_row.addWidget(prev_btn)

        next_btn = QPushButton("▶")
        next_btn.setFixedSize(26, 24)
        next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        next_btn.setStyleSheet(switch_btn_style)
        next_btn.setToolTip("Chuyển trang Banner")
        next_btn.clicked.connect(lambda: self._switch_banner_page((self.current_banner_idx + 1) % len(self.banner_cards)))
        poster_top_row.addWidget(next_btn)

        info_col.addLayout(poster_top_row)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 23px; font-weight: 800; color: #F3F4F6; line-height: 1.2;")
        info_col.addWidget(title_lbl)

        sub_lbl = QLabel(subtitle)
        sub_lbl.setWordWrap(True)
        sub_lbl.setStyleSheet("font-size: 12px; color: #9CA3AF; line-height: 1.45;")
        info_col.addWidget(sub_lbl)

        # Voice Preview Button directly on Banner Poster
        voice_btn = QPushButton("▶  Nghe Thử Giọng Nói Nhân Vật")
        voice_btn.setFixedHeight(32)
        voice_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        voice_btn.setStyleSheet("""
            QPushButton {
                background: #22252E;
                color: #D1D5DB;
                font-size: 11px;
                font-weight: 600;
                border-radius: 6px;
                border: 1px solid #323644;
                padding: 0 14px;
            }
            QPushButton:hover {
                background: #2B2F3A;
                color: #F3F4F6;
            }
        """)
        voice_btn.clicked.connect(lambda: self._play_banner_voice(voice_sample))
        info_col.addWidget(voice_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        info_col.addStretch()

        # Companion Rate-Up Row at bottom-left of Poster
        comp_hdr = QLabel("NHÂN VẬT ĐI KÈM TRONG BANNER:")
        comp_hdr.setStyleSheet("font-size: 10px; font-weight: 700; color: #6B7280;")
        info_col.addWidget(comp_hdr)

        comp_row = QHBoxLayout()
        comp_row.setSpacing(10)
        for cid in companion_ids:
            c_def = self.service.registry.get(cid)
            if c_def:
                c_box = QHBoxLayout()
                c_box.setSpacing(6)
                pw = CharacterPreviewWidget(c_def, size=44, animated=False)
                c_box.addWidget(pw)
                c_lbl = QLabel(c_def.name)
                c_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #D1D5DB;")
                c_box.addWidget(c_lbl)
                comp_row.addLayout(c_box)
        comp_row.addStretch()
        info_col.addLayout(comp_row)

        layout.addLayout(info_col, stretch=3)

        # Right Showcase Column of Poster (Large Live 2D Animated Character Portrait)
        showcase_frame = QFrame()
        showcase_frame.setObjectName(f"posterStage{page_num}")
        showcase_frame.setFixedSize(220, 268)
        showcase_frame.setStyleSheet(f"""
            QFrame#posterStage{page_num} {{
                background: #22252E;
                border: 1px solid #2E323E;
                border-radius: 10px;
            }}
        """)
        sf_layout = QVBoxLayout(showcase_frame)
        sf_layout.setContentsMargins(14, 14, 14, 12)
        sf_layout.setSpacing(8)
        sf_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if featured_char:
            big_preview = CharacterPreviewWidget(featured_char, size=182, animated=True)
            sf_layout.addWidget(big_preview, alignment=Qt.AlignmentFlag.AlignCenter)

            char_badge = QLabel(f"★ {featured_char.name.upper()} ★")
            char_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            char_badge.setStyleSheet(f"font-size: 12px; font-weight: 800; color: {tag_col};")
            sf_layout.addWidget(char_badge)

        layout.addWidget(showcase_frame, alignment=Qt.AlignmentFlag.AlignVCenter)
        return poster

    def _switch_banner_page(self, index: int):
        self.current_banner_idx = index
        self.banner_pages_stack.setCurrentIndex(index)
        for i, card in enumerate(self.banner_cards):
            card.set_active(i == index)

    def _play_banner_voice(self, sample_name: str):
        try:
            import os
            from utils.paths import resource_path
            from utils.sound_player import play_wav_safely
            wav_path = resource_path(os.path.join("voice-models", "samples", sample_name))
            play_wav_safely(wav_path)
        except Exception:
            pass

    def refresh(self):
        w = self.service.wallet()
        pity = int(w.get("pity", 0))

        self.pity_bar.setValue(min(120, pity))
        remaining = max(0, 120 - pity)
        self.pity_label.setText(f"Bảo hiểm Trúng Rate: {pity}/120 (còn {remaining} lượt)")

        # Daily Check-In button state
        today_iso = date.today().isoformat()
        last_daily = w.get("last_daily")
        streak = int(w.get("streak", 0))
        if last_daily == today_iso:
            self.daily_btn.setText(f"Đã Điểm Danh ({streak}N)")
            self.daily_btn.setEnabled(False)
        else:
            self.daily_btn.setText("Điểm Danh (+50 Xu)")
            self.daily_btn.setEnabled(True)

        self.open_btn.setText("Quay x1 (200 Xu)")
        self.open5_btn.setText("Quay x5 + 1 Rate (1,000 Xu)")
        self.roll_again_1_btn.setText("Quay Tiếp x1 (200 Xu)")
        self.roll_again_5_btn.setText("Quay Tiếp x5 + 1 Rate (1,000 Xu)")

    def _on_daily_claim_clicked(self):
        msg = self.service.claim_daily()
        if msg:
            self.refresh()
            self.buyEggRequested.emit()
            QMessageBox.information(self, "Điểm Danh Hằng Ngày", msg)

    def _on_open_clicked(self, count: int = 1):
        if self.gacha_stage.is_cracking:
            return

        banner_ids = ["phoebe_chuby", "nono_chubby", "aemeath_idol"]
        featured_id = banner_ids[self.current_banner_idx] if 0 <= self.current_banner_idx < len(banner_ids) else "phoebe_chuby"
        outcome, results = self.service.roll_with_coins(count=count, featured_id=featured_id)
        if not outcome.ok or not results:
            QMessageBox.information(
                self,
                "Chưa Đủ Pop Xu",
                f"{outcome.message}\n\n"
                f"• Quay 1 lần: 200 Xu\n"
                f"• Quay 5 lần (+1 lượt Rate ngẫu nhiên): 1,000 Xu\n"
                f"• Điểm danh hằng ngày hoặc trò chuyện với Mascot để nhận thêm Xu!",
            )
            return

        # Enter Full-Screen 3D Summon View!
        self.view_stack.setCurrentIndex(1)
        self.fullscreenModeChanged.emit(True)

        banner_names = [
            "Banner 01: Phoebe Chupi",
            "Banner 02: Nono (Phruonuo)",
            "Banner 03: Aemeath (Thiên Thần Idol)",
        ]
        banner_name = banner_names[self.current_banner_idx] if 0 <= self.current_banner_idx < len(banner_names) else banner_names[0]
        self.fs_banner_lbl.setText(f"TRIỆU HỒI TỪ {banner_name.upper()}")
        self.skip_btn.setText("Bỏ Qua Hoạt Ảnh ⏭")
        self.fs_bottom_bar.setVisible(False)
        self.equip_now_btn.setVisible(False)

        self.gacha_stage.start_open_sequence(results, on_finish=self._on_gacha_finished)

    def _on_gacha_finished(self):
        self.refresh()
        self.skip_btn.setText("✕ Đóng Màn Hình Triệu Hồi")
        self.fs_bottom_bar.setVisible(True)

        single = self.gacha_stage.last_single_result
        if single:
            self.equip_now_btn.setText(f"Trang Bị {single.character.name}")
            self.equip_now_btn.setVisible(True)
            self.equip_now_btn.setEnabled(True)
        else:
            self.equip_now_btn.setVisible(False)

        self.eggOpened.emit()

    def _on_skip_or_close_fullscreen(self):
        if self.gacha_stage.is_cracking:
            self.gacha_stage.skip_to_reveal()
        else:
            self._exit_fullscreen_summon()

    def _exit_fullscreen_summon(self):
        self.gacha_stage.reset_to_atom()
        self.view_stack.setCurrentIndex(0)
        self.fullscreenModeChanged.emit(False)
        self.refresh()

    def _on_equip_now_clicked(self):
        single = self.gacha_stage.last_single_result
        if not single:
            return
        outcome = self.service.equip(single.character.id)
        if outcome.ok:
            self.equip_now_btn.setText("Đã Trang Bị")
            self.equip_now_btn.setEnabled(False)
            self.equipRequested.emit(single.character.id)

    def _on_buy_clicked(self, qty: int = 1):
        outcome = self.service.buy_egg(qty)
        if outcome.ok:
            self.refresh()
            self.buyEggRequested.emit()
        else:
            QMessageBox.information(self, "Nạp Lõi Năng Lượng", outcome.message)
