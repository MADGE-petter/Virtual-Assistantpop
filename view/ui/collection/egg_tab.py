"""
Egg Tab - Interactive Gacha Quantum Atomic Core View.
Features a central atomic core with afterimage orbiting electrons, fast-spin overcharge,
white-hot energy flash, and instant transformation into the revealed mascot character.
Styled to match POP AI View design system with no emoji icons.
"""

import math
from typing import Optional, List, Dict, Any
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QLinearGradient, QRadialGradient,
    QPainterPath, QFont
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFrame, QMessageBox
)
from service.collection.character_registry import RARITY_INFO, CharacterDef
from service.collection.collection_service import CollectionService, OpenResult
from view.ui.mascot.characters import create_renderer_for_character
from view.ui.mascot.characters.base_character_renderer import BaseCharacterRenderer
from view.ui.mascot.mascot_model import MascotModel
from view.ui.styles import DesignTokens


class GachaStageWidget(QWidget):
    """
    Central Gacha Stage Widget.
    - State 'IDLE': Sleek transparent atomic core with orbiting particles leaving afterimages.
    - State 'SPINNING': Super-accelerated rotation creating glowing light ribbons.
    - State 'FLASH': Sudden white-hot energy flash.
    - State 'REVEALED': Directly transforms into the revealed Mascot Character on the stage.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(440, 290)
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

        self._current_result: Optional[OpenResult] = None
        self._mascot_renderer: Optional[BaseCharacterRenderer] = None
        self._mascot_model: MascotModel = MascotModel()
        self._on_finish_callback = None

        # 4 Quỹ đạo 3D phân bổ đều 4 hướng (Ngang, Dọc, Chéo 1, Chéo 2)
        # Nhịp quay lệch nhau 90 độ cố định để 4 quả luôn phân bổ đều, không dồn cục
        self.orbitals: List[Dict[str, Any]] = [
            {"type": "horizontal", "speed": 1.25, "offset": 0.0,            "radius": 60.0},  # Vòng 1: Ngang (lướt trước - sau theo chiều ngang)
            {"type": "vertical",   "speed": 1.25, "offset": math.pi * 0.5,  "radius": 66.0},  # Vòng 2: Dọc (lướt đỉnh - đáy theo chiều dọc)
            {"type": "diag_a",     "speed": 1.25, "offset": math.pi * 1.0,  "radius": 56.0},  # Vòng 3: Chéo 1 (Tây Bắc - Đông Nam)
            {"type": "diag_b",     "speed": 1.25, "offset": math.pi * 1.5,  "radius": 62.0},  # Vòng 4: Chéo 2 (Tây Nam - Đông Bắc)
        ]

        self._timer = QTimer(self)
        self._timer.setInterval(25)  # 40 fps
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    @property
    def is_cracking(self) -> bool:
        return self.state in ("SPINNING", "FLASH")

    def set_aura_color(self, hex_color: str):
        self.aura_color = QColor(hex_color)
        self.update()

    def start_open_sequence(self, result: OpenResult, on_finish):
        """Begin gacha roll: fast spin -> bright flash -> reveal character."""
        self._current_result = result
        self._mascot_renderer = create_renderer_for_character(result.character)
        self._on_finish_callback = on_finish

        r_info = RARITY_INFO.get(result.character.rarity, {})
        self.set_aura_color(r_info.get("color", "#00D2FF"))

        self.state = "SPINNING"
        self.spin_timer = 0.0
        self.flash_timer = 0.0
        self.reveal_bounce = 0.0
        self.update()

    def reset_to_atom(self):
        """Reset state back to the idle atomic core."""
        self.state = "IDLE"
        self._current_result = None
        self._mascot_renderer = None
        self.aura_color = QColor(0, 210, 255)
        self.update()

    def _on_tick(self):
        dt = 0.025
        if self.state == "IDLE":
            self.phase += 0.045

        elif self.state == "SPINNING":
            self.spin_timer += dt
            # Exponential speedup from 1.0x to 10.0x
            prog = min(1.0, self.spin_timer / self.spin_duration)
            speed_mult = 1.0 + (prog ** 2.2) * 9.0
            self.phase += 0.045 * speed_mult

            if self.spin_timer >= self.spin_duration:
                # Trigger sudden bright flash
                self.state = "FLASH"
                self.flash_timer = 0.0

        elif self.state == "FLASH":
            self.flash_timer += dt
            self.phase += 0.35  # ultra fast during flash
            if self.flash_timer >= self.flash_duration:
                # Morph into revealed character!
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

        cx = self.width() / 2.0
        cy = self.height() / 2.0 - 15.0

        if self.state in ("IDLE", "SPINNING", "FLASH"):
            self._paint_atomic_core(painter, cx, cy)
            if self.state == "FLASH":
                self._paint_flash(painter, cx, cy)
        elif self.state == "REVEALED":
            self._paint_revealed_character(painter, cx, cy)

    # ============================================================
    # 1. ATOMIC CORE WITH AFTERIMAGES (NO WHITE PETALS)
    # ============================================================
    def _paint_atomic_core(self, painter: QPainter, cx: float, cy: float):
        is_fast = (self.state == "SPINNING")
        speed_mult = 2.2 if is_fast else 1.0

        # Màu sắc chính (mặc định Cyan Rasengan, tự đổi theo độ hiếm khi gacha)
        ar, ag, ab = self.aura_color.red(), self.aura_color.green(), self.aura_color.blue()

        # ============================================================
        # 1. TỌA ĐỘ 3D VÀ PHÉP CHIẾU PHỐI CẢNH (TRUE 3D PERSPECTIVE)
        # ============================================================
        rasengan_r = 20.0
        meteor_head_r = 9.0
        trail_count = 18 if is_fast else 14
        trail_step = 0.05 if is_fast else 0.065
        cam_dist = 220.0

        def calc_meteor_3d(orb_idx: int, theta: float):
            orb = self.orbitals[orb_idx]
            r = orb.get("radius", 60.0)
            orb_type = orb.get("type", "horizontal")

            ct = math.cos(theta)
            st = math.sin(theta)

            if orb_type == "horizontal":
                # Quỹ đạo ngang 3D: lướt qua trước mặt (Z > 0) và chìm sau lưng (Z < 0) theo phương ngang
                xw = r * ct
                yw = r * st * 0.38
                zw = r * st * 0.92
            elif orb_type == "vertical":
                # Quỹ đạo dọc 3D: lượn từ đỉnh qua trước mặt xuống đáy rồi vòng ngược sau lưng
                xw = r * ct * 0.38
                yw = r * st
                zw = r * ct * 0.92
            elif orb_type == "diag_a":
                # Quỹ đạo chéo 1 (Tây Bắc - Đông Nam): lượn 3D chéo góc
                xw = r * (ct * 0.7071 + st * 0.27)
                yw = r * (ct * 0.7071 - st * 0.27)
                zw = r * st * 0.92
            else:  # diag_b
                # Quỹ đạo chéo 2 (Tây Nam - Đông Bắc): lượn 3D chéo góc đối xứng
                xw = r * (ct * 0.7071 + st * 0.27)
                yw = r * (-ct * 0.7071 + st * 0.27)
                zw = r * st * 0.92

            # Phép chiếu phối cảnh 3D thực thụ (True Perspective Divide)
            # zw càng lớn (càng gần người xem) thì p_scale càng to, screen_x/y càng nở rộng
            p_scale = cam_dist / max(40.0, (cam_dist - zw))
            screen_x = cx + xw * p_scale
            screen_y = cy + yw * p_scale
            return (screen_x, screen_y, zw, p_scale)

        # Thu thập các điểm (đầu + đuôi thiên thạch)
        # Point tuple: (px, py, zw, p_scale, k, orb_idx)
        meteor_points = []
        for orb_idx, orb in enumerate(self.orbitals):
            head_theta = self.phase * orb["speed"] * speed_mult + orb["offset"]
            for k in range(trail_count, -1, -1):
                t_theta = head_theta - k * trail_step
                px, py, zw, p_scale = calc_meteor_3d(orb_idx, t_theta)
                meteor_points.append((px, py, zw, p_scale, k, orb_idx))

        # Phân lớp chiều sâu 3D: sau lưng (zw < 0) và phía trước (zw >= 0)
        behind_points = [p for p in meteor_points if p[2] < 0]
        front_points = [p for p in meteor_points if p[2] >= 0]
        behind_points.sort(key=lambda item: item[2])
        front_points.sort(key=lambda item: item[2])

        def draw_meteor_point(px: float, py: float, zw: float, p_scale: float, k: int, in_front: bool):
            if k == 0:
                # Quả cầu to xung quanh (rõ nét, kích thước co giãn mạnh theo 3D)
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

                # Thân quả cầu 3D
                s_grad = QRadialGradient(px - hr * 0.3, py - hr * 0.3, hr * 1.25)
                s_grad.setColorAt(0.0, QColor(255, 255, 255, 255))
                s_grad.setColorAt(0.45, QColor(ar, ag, ab, 240 if in_front else 160))
                s_grad.setColorAt(0.9, QColor(0, 90, 220, 200 if in_front else 130))
                s_grad.setColorAt(1.0, QColor(0, 40, 120, 180 if in_front else 100))
                painter.setBrush(QBrush(s_grad))
                painter.setPen(QPen(QColor(255, 255, 255, 200 if in_front else 120), 0.8))
                painter.drawEllipse(QRectF(px - hr, py - hr, hr * 2, hr * 2))

                # Lõi trắng sáng
                painter.setBrush(QBrush(QColor(255, 255, 255, 250 if in_front else 150)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(px - hr * 0.35, py - hr * 0.35, hr * 0.7, hr * 0.7))
            else:
                # Đuôi thiên thạch vuốt bé dần mượt mà theo phối cảnh 3D
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

        # ---------------- BƯỚC 1: VẼ CÁC QUẢ CẦU / ĐUÔI BAY SAU LƯNG (ZW < 0) ----------------
        for px, py, zw, p_scale, k, orb_idx in behind_points:
            draw_meteor_point(px, py, zw, p_scale, k, in_front=False)

        # ---------------- BƯỚC 2: VẼ QUẢ CẦU NỬA XANH NỬA TRẮNG KẾT HỢP (KHÔNG CÒN XOÁY TRẮNG) ----------------
        # A. Quầng sáng êm dịu bao quanh
        aura_rad = rasengan_r * 1.6
        aura_grad = QRadialGradient(cx, cy, aura_rad)
        aura_grad.setColorAt(0.0, QColor(ar, ag, ab, 65 if is_fast else 40))
        aura_grad.setColorAt(0.6, QColor(0, 140, 255, 20))
        aura_grad.setColorAt(1.0, QColor(0, 50, 200, 0))
        painter.setBrush(QBrush(aura_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - aura_rad, cy - aura_rad, aura_rad * 2, aura_rad * 2))

        # B. Quả cầu 3D nửa trắng nửa xanh xoay tròn rõ nét và sinh động hơn
        center_speed = 3.4 * (1.8 if is_fast else 1.0)
        rot_ang = -0.785 + self.phase * center_speed
        cos_rot = math.cos(rot_ang)
        sin_rot = math.sin(rot_ang)

        diag_x1 = cx - rasengan_r * cos_rot
        diag_y1 = cy - rasengan_r * sin_rot
        diag_x2 = cx + rasengan_r * cos_rot
        diag_y2 = cy + rasengan_r * sin_rot

        dual_grad = QLinearGradient(diag_x1, diag_y1, diag_x2, diag_y2)
        dual_grad.setColorAt(0.0, QColor(255, 255, 255, 255))        # Nửa trắng tinh khiết
        dual_grad.setColorAt(0.40, QColor(245, 250, 255, 250))      # Trắng ngọc phát quang
        dual_grad.setColorAt(0.48, QColor(190, 235, 255, 245))      # Giao thoa trắng - xanh dịu
        dual_grad.setColorAt(0.52, QColor(ar, ag, ab, 245))          # Nửa xanh năng lượng rực rỡ
        dual_grad.setColorAt(0.82, QColor(0, 110, 240, 230))        # Xanh lam điện
        dual_grad.setColorAt(1.0, QColor(10, 30, 80, 220))          # Xanh sapphire sâu tạo khối 3D

        painter.setBrush(QBrush(dual_grad))
        painter.setPen(QPen(QColor(255, 255, 255, 190), 0.8))
        painter.drawEllipse(QRectF(cx - rasengan_r, cy - rasengan_r, rasengan_r * 2, rasengan_r * 2))

        # C. Điểm bóng sáng thủy tinh 3D di chuyển theo nhịp quay
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

        # D. Lõi phát sáng nhẹ dịu trung tâm (kết nối 2 mảng màu)
        core_r = 4.5
        core_grad = QRadialGradient(cx, cy, core_r)
        core_grad.setColorAt(0.0, QColor(255, 255, 255, 220))
        core_grad.setColorAt(1.0, QColor(ar, ag, ab, 0))
        painter.setBrush(QBrush(core_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - core_r, cy - core_r, core_r * 2, core_r * 2))

        # ---------------- BƯỚC 3: VẼ CÁC QUẢ CẦU / ĐUÔI BAY PHÍA TRƯỚC (ZW >= 0) ----------------
        for px, py, zw, p_scale, k, orb_idx in front_points:
            draw_meteor_point(px, py, zw, p_scale, k, in_front=True)

    # ============================================================
    # 2. ENERGY FLASH (SÁNG BỪNG LÊN 1 CÁI)
    # ============================================================
    def _paint_flash(self, painter: QPainter, cx: float, cy: float):
        t = min(1.0, self.flash_timer / self.flash_duration)
        # Intensity peaks around t = 0.3 then fades
        if t < 0.3:
            intensity = t / 0.3
        else:
            intensity = 1.0 - ((t - 0.3) / 0.7)

        flash_rad = 30.0 + t * 160.0
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
    # 3. REVEALED CHARACTER ON STAGE (THAY THẾ BẢNG DƯỚI)
    # ============================================================
    def _paint_revealed_character(self, painter: QPainter, cx: float, cy: float):
        if not self._current_result:
            return

        char = self._current_result.character
        is_new = self._current_result.is_new
        shards_gained = self._current_result.shards_gained

        r_info = RARITY_INFO.get(char.rarity, {})
        r_col = QColor(r_info.get("color", "#00FFAA"))
        r_label = r_info.get("label", "Thường")

        # Gentle floating hover
        float_y = math.sin(self.phase * 2.2) * 3.5
        bounce_scale = 0.7 + 0.3 * math.sin(self.reveal_bounce * math.pi / 2.0)

        # 1. Glowing Rarity Pedestal / Aura
        halo_rad = 75.0
        h_grad = QRadialGradient(cx, cy - 20.0 + float_y, halo_rad)
        h_grad.setColorAt(0.0, QColor(r_col.red(), r_col.green(), r_col.blue(), 110))
        h_grad.setColorAt(0.6, QColor(r_col.red(), r_col.green(), r_col.blue(), 30))
        h_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(h_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - halo_rad, (cy - 20.0 + float_y) - halo_rad, halo_rad * 2, halo_rad * 2))

        # 2. Draw Mascot Sprite (Centered at 100x100)
        if self._mascot_renderer:
            mascot_size = 104.0 * bounce_scale
            scale = mascot_size / 120.0
            painter.save()
            painter.translate(cx - mascot_size / 2.0, (cy - 68.0 + float_y))
            painter.scale(scale, scale)
            try:
                self._mascot_renderer.paint(painter, 120, 120, self._mascot_model)
            except Exception as e:
                print(f"[GachaStageWidget] Paint mascot error: {e}")
            painter.restore()

        # 3. Text Info Card Below Mascot
        card_w = 340.0
        card_h = 76.0
        card_x = cx - card_w / 2.0
        card_y = cy + 44.0

        # Background badge for text
        painter.setBrush(QBrush(QColor(15, 23, 42, 220)))
        painter.setPen(QPen(QColor(r_col.red(), r_col.green(), r_col.blue(), 140), 1.2))
        painter.drawRoundedRect(QRectF(card_x, card_y, card_w, card_h), 12.0, 12.0)

        # Title: [MỚI] / [TRÙNG] + Name + Rarity
        tag_str = "[MỚI]" if is_new else "[TRÙNG]"
        title_str = f"{tag_str} [{r_label.upper()}] {char.name}"
        painter.setPen(r_col)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.drawText(QRectF(card_x + 10, card_y + 8, card_w - 20, 24), Qt.AlignmentFlag.AlignCenter, title_str)

        # Description / Duplicate Shards notice
        if is_new:
            sub_str = char.description
            sub_col = QColor(DesignTokens.TEXT_SECONDARY)
        else:
            sub_str = f"Đã sở hữu trước đó. Tự động quy đổi: +{shards_gained} Mảnh Nhân Vật"
            sub_col = QColor("#D8B4FE")

        painter.setPen(sub_col)
        desc_font = QFont()
        desc_font.setPointSize(10)
        desc_font.setBold(False)
        painter.setFont(desc_font)
        painter.drawText(QRectF(card_x + 10, card_y + 34, card_w - 20, 34), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, sub_str)


# Backward compatibility alias
AnimatedEggWidget = GachaStageWidget
AtomicCoreWidget = GachaStageWidget


class EggTab(QWidget):
    """View containing gacha statistics, interactive atomic stage, and instant mascot reveals."""

    eggOpened = pyqtSignal()
    buyEggRequested = pyqtSignal()

    def __init__(self, service: CollectionService, parent=None):
        super().__init__(parent)
        self.service = service
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(14)

        # ---------------- Stats Bar ----------------
        stats_frame = QFrame()
        stats_frame.setObjectName("statsFrame")
        stats_frame.setStyleSheet(f"""
            QFrame#statsFrame {{
                background: {DesignTokens.SURFACE_2};
                border: 1px solid;
                border-color: {DesignTokens.BORDER_GRADIENT};
                border-radius: 12px;
                padding: 8px 14px;
            }}
            QFrame#statsFrame QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(10, 4, 10, 4)

        self.eggs_label = QLabel("Lõi Nguyên Tử: 0")
        self.eggs_label.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {DesignTokens.TEXT_MAIN};")
        stats_layout.addWidget(self.eggs_label)

        stats_layout.addStretch()

        self.pity_label = QLabel("Bảo hiểm Huyền Thoại+: còn 50 lượt")
        self.pity_label.setStyleSheet("font-size: 12px; color: #F59E0B; font-weight: 700;")
        stats_layout.addWidget(self.pity_label)

        self.pity_bar = QProgressBar()
        self.pity_bar.setRange(0, 50)
        self.pity_bar.setValue(0)
        self.pity_bar.setFixedWidth(130)
        self.pity_bar.setFixedHeight(8)
        self.pity_bar.setTextVisible(False)
        self.pity_bar.setStyleSheet(f"""
            QProgressBar {{
                background: rgba(255, 255, 255, 0.08);
                border-radius: 4px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: {DesignTokens.GRADIENT_BLUE_GREEN};
                border-radius: 4px;
            }}
        """)
        stats_layout.addWidget(self.pity_bar)

        layout.addWidget(stats_frame)

        # ---------------- Center Stage: Quantum Atom Morphing Stage ----------------
        layout.addStretch(1)

        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # The Stage handles both Atomic Core and Revealed Mascot in-place
        self.gacha_stage = GachaStageWidget()
        self.egg_widget = self.gacha_stage  # alias
        center_layout.addWidget(self.gacha_stage, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(center_layout)
        layout.addStretch(1)

        # ---------------- Action Buttons ----------------
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(14)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.open_btn = QPushButton("Kích Hoạt Lõi (1)")
        self.open_btn.setFixedHeight(38)
        self.open_btn.setMinimumWidth(170)
        self.open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_btn.setStyleSheet(f"""
            QPushButton {{
                background: {DesignTokens.GRADIENT_BLUE_GREEN};
                color: #040812;
                font-size: 13px;
                font-weight: 700;
                border-radius: 8px;
                border: none;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0077D6, stop:1 #00E699);
            }}
            QPushButton:disabled {{
                background: rgba(255, 255, 255, 0.05);
                color: #64748B;
            }}
        """)
        self.open_btn.clicked.connect(self._on_open_clicked)
        btn_layout.addWidget(self.open_btn)

        self.buy_btn = QPushButton("Nạp Lõi (300 Xu)")
        self.buy_btn.setFixedHeight(38)
        self.buy_btn.setMinimumWidth(170)
        self.buy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.buy_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.04);
                color: {DesignTokens.TEXT_MAIN};
                font-size: 13px;
                font-weight: 600;
                border-radius: 8px;
                border: 1px solid;
                border-color: {DesignTokens.BORDER_GRADIENT};
                padding: 0 18px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.08);
                border-color: rgba(0, 255, 170, 0.4);
            }}
        """)
        self.buy_btn.clicked.connect(self._on_buy_clicked)
        btn_layout.addWidget(self.buy_btn)

        layout.addLayout(btn_layout)

    def refresh(self):
        w = self.service.wallet()
        eggs = int(w.get("eggs", 0))
        pity = int(w.get("pity", 0))

        self.eggs_label.setText(f"Lõi Nguyên Tử: {eggs}")
        self.pity_bar.setValue(min(50, pity))
        remaining = max(0, 50 - pity)
        self.pity_label.setText(f"Bảo hiểm Huyền Thoại+: còn {remaining} lượt")

        self.open_btn.setEnabled(eggs > 0)
        if eggs <= 0:
            self.open_btn.setText("Hết Lõi Năng Lượng")
        else:
            self.open_btn.setText(f"Kích Hoạt Lõi ({eggs})")

    def _on_open_clicked(self):
        if self.gacha_stage.is_cracking:
            return
        result = self.service.open_egg()
        if not result:
            return

        self.open_btn.setEnabled(False)
        self.buy_btn.setEnabled(False)

        # Trigger sequence on the stage itself
        self.gacha_stage.start_open_sequence(result, on_finish=self._on_gacha_finished)

    def _on_gacha_finished(self):
        self.refresh()
        self.buy_btn.setEnabled(True)
        self.eggOpened.emit()

    def _on_buy_clicked(self):
        outcome = self.service.buy_egg(1)
        if outcome.ok:
            self.refresh()
            self.buyEggRequested.emit()
        else:
            QMessageBox.information(self, "Nạp Lõi", outcome.message)
