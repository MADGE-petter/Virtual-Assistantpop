"""
Inventory Tab - Flat 2D Player's Collection & Interactive Character Studio.
Styled with flat 2D surfaces and natural muted colors without gradients.
"""

import time
from typing import Optional, List
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QProgressBar, QMessageBox
)
from model.voice_state_model import VoiceState
from service.collection.character_registry import RARITY_INFO, CharacterDef
from service.collection.collection_service import CollectionService
from view.ui.collection.character_preview_widget import CharacterPreviewWidget
from view.ui.mascot.characters import create_renderer_for_character
from view.ui.mascot.characters.base_character_renderer import BaseCharacterRenderer
from view.ui.mascot.mascot_model import MascotModel


class InteractiveCharacterStage(QWidget):
    """Flat 2D live animated 35 FPS preview stage for testing Idle, Talk, Sleep & Bubble Pop states."""

    def __init__(self, size: int = 136, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._size = size
        self._char: Optional[CharacterDef] = None
        self._renderer: Optional[BaseCharacterRenderer] = None
        self.model = MascotModel()
        self.model.cling_edge = None
        self.model.cling_ratio = 0.0

        self._timer = QTimer(self)
        self._timer.setInterval(28)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    def set_character(self, char: Optional[CharacterDef]):
        if self._char is None or (char and char.id != self._char.id):
            self.set_preview_mode("idle")
        self._char = char
        self._renderer = create_renderer_for_character(char) if char else None
        self.update()

    def set_preview_mode(self, mode: str):
        now = time.time()
        self.model.zzz_particles.clear()
        self.model.bubble_pop_particles.clear()
        self.model.bubble_pop_until = 0.0
        self.model.wake_up_until = 0.0
        self.model.is_dragging = False
        self.model.dizzy_end_time = 0.0
        self.model.is_playing_music = False

        if mode == "talk":
            self.model.is_sleeping = False
            self.model.cling_edge = None
            self.model.cling_ratio = 0.0
            self.model.voice_state = VoiceState.SPEAKING
        elif mode == "music":
            self.model.is_sleeping = False
            self.model.cling_edge = None
            self.model.cling_ratio = 0.0
            self.model.voice_state = VoiceState.READY
            self.model.is_playing_music = True
        elif mode == "drag":
            self.model.is_sleeping = False
            self.model.cling_edge = None
            self.model.cling_ratio = 0.0
            self.model.voice_state = VoiceState.READY
            self.model.is_dragging = True
        elif mode == "sleep_flat":
            self.model.voice_state = VoiceState.SLEEPING
            self.model.is_sleeping = True
            self.model.sleep_enter_time = now - 5.0
            self.model.cling_edge = None
            self.model.cling_ratio = 0.0
        elif mode == "sleep_corner":
            self.model.voice_state = VoiceState.SLEEPING
            self.model.is_sleeping = True
            self.model.sleep_enter_time = now - 5.0
            self.model.cling_edge = "right"
            self.model.cling_ratio = 1.0
        elif mode == "pop_bubble":
            self.model.is_sleeping = True
            self.model.cling_edge = "right"
            self.model.cling_ratio = 1.0
            self.model.trigger_wake_up(pop_bubble=True)
            self.model.voice_state = VoiceState.READY
        else:
            self.model.is_sleeping = False
            self.model.cling_edge = None
            self.model.cling_ratio = 0.0
            self.model.voice_state = VoiceState.READY
        self.update()

    def _on_tick(self):
        if not self.isVisible():
            return
        self.model.pulse_phase += 0.06
        if self.model.voice_state == VoiceState.SPEAKING:
            import math
            self.model.mouth_open = (math.sin(self.model.pulse_phase * 3.5) + 1.0) / 2.0
        else:
            self.model.mouth_open = 0.0

        now = time.time()
        if self.model.bubble_pop_particles:
            surviving_pop = []
            for bp in self.model.bubble_pop_particles:
                bp["dx"] = bp.get("dx", 0.0) + bp.get("vx", 0.0)
                bp["dy"] = bp.get("dy", 0.0) + bp.get("vy", 0.0)
                bp["vy"] = bp.get("vy", 0.0) + 0.12
                bp["alpha"] = bp.get("alpha", 240) - 12.0
                if bp["alpha"] > 0:
                    surviving_pop.append(bp)
            self.model.bubble_pop_particles = surviving_pop

        if self.model.wake_up_until > 0 and now >= self.model.wake_up_until:
            self.model.is_sleeping = False
            self.model.wake_up_until = 0.0

        self.update()

    def paintEvent(self, a0):
        super().paintEvent(a0)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Flat 2D circular stage background
        painter.setPen(QPen(QColor("#2A2E39"), 1.2))
        painter.setBrush(QBrush(QColor("#22252E")))
        painter.drawEllipse(QRectF(4.0, 4.0, self._size - 8.0, self._size - 8.0))

        if self._renderer:
            pad = 8.0
            avail = float(self._size) - pad * 2.0
            scale = avail / 120.0
            painter.save()
            painter.translate(pad, pad)
            painter.scale(scale, scale)
            try:
                self._renderer.paint(painter, 120, 120, self.model)
            except Exception:
                pass
            painter.restore()


class InventoryCard(QFrame):
    """Flat 2D character card for the 3-column inventory grid."""

    clicked = pyqtSignal(str)

    def __init__(
        self,
        char: CharacterDef,
        is_owned: bool,
        count: int,
        is_equipped: bool,
        is_selected: bool,
        parent=None,
    ):
        super().__init__(parent)
        self.char = char
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(140)

        is_exclusive = getattr(char, "is_exclusive", False) or (char.id == "aemeath_idol")
        r_info = RARITY_INFO.get(char.rarity, {})
        r_color = "#F43F5E" if is_exclusive else r_info.get("color", "#9CA3AF")
        r_label = "★ TỐI THƯỢNG ★" if is_exclusive else r_info.get("label", "Thường")

        if is_selected:
            bg_col = "#2F1E2A" if is_exclusive else "#282D3A"
            border_style = "2px solid #F43F5E" if is_exclusive else "1.5px solid #5B8BB2"
        elif is_equipped:
            bg_col = "#2A1826" if is_exclusive else "#242934"
            border_style = "2px solid #F43F5E" if is_exclusive else "1.5px solid #4A7C6B"
        elif is_owned:
            bg_col = "#241622" if is_exclusive else "#22252E"
            border_style = "1.5px solid #F43F5E" if is_exclusive else "1px solid #2E323E"
        else:
            bg_col = "#1E131C" if is_exclusive else "#1C1F26"
            border_style = "1px solid #701A28" if is_exclusive else "1px solid #262932"

        self.setStyleSheet(f"""
            InventoryCard {{
                background: {bg_col};
                border: {border_style};
                border-radius: 9px;
            }}
            InventoryCard:hover {{
                background: {"#382030" if is_exclusive else "#2A2F3D"};
                border: 1.5px solid {"#FDA4AF" if is_exclusive else "#5B8BB2"};
            }}
            InventoryCard QLabel {{
                border: none;
                background: transparent;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Top row: Rarity Pill (left) + Status (right)
        top_row = QHBoxLayout()
        top_row.setSpacing(4)

        tag = QLabel(r_label)
        if is_exclusive:
            tag.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #881337, stop:0.5 #F43F5E, stop:1 #D97706);
                color: #FFFFFF;
                font-weight: 800;
                font-size: 8px;
                padding: 2px 6px;
                border-radius: 4px;
            """)
        else:
            tag.setStyleSheet(f"""
                background: #181A20;
                color: {r_color};
                font-weight: 700;
                font-size: 9px;
                padding: 2px 6px;
                border-radius: 4px;
            """)
        top_row.addWidget(tag)

        if is_exclusive:
            music_badge = QLabel("♪ Nhạc")
            music_badge.setStyleSheet("""
                background: #3B0764;
                color: #F0ABFC;
                font-size: 8px;
                font-weight: 700;
                padding: 2px 4px;
                border-radius: 3px;
                border: 0.5px solid #A855F7;
            """)
            top_row.addWidget(music_badge)

        top_row.addStretch()

        if is_equipped:
            eq_badge = QLabel("Đang dùng")
            eq_badge.setStyleSheet("""
                background: #3A6B5C;
                color: #F3F4F6;
                font-size: 9px;
                font-weight: 700;
                border-radius: 4px;
                padding: 2px 5px;
            """)
            top_row.addWidget(eq_badge)
        elif is_owned:
            cnt_badge = QLabel(f"x{count}" if count > 1 else "Đã mở")
            cnt_badge.setStyleSheet("color: #9CA3AF; font-size: 9px; font-weight: 600;")
            top_row.addWidget(cnt_badge)
        else:
            lock_badge = QLabel("Chưa mở")
            lock_badge.setStyleSheet("color: #6B7280; font-size: 9px; font-weight: 600;")
            top_row.addWidget(lock_badge)

        layout.addLayout(top_row)

        # Mascot Avatar Preview (64x64)
        self.preview = CharacterPreviewWidget(
            char, size=64, animated=(char.rarity in ("mythic", "legendary") or is_exclusive)
        )
        layout.addWidget(self.preview, alignment=Qt.AlignmentFlag.AlignCenter)

        # Character Name
        name_lbl = QLabel(char.name)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_col = "#E5E7EB" if is_owned else "#6B7280"
        name_lbl.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {name_col};")
        layout.addWidget(name_lbl)

    def mousePressEvent(self, a0):
        if a0 is not None and a0.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.char.id)
            a0.accept()
        super().mousePressEvent(a0)


class InventoryTab(QWidget):
    """Collection inventory view with flat 2D filter bar and right-side Character Studio."""

    equipChanged = pyqtSignal(str)
    switchToShopRequested = pyqtSignal()

    def __init__(self, service: CollectionService, parent=None):
        super().__init__(parent)
        self.service = service
        self.selected_id: Optional[str] = None
        self.current_filter: str = "all"
        self.filter_buttons: dict[str, QPushButton] = {}
        self._active_pose: str = "idle"
        self._pose_buttons: dict[str, QPushButton] = {}
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(10)

        # ============================================================
        # 1. FULL-WIDTH TOP TOOLBAR: FLAT 2D FILTER PILLS + PROGRESS
        # ============================================================
        toolbar = QFrame()
        toolbar.setObjectName("invToolbar")
        toolbar.setFixedHeight(44)
        toolbar.setStyleSheet("""
            QFrame#invToolbar {
                background: #22252E;
                border: 1px solid #2E323E;
                border-radius: 9px;
            }
            QFrame#invToolbar QLabel {
                border: none;
                background: transparent;
            }
        """)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(10, 6, 12, 6)
        tb_layout.setSpacing(6)

        filters = [
            ("all", "Tất Cả"),
            ("owned", "Đã Sở Hữu"),
            ("mythic", "Thần Thoại"),
            ("legendary", "Huyền Thoại"),
            ("epic", "Sử Thi"),
            ("rare", "Hiếm"),
            ("common", "Thường"),
        ]
        for f_key, f_label in filters:
            btn = QPushButton(f_label)
            btn.setFixedHeight(28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=f_key: self._set_filter(k))
            tb_layout.addWidget(btn)
            self.filter_buttons[f_key] = btn

        tb_layout.addStretch()

        self.progress_label = QLabel("Sưu tập: 0/0")
        self.progress_label.setStyleSheet("color: #D1D5DB; font-size: 11px; font-weight: 600;")
        tb_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedSize(90, 6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
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
        tb_layout.addWidget(self.progress_bar)

        root_layout.addWidget(toolbar)

        # ============================================================
        # 2. MAIN BODY: 3-COL GRID (LEFT) + CHARACTER STUDIO (RIGHT)
        # ============================================================
        body_layout = QHBoxLayout()
        body_layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 4, 0)
        self.grid_layout.setSpacing(10)

        scroll.setWidget(self.grid_container)
        body_layout.addWidget(scroll, stretch=1)

        # Right: Flat 2D Character Studio Panel (300px)
        self.inspector = QFrame()
        self.inspector.setObjectName("inspectorFrame")
        self.inspector.setFixedWidth(300)
        self.inspector.setStyleSheet("""
            QFrame#inspectorFrame {
                background: #22252E;
                border: 1px solid #2E323E;
                border-radius: 10px;
            }
            QFrame#inspectorFrame QLabel {
                border: none;
                background: transparent;
            }
        """)
        insp_layout = QVBoxLayout(self.inspector)
        insp_layout.setContentsMargins(16, 14, 16, 14)
        insp_layout.setSpacing(10)

        # Top Header: Character Name + Rarity Pill
        hdr_row = QHBoxLayout()
        self.insp_title = QLabel("Chi Tiết Nhân Vật")
        self.insp_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #F3F4F6;")
        hdr_row.addWidget(self.insp_title)
        hdr_row.addStretch()

        self.insp_rarity = QLabel("THẦN THOẠI")
        self.insp_rarity.setStyleSheet("font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 4px;")
        hdr_row.addWidget(self.insp_rarity)
        insp_layout.addLayout(hdr_row)

        self.insp_count = QLabel("")
        self.insp_count.setStyleSheet("font-size: 11px; font-weight: 600; color: #9CA3AF;")
        insp_layout.addWidget(self.insp_count)

        # Flat Recessed Studio Stage Box (#1C1F26)
        stage_box = QFrame()
        stage_box.setObjectName("studioStageBox")
        stage_box.setStyleSheet("""
            QFrame#studioStageBox {
                background: #1C1F26;
                border: 1px solid #2A2E39;
                border-radius: 8px;
            }
        """)
        stage_box_layout = QVBoxLayout(stage_box)
        stage_box_layout.setContentsMargins(10, 10, 10, 10)
        stage_box_layout.setSpacing(8)

        self.insp_preview = InteractiveCharacterStage(size=140)
        stage_box_layout.addWidget(self.insp_preview, alignment=Qt.AlignmentFlag.AlignCenter)

        # Flat 2D 6-button Pose & Voice bar inside Stage Box
        pose_row = QHBoxLayout()
        pose_row.setSpacing(3)
        poses = [
            ("idle", "Đứng"),
            ("talk", "Nói"),
            ("music", "Nhạc/YT"),
            ("drag", "Kéo"),
            ("sleep_corner", "Ngủ"),
            ("pop_bubble", "Dậy"),
        ]
        for p_key, p_label in poses:
            p_btn = QPushButton(p_label)
            p_btn.setFixedHeight(26)
            p_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            p_btn.clicked.connect(lambda checked, m=p_key: self._on_pose_selected(m))
            pose_row.addWidget(p_btn)
            self._pose_buttons[p_key] = p_btn

        stage_box_layout.addLayout(pose_row)
        insp_layout.addWidget(stage_box)

        # Description
        self.insp_desc = QLabel("Chọn một nhân vật bên trái để xem chi tiết, thử biểu cảm và trang bị.")
        self.insp_desc.setWordWrap(True)
        self.insp_desc.setStyleSheet("font-size: 11px; color: #9CA3AF; line-height: 1.35;")
        insp_layout.addWidget(self.insp_desc)

        insp_layout.addStretch()

        # Flat 2D Primary Equip Button
        self.equip_btn = QPushButton("Trang Bị Nhân Vật")
        self.equip_btn.setFixedHeight(38)
        self.equip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.equip_btn.setStyleSheet("""
            QPushButton {
                background: #3D6B8E;
                color: #F3F4F6;
                font-size: 13px;
                font-weight: 700;
                border-radius: 7px;
                border: none;
            }
            QPushButton:hover {
                background: #487CA3;
            }
            QPushButton:pressed {
                background: #335978;
            }
            QPushButton:disabled {
                background: #1C1F26;
                color: #6B7280;
                border: 1px solid #2A2E39;
            }
        """)
        self.equip_btn.clicked.connect(self._on_equip_clicked)
        insp_layout.addWidget(self.equip_btn)

        body_layout.addWidget(self.inspector)
        root_layout.addLayout(body_layout, stretch=1)

        self._update_filter_styles()
        self._update_pose_styles()

    def _set_filter(self, f_key: str):
        self.current_filter = f_key
        self._update_filter_styles()
        self.refresh()

    def _update_filter_styles(self):
        for k, btn in self.filter_buttons.items():
            if k == self.current_filter:
                btn.setStyleSheet("""
                    QPushButton {
                        background: #3D6B8E;
                        color: #F3F4F6;
                        font-size: 11px;
                        font-weight: 700;
                        border-radius: 5px;
                        border: none;
                        padding: 0 11px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: #1C1F26;
                        color: #9CA3AF;
                        font-size: 11px;
                        font-weight: 600;
                        border-radius: 5px;
                        border: 1px solid #2A2E39;
                        padding: 0 11px;
                    }
                    QPushButton:hover {
                        background: #2B2F3A;
                        color: #E5E7EB;
                    }
                """)

    def _on_pose_selected(self, mode: str):
        self._active_pose = mode
        self._update_pose_styles()
        self.insp_preview.set_preview_mode(mode)
        if mode in ("talk", "pop_bubble"):
            self._play_selected_voice_sfx()

    def _update_pose_styles(self):
        for k, btn in self._pose_buttons.items():
            if k == self._active_pose:
                btn.setStyleSheet("""
                    QPushButton {
                        background: #3D6B8E;
                        color: #F3F4F6;
                        font-size: 10px;
                        font-weight: 700;
                        border-radius: 5px;
                        border: none;
                        padding: 0 6px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: #22252E;
                        color: #9CA3AF;
                        font-size: 10px;
                        font-weight: 600;
                        border-radius: 5px;
                        border: 1px solid #2E323E;
                        padding: 0 6px;
                    }
                    QPushButton:hover {
                        background: #2B2F3A;
                        color: #E5E7EB;
                    }
                """)

    def _play_selected_voice_sfx(self):
        if self.selected_id not in ("phoebe_chuby", "nono_chubby", "aemeath_idol"):
            return
        try:
            import os
            from utils.paths import resource_path
            from utils.sound_player import play_wav_safely
            sample_name = "nono_chubby.wav" if self.selected_id == "nono_chubby" else "phoebe_chupi.wav"
            wav_path = resource_path(os.path.join("voice-models", "samples", sample_name))
            play_wav_safely(wav_path)
        except Exception:
            pass

    def refresh(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item is not None:
                w = item.widget()
                if w is not None:
                    w.deleteLater()

        all_chars = list(reversed(self.service.registry.all()))
        owned = self.service.owned()
        equipped_char = self.service.equipped()
        equipped_id = equipped_char.id if equipped_char else "pop"

        if not self.selected_id or self.service.registry.get(self.selected_id) is None:
            self.selected_id = equipped_id

        owned_count = sum(1 for c in all_chars if c.id in owned)
        total_count = len(all_chars)
        pct = int((owned_count / total_count * 100)) if total_count > 0 else 0
        self.progress_label.setText(f"Bộ sưu tập: {owned_count}/{total_count} ({pct}%)")
        self.progress_bar.setMaximum(max(1, total_count))
        self.progress_bar.setValue(owned_count)

        filtered: List[CharacterDef] = []
        for c in all_chars:
            if self.current_filter == "all":
                filtered.append(c)
            elif self.current_filter == "owned":
                if c.id in owned:
                    filtered.append(c)
            elif c.rarity == self.current_filter:
                filtered.append(c)

        cols = 3
        for idx, char in enumerate(filtered):
            is_owned = char.id in owned
            count = owned.get(char.id, 0)
            is_eq = (char.id == equipped_id)
            is_sel = (char.id == self.selected_id)

            card = InventoryCard(char, is_owned, count, is_eq, is_sel)
            card.clicked.connect(self._on_card_selected)

            row = idx // cols
            col = idx % cols
            self.grid_layout.addWidget(card, row, col)

        self.grid_layout.setRowStretch((len(filtered) // cols) + 1, 1)
        self._update_inspector()

    def _on_card_selected(self, char_id: str):
        if self.selected_id != char_id:
            self._active_pose = "idle"
            self._update_pose_styles()
        self.selected_id = char_id
        self.refresh()

    def _update_inspector(self):
        char = self.service.registry.get(self.selected_id or "pop")
        if not char:
            return

        owned = self.service.owned()
        is_owned = char.id in owned
        count = owned.get(char.id, 0)
        equipped_char = self.service.equipped()
        equipped_id = equipped_char.id if equipped_char else "pop"
        is_equipped = (char.id == equipped_id)

        is_exclusive = getattr(char, "is_exclusive", False) or (char.id == "aemeath_idol")
        r_info = RARITY_INFO.get(char.rarity, {})
        r_color = "#F43F5E" if is_exclusive else r_info.get("color", "#9CA3AF")
        r_label = "★ ĐỘC QUYỀN ÂM NHẠC — THẦN THOẠI TỐI THƯỢNG ★" if is_exclusive else r_info.get("label", "Thường").upper()

        self.insp_title.setText(char.name)
        self.insp_rarity.setText(r_label)
        if is_exclusive:
            self.insp_rarity.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #881337, stop:0.5 #F43F5E, stop:1 #D97706);
                color: #FFFFFF;
                border: 1px solid #FDA4AF;
                font-size: 9.5px;
                font-weight: 800;
                padding: 4px 10px;
                border-radius: 5px;
            """)
            if "music" in self._pose_buttons:
                self._pose_buttons["music"].setText("♪ Nhạc (19f) ♪")
        else:
            self.insp_rarity.setStyleSheet(f"""
                background: #181A20;
                color: {r_color};
                border: 1px solid #2E323E;
                font-size: 10px;
                font-weight: 700;
                padding: 3px 8px;
                border-radius: 4px;
            """)
            if "music" in self._pose_buttons:
                self._pose_buttons["music"].setText("Nhạc/YT")
        self.insp_preview.set_character(char)
        self.insp_desc.setText(char.description)

        if is_owned:
            self.insp_count.setText(f"Trạng thái: Đã sở hữu trong kho (x{count})")
            if is_equipped:
                self.equip_btn.setEnabled(False)
                self.equip_btn.setText("Đang Đồng Hành Trên Màn Hình")
            else:
                self.equip_btn.setEnabled(True)
                self.equip_btn.setText("Trang Bị Nhân Vật")
        else:
            self.insp_count.setText(f"Chưa mở khóa  •  Giá: {char.price:,} Xu hoặc {r_info.get('shard_cost', 100)} Mảnh")
            self.equip_btn.setEnabled(False)
            self.equip_btn.setText("Chưa Sở Hữu")

    def _on_equip_clicked(self):
        if not self.selected_id:
            return
        outcome = self.service.equip(self.selected_id)
        if outcome.ok:
            self.refresh()
            self.equipChanged.emit(self.selected_id)
        else:
            QMessageBox.information(self, "Trang Bị", outcome.message)
