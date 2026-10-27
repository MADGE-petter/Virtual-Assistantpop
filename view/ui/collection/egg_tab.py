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
        self.aura_color: QColor = QColor(0, 255, 170)

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

        # 3 Orbitals with clean wireframe paths
        self.orbitals: List[Dict[str, Any]] = [
            {"base_angle": 30.0,  "speed": 1.25, "offset": 0.0, "particles": [0.0, math.pi]},
            {"base_angle": 90.0,  "speed": 0.95, "offset": 1.4, "particles": [0.4, 0.4 + math.pi]},
            {"base_angle": 150.0, "speed": 1.40, "offset": 2.8, "particles": [1.1, 1.1 + math.pi]},
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
        self.set_aura_color(r_info.get("color", "#00FFAA"))

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
        self.aura_color = QColor(0, 255, 170)
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
        # Subtle shake during high-speed spin
        if self.state == "SPINNING":
            spin_p = self.spin_timer / self.spin_duration
            shake = (spin_p ** 2) * 3.5
            cx += math.sin(self.phase * 22.0) * shake
            cy += math.cos(self.phase * 19.0) * shake

        a = 78.0  # semi-major axis
        b = 26.0  # semi-minor axis
        precession = math.sin(self.phase * 0.4) * 3.0

        is_fast = (self.state == "SPINNING")
        trail_count = 14 if is_fast else 7
        trail_step = 0.06 if is_fast else 0.075

        # ---------------- A. DRAW ORBITAL WIREFRAMES ----------------
        # CRITICAL: Always set brush to NoBrush so NO white/solid fill occurs!
        painter.setBrush(Qt.BrushStyle.NoBrush)

        orbit_thetas = []
        for orb in self.orbitals:
            angle_deg = orb["base_angle"] + precession
            theta = math.radians(angle_deg)
            orbit_thetas.append(theta)

            # Draw clean wireframe ellipse ring
            path = QPainterPath()
            cos_t = math.cos(theta)
            sin_t = math.sin(theta)
            for s in range(61):
                phi = (s / 60.0) * 2.0 * math.pi
                xl = a * math.cos(phi)
                yl = b * math.sin(phi)
                px = cx + xl * cos_t - yl * sin_t
                py = cy + xl * sin_t + yl * cos_t
                if s == 0:
                    path.moveTo(px, py)
                else:
                    path.lineTo(px, py)

            pen_alpha = 150 if is_fast else 90
            ring_pen = QPen(QColor(self.aura_color.red(), self.aura_color.green(), self.aura_color.blue(), pen_alpha), 1.3)
            painter.setPen(ring_pen)
            painter.drawPath(path)

        # ---------------- B. PARTICLES & AFTERIMAGES (TÀN ẢNH) ----------------
        for idx, orb in enumerate(self.orbitals):
            theta = orbit_thetas[idx]
            cos_t = math.cos(theta)
            sin_t = math.sin(theta)
            speed = orb["speed"]
            offset = orb["offset"]

            for base_p in orb["particles"]:
                phi = self.phase * speed + offset + base_p

                # 1. Draw glowing Afterimage Tail (Tàn ảnh lướt phía sau)
                for k in range(1, trail_count + 1):
                    t_phi = phi - k * trail_step
                    txl = a * math.cos(t_phi)
                    tyl = b * math.sin(t_phi)
                    tpx = cx + txl * cos_t - tyl * sin_t
                    tpy = cy + txl * sin_t + tyl * cos_t

                    decay = 1.0 - (k / float(trail_count))
                    tail_alpha = int((190 if is_fast else 140) * (decay ** 1.4))
                    tail_size = max(1.2, 4.2 * decay)

                    t_col = QColor(self.aura_color.red(), self.aura_color.green(), self.aura_color.blue(), tail_alpha)
                    painter.setBrush(QBrush(t_col))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(QRectF(tpx - tail_size / 2, tpy - tail_size / 2, tail_size, tail_size))

                # 2. Main Particle (Hạt nguyên tử)
                xl = a * math.cos(phi)
                yl = b * math.sin(phi)
                px = cx + xl * cos_t - yl * sin_t
                py = cy + xl * sin_t + yl * cos_t

                # Glowing Halo
                halo_r = 8.5
                halo_grad = QRadialGradient(px, py, halo_r)
                halo_grad.setColorAt(0.0, QColor(self.aura_color.red(), self.aura_color.green(), self.aura_color.blue(), 210))
                halo_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
                painter.setBrush(QBrush(halo_grad))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(px - halo_r, py - halo_r, halo_r * 2, halo_r * 2))

                # Bright Core Dot
                painter.setBrush(QBrush(QColor(255, 255, 255, 250)))
                painter.drawEllipse(QRectF(px - 2.8, py - 2.8, 5.6, 5.6))

        # ---------------- C. CENTRAL NUCLEUS (HIỆN RÕ LÕI) ----------------
        pulse = (math.sin(self.phase * 2.4) + 1.0) / 2.0
        nuc_r = 23.0 + pulse * 2.2

        # 1. Soft Outer Aura (No obscuring white)
        aura_rad = nuc_r * 2.2 + pulse * 8.0
        aura_grad = QRadialGradient(cx, cy, aura_rad)
        aura_alpha = 110 if is_fast else 65
        aura_grad.setColorAt(0.0, QColor(self.aura_color.red(), self.aura_color.green(), self.aura_color.blue(), aura_alpha))
        aura_grad.setColorAt(0.7, QColor(self.aura_color.red(), self.aura_color.green(), self.aura_color.blue(), int(aura_alpha * 0.2)))
        aura_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(aura_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - aura_rad, cy - aura_rad, aura_rad * 2, aura_rad * 2))

        # 2. Semi-transparent Luminous Crystal Nucleus Sphere
        sphere_grad = QRadialGradient(cx - nuc_r * 0.25, cy - nuc_r * 0.25, nuc_r * 1.2)
        sphere_grad.setColorAt(0.0, QColor(255, 255, 255, 230))
        sphere_grad.setColorAt(0.35, QColor(self.aura_color.red(), self.aura_color.green(), self.aura_color.blue(), 200))
        sphere_grad.setColorAt(0.85, QColor(self.aura_color.red(), self.aura_color.green(), self.aura_color.blue(), 130))
        sphere_grad.setColorAt(1.0, QColor(10, 20, 38, 190))
        painter.setBrush(QBrush(sphere_grad))
        painter.setPen(QPen(QColor(self.aura_color.red(), self.aura_color.green(), self.aura_color.blue(), 220), 1.5))
        painter.drawEllipse(QRectF(cx - nuc_r, cy - nuc_r, nuc_r * 2, nuc_r * 2))

        # 3. Inner Energy Nodes (3 micro quarks orbiting inside nucleus)
        for q_idx in range(3):
            q_angle = self.phase * 3.2 + q_idx * (2.0 * math.pi / 3.0)
            q_rad = nuc_r * 0.40
            qx = cx + math.cos(q_angle) * q_rad
            qy = cy + math.sin(q_angle) * q_rad
            painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(qx - 2.2, qy - 2.2, 4.4, 4.4))

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
