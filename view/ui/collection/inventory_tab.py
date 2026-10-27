"""
Inventory Tab - Player's Collection Backpack.
View owned characters, collection progress, character stats, and equip mascot skins.
Styled to match POP AI View design system with no emoji icons.
"""

from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QProgressBar, QMessageBox
)
from service.collection.character_registry import RARITY_INFO, CharacterDef
from service.collection.collection_service import CollectionService
from view.ui.collection.character_preview_widget import CharacterPreviewWidget
from view.ui.styles import DesignTokens


class InventoryCard(QFrame):
    """Grid item showing miniature character status and equipped indicator."""

    clicked = pyqtSignal(str)

    def __init__(self, char: CharacterDef, is_owned: bool, count: int, is_equipped: bool, is_selected: bool, parent=None):
        super().__init__(parent)
        self.char = char
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(132)

        r_info = RARITY_INFO.get(char.rarity, {})
        r_color = r_info.get("color", "#94A3B8")
        r_label = r_info.get("label", "Thường")

        border_color = r_color if is_selected else ("#00FFAA" if is_equipped else "rgba(255, 255, 255, 0.08)")
        bg_alpha = "0.85" if is_selected else ("0.75" if is_owned else "0.35")

        self.setStyleSheet(f"""
            InventoryCard {{
                background: rgba(19, 28, 48, {bg_alpha});
                border: {'2px solid' if is_selected or is_equipped else '1px solid'} {border_color};
                border-radius: 10px;
                padding: 6px;
            }}
            InventoryCard:hover {{
                border-color: {r_color};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Top line: Status / count
        top_row = QHBoxLayout()
        if is_equipped:
            eq_badge = QLabel("ĐANG DÙNG")
            eq_badge.setStyleSheet(f"background: {DesignTokens.CYAN}; color: #040812; font-size: 9px; font-weight: 800; border-radius: 4px; padding: 2px 5px;")
            top_row.addWidget(eq_badge)
        elif is_owned and count > 1:
            cnt_badge = QLabel(f"x{count}")
            cnt_badge.setStyleSheet(f"color: {DesignTokens.TEXT_SECONDARY}; font-size: 10px; font-weight: 700;")
            top_row.addWidget(cnt_badge)
        top_row.addStretch()

        tag = QLabel(r_label[:1])  # First letter (T, H, S, H, T)
        tag.setToolTip(r_label)
        tag.setStyleSheet(f"color: {r_color}; font-weight: 700; font-size: 11px;")
        top_row.addWidget(tag)
        layout.addLayout(top_row)

        # Mascot Avatar Preview
        self.preview = CharacterPreviewWidget(char, size=46)
        layout.addWidget(self.preview, alignment=Qt.AlignmentFlag.AlignCenter)

        # Name
        name_lbl = QLabel(char.name)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setWordWrap(True)
        name_col = DesignTokens.TEXT_MAIN if is_owned else DesignTokens.TEXT_MUTED
        name_lbl.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {name_col};")
        layout.addWidget(name_lbl)

        layout.addStretch()

    def mousePressEvent(self, a0):
        if a0 is not None and a0.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.char.id)
            a0.accept()
        super().mousePressEvent(a0)


class InventoryTab(QWidget):
    """Collection inventory view with character inspector and equip functionality."""

    equipChanged = pyqtSignal(str)

    def __init__(self, service: CollectionService, parent=None):
        super().__init__(parent)
        self.service = service
        self.selected_id: Optional[str] = None
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 16)
        main_layout.setSpacing(16)

        # ---------------- Left side: Grid of characters ----------------
        left_box = QVBoxLayout()
        left_box.setSpacing(10)

        # Progress bar
        self.progress_label = QLabel("Bộ sưu tập: 0/0")
        self.progress_label.setStyleSheet(f"color: {DesignTokens.TEXT_SECONDARY}; font-size: 12px; font-weight: 600;")
        left_box.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: rgba(255, 255, 255, 0.08);
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: {DesignTokens.GRADIENT_BLUE_GREEN};
                border-radius: 3px;
            }}
        """)
        left_box.addWidget(self.progress_bar)

        # Scroll grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(8)

        scroll.setWidget(self.grid_container)
        left_box.addWidget(scroll, stretch=1)

        main_layout.addLayout(left_box, stretch=3)

        # ---------------- Right side: Character Inspector ----------------
        self.inspector = QFrame()
        self.inspector.setObjectName("inspectorFrame")
        self.inspector.setFixedWidth(240)
        self.inspector.setStyleSheet(f"""
            QFrame#inspectorFrame {{
                background: {DesignTokens.SURFACE_2};
                border: 1px solid;
                border-color: {DesignTokens.BORDER_GRADIENT};
                border-radius: 12px;
                padding: 14px;
            }}
            QFrame#inspectorFrame QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        insp_layout = QVBoxLayout(self.inspector)
        insp_layout.setContentsMargins(14, 14, 14, 14)
        insp_layout.setSpacing(10)

        self.insp_title = QLabel("Chi Tiết")
        self.insp_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {DesignTokens.TEXT_MAIN};")
        insp_layout.addWidget(self.insp_title)

        self.insp_rarity = QLabel("")
        self.insp_rarity.setStyleSheet("font-size: 11px; font-weight: 700;")
        insp_layout.addWidget(self.insp_rarity)

        # Mascot Avatar Preview
        self.insp_preview = CharacterPreviewWidget(size=80)
        insp_layout.addWidget(self.insp_preview, alignment=Qt.AlignmentFlag.AlignCenter)

        self.insp_desc = QLabel("Chọn một nhân vật bên trái để xem chi tiết và trang bị.")
        self.insp_desc.setWordWrap(True)
        self.insp_desc.setStyleSheet(f"font-size: 12px; color: {DesignTokens.TEXT_SECONDARY}; line-height: 1.4;")
        insp_layout.addWidget(self.insp_desc)

        insp_layout.addStretch()

        self.insp_count = QLabel("")
        self.insp_count.setStyleSheet(f"font-size: 11px; color: {DesignTokens.TEXT_MUTED};")
        insp_layout.addWidget(self.insp_count)

        self.equip_btn = QPushButton("Trang Bị")
        self.equip_btn.setFixedHeight(38)
        self.equip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.equip_btn.setStyleSheet(f"""
            QPushButton {{
                background: {DesignTokens.GRADIENT_BLUE_GREEN};
                color: #040812;
                font-size: 13px;
                font-weight: 700;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0077D6, stop:1 #00E699);
            }}
            QPushButton:disabled {{
                background: rgba(255, 255, 255, 0.05);
                color: #64748B;
            }}
        """)
        self.equip_btn.clicked.connect(self._on_equip_clicked)
        insp_layout.addWidget(self.equip_btn)

        main_layout.addWidget(self.inspector, stretch=2)

    def refresh(self):
        # Clear grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item is not None:
                w = item.widget()
                if w is not None:
                    w.deleteLater()

        all_chars = self.service.registry.all()
        owned = self.service.owned()
        equipped_char = self.service.equipped()
        equipped_id = equipped_char.id if equipped_char else "pop"

        if not self.selected_id or self.service.registry.get(self.selected_id) is None:
            self.selected_id = equipped_id

        # Update progress
        owned_count = sum(1 for c in all_chars if c.id in owned)
        total_count = len(all_chars)
        pct = int((owned_count / total_count * 100)) if total_count > 0 else 0
        self.progress_label.setText(f"Bộ sưu tập: {owned_count}/{total_count} nhân vật ({pct}%)")
        self.progress_bar.setMaximum(total_count)
        self.progress_bar.setValue(owned_count)

        cols = 3
        for idx, char in enumerate(all_chars):
            is_owned = char.id in owned
            count = owned.get(char.id, 0)
            is_eq = (char.id == equipped_id)
            is_sel = (char.id == self.selected_id)

            card = InventoryCard(char, is_owned, count, is_eq, is_sel)
            card.clicked.connect(self._on_card_selected)

            row = idx // cols
            col = idx % cols
            self.grid_layout.addWidget(card, row, col)

        self._update_inspector()

    def _on_card_selected(self, char_id: str):
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

        r_info = RARITY_INFO.get(char.rarity, {})
        r_color = r_info.get("color", "#94A3B8")
        r_label = r_info.get("label", "Thường")

        self.insp_title.setText(char.name)
        self.insp_rarity.setText(f"Độ hiếm: {r_label}")
        self.insp_rarity.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {r_color};")
        self.insp_preview.set_character(char)
        self.insp_desc.setText(char.description)

        if is_owned:
            self.insp_count.setText(f"Số lượng sở hữu: x{count}")
            if is_equipped:
                self.equip_btn.setEnabled(False)
                self.equip_btn.setText("Đang Trang Bị")
            else:
                self.equip_btn.setEnabled(True)
                self.equip_btn.setText("Trang Bị")
        else:
            self.insp_count.setText("Trạng thái: Chưa sở hữu")
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
