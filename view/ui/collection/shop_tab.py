"""
Shop Tab - Flat 2D Mascot Character & Energy Core Store.
Styled with flat 2D surfaces and natural muted colors without gradients.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QMessageBox
)
from service.collection.character_registry import RARITY_INFO, CharacterDef, rarity_rank
from service.collection.collection_service import CollectionService, EGG_PRICE
from view.ui.collection.character_preview_widget import CharacterPreviewWidget


class CharacterShopCard(QFrame):
    """Flat 2D vertical showcase card for the 3-column store grid."""

    buyClicked = pyqtSignal(str)
    exchangeClicked = pyqtSignal(str)
    equipClicked = pyqtSignal(str)

    def __init__(
        self,
        char: CharacterDef,
        is_owned: bool,
        is_equipped: bool,
        coins: int,
        shards: int,
        parent=None,
    ):
        super().__init__(parent)
        self.char = char
        self.is_owned = is_owned
        self.is_equipped = is_equipped
        self.coins = coins
        self.shards = shards

        r_info = RARITY_INFO.get(char.rarity, {})
        is_exclusive = getattr(char, "is_exclusive", False) or (char.id == "aemeath_idol")
        r_color = "#F43F5E" if is_exclusive else r_info.get("color", "#9CA3AF")
        r_label = "★ TỐI THƯỢNG ★" if is_exclusive else r_info.get("label", "Thường")
        shard_cost = r_info.get("shard_cost", 100)

        self.setFixedHeight(216)
        bg_col = "#241622" if is_exclusive else "#22252E"
        border_col = "#F43F5E" if is_exclusive else ("#4A7C6B" if is_equipped else "#2E323E")
        hover_bg = "#321C2C" if is_exclusive else "#272B36"
        hover_border = "#FDA4AF" if is_exclusive else "#5B8BB2"

        self.setStyleSheet(f"""
            CharacterShopCard {{
                background: {bg_col};
                border: {"1.5px solid " + border_col if is_exclusive else "1px solid " + border_col};
                border-radius: 10px;
            }}
            CharacterShopCard:hover {{
                background: {hover_bg};
                border: 1.5px solid {hover_border};
            }}
            CharacterShopCard QLabel {{
                background: transparent;
                border: none;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(6)

        # 1. Top Row: Flat Rarity Tag (Left) + Shard Progress / Status (Right)
        top_row = QHBoxLayout()
        top_row.setSpacing(4)

        tag = QLabel(r_label)
        if is_exclusive:
            tag.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #881337, stop:0.5 #F43F5E, stop:1 #D97706);
                color: #FFFFFF;
                font-size: 8.5px;
                font-weight: 800;
                padding: 2px 7px;
                border-radius: 4px;
            """)
        else:
            tag.setStyleSheet(f"""
                background: #181A20;
                color: {r_color};
                font-size: 10px;
                font-weight: 700;
                padding: 2px 7px;
                border-radius: 4px;
            """)
        top_row.addWidget(tag)

        if is_exclusive:
            music_tag = QLabel("♪ 19f GIF")
            music_tag.setStyleSheet("""
                background: #3B0764;
                color: #F0ABFC;
                font-size: 8px;
                font-weight: 700;
                padding: 2px 5px;
                border-radius: 3px;
                border: 0.5px solid #A855F7;
            """)
            top_row.addWidget(music_tag)

        top_row.addStretch()

        if is_owned:
            status_lbl = QLabel("Đã sở hữu")
            status_lbl.setStyleSheet("font-size: 10px; font-weight: 600; color: #7AA2C4;")
            top_row.addWidget(status_lbl)
        else:
            shard_col = "#A78BFA" if shards >= shard_cost else "#6B7280"
            shard_lbl = QLabel(f"Mảnh: {min(shards, shard_cost)}/{shard_cost}")
            shard_lbl.setStyleSheet(f"font-size: 10px; font-weight: 600; color: {shard_col};")
            top_row.addWidget(shard_lbl)

        layout.addLayout(top_row)

        # 2. Centered Flat Avatar Preview (72x72)
        self.preview = CharacterPreviewWidget(
            char,
            size=72,
            animated=(char.rarity in ("mythic", "legendary") or is_exclusive),
        )
        layout.addWidget(self.preview, alignment=Qt.AlignmentFlag.AlignCenter)

        # 3. Character Name & Short Description
        name_lbl = QLabel(char.name)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #F3F4F6;")
        layout.addWidget(name_lbl)

        desc_lbl = QLabel(char.description)
        desc_lbl.setWordWrap(True)
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_lbl.setStyleSheet("font-size: 10px; color: #9CA3AF; min-height: 26px; max-height: 28px;")
        layout.addWidget(desc_lbl)

        layout.addStretch()

        # 4. Bottom Action Row (100% Flat 2D Buttons)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        if is_owned:
            if is_equipped:
                eq_badge = QLabel("Đang Đồng Hành")
                eq_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                eq_badge.setFixedHeight(30)
                eq_badge.setStyleSheet("""
                    background: #1C1F26;
                    color: #9CA3AF;
                    font-weight: 600;
                    font-size: 11px;
                    border-radius: 6px;
                    border: 1px solid #2A2E39;
                """)
                btn_row.addWidget(eq_badge)
            else:
                equip_btn = QPushButton("Trang Bị Ngay")
                equip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                equip_btn.setFixedHeight(30)
                equip_btn.setStyleSheet("""
                    QPushButton {
                        background: #3A6B5C;
                        color: #F3F4F6;
                        font-size: 11px;
                        font-weight: 700;
                        border-radius: 6px;
                        border: none;
                    }
                    QPushButton:hover {
                        background: #467E6D;
                    }
                    QPushButton:pressed {
                        background: #315B4E;
                    }
                """)
                equip_btn.clicked.connect(lambda: self.equipClicked.emit(self.char.id))
                btn_row.addWidget(equip_btn)
        else:
            can_coin = coins >= char.price
            buy_btn = QPushButton(f"{char.price:,} Xu")
            buy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            buy_btn.setFixedHeight(30)
            if can_coin:
                buy_btn.setToolTip(f"Mua {char.name} bằng {char.price:,} Xu")
                buy_btn.setStyleSheet("""
                    QPushButton {
                        background: #3D6B8E;
                        color: #F3F4F6;
                        font-size: 11px;
                        font-weight: 700;
                        border-radius: 6px;
                        border: none;
                        padding: 0 8px;
                    }
                    QPushButton:hover {
                        background: #487CA3;
                    }
                    QPushButton:pressed {
                        background: #335978;
                    }
                """)
            else:
                buy_btn.setToolTip(f"Còn thiếu {char.price - coins:,} Xu")
                buy_btn.setStyleSheet("""
                    QPushButton {
                        background: #1C1F26;
                        color: #9CA3AF;
                        font-size: 11px;
                        font-weight: 600;
                        border-radius: 6px;
                        border: 1px solid #2E323E;
                        padding: 0 8px;
                    }
                    QPushButton:hover {
                        background: #2B2F3A;
                        color: #E5E7EB;
                    }
                """)
            buy_btn.clicked.connect(lambda: self.buyClicked.emit(self.char.id))
            btn_row.addWidget(buy_btn, stretch=1)

            can_shard = shards >= shard_cost
            shard_btn = QPushButton(f"{shard_cost} Mảnh")
            shard_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            shard_btn.setFixedHeight(30)
            if can_shard:
                shard_btn.setToolTip(f"Đổi {char.name} bằng {shard_cost} Mảnh")
                shard_btn.setStyleSheet("""
                    QPushButton {
                        background: #695678;
                        color: #F3F4F6;
                        font-size: 11px;
                        font-weight: 700;
                        border-radius: 6px;
                        border: none;
                        padding: 0 8px;
                    }
                    QPushButton:hover {
                        background: #78638A;
                    }
                    QPushButton:pressed {
                        background: #594866;
                    }
                """)
            else:
                shard_btn.setToolTip(f"Còn thiếu {shard_cost - shards} Mảnh")
                shard_btn.setStyleSheet("""
                    QPushButton {
                        background: #1C1F26;
                        color: #6B7280;
                        font-size: 11px;
                        font-weight: 600;
                        border-radius: 6px;
                        border: 1px solid #2A2E39;
                        padding: 0 8px;
                    }
                    QPushButton:hover {
                        background: #2B2F3A;
                        color: #D1D5DB;
                    }
                """)
            shard_btn.clicked.connect(lambda: self.exchangeClicked.emit(self.char.id))
            btn_row.addWidget(shard_btn, stretch=1)

        layout.addLayout(btn_row)


class ShopTab(QWidget):
    """Storefront for Mascots & Energy Cores with flat 2D toolbar and 3-column showcase grid."""

    itemPurchased = pyqtSignal()
    equipRequested = pyqtSignal(str)

    def __init__(self, service: CollectionService, parent=None):
        super().__init__(parent)
        self.service = service
        self._active_filter = "all"
        self._filter_buttons: dict[str, QPushButton] = {}
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 1. Flat 2D 44px Top Toolbar: Filters (Left) + Quick Core Pack Supply (Right)
        toolbar = QFrame()
        toolbar.setObjectName("shopToolbar")
        toolbar.setFixedHeight(44)
        toolbar.setStyleSheet("""
            QFrame#shopToolbar {
                background: #22252E;
                border: 1px solid #2E323E;
                border-radius: 9px;
            }
            QFrame#shopToolbar QLabel {
                background: transparent;
                border: none;
            }
        """)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(10, 6, 10, 6)
        tb_layout.setSpacing(6)

        filters = [
            ("all", "Tất Cả"),
            ("unowned", "Chưa Sở Hữu"),
            ("mythic", "Thần Thoại"),
            ("legendary", "Huyền Thoại"),
            ("epic", "Sử Thi"),
            ("rare", "Hiếm"),
            ("common", "Thường"),
        ]
        for key, label in filters:
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda checked, k=key: self._set_filter(k))
            tb_layout.addWidget(btn)
            self._filter_buttons[key] = btn

        tb_layout.addStretch()

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #9CA3AF;")
        tb_layout.addWidget(self.count_lbl)

        layout.addWidget(toolbar)

        # 2. Scroll Area for 3-Column Character Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        self.cards_container = QWidget()
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 4, 4)
        self.cards_layout.setSpacing(10)

        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll, stretch=1)

        self._update_filter_styles()

    def _set_filter(self, key: str):
        self._active_filter = key
        self._update_filter_styles()
        self.refresh()

    def _update_filter_styles(self):
        for key, btn in self._filter_buttons.items():
            if key == self._active_filter:
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

    def refresh(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item is not None:
                w = item.widget()
                if w is not None:
                    w.deleteLater()

        w = self.service.wallet()
        coins = int(w.get("coins", 0))
        shards = int(w.get("shards", 0))
        equipped_id = w.get("equipped", "pop_default")
        owned = self.service.owned()

        all_items = sorted(
            self.service.registry.shop_items(),
            key=lambda c: (-rarity_rank(c.rarity), c.price * -1, c.name),
        )

        filtered: list[CharacterDef] = []
        for c in all_items:
            if self._active_filter == "all":
                filtered.append(c)
            elif self._active_filter == "unowned":
                if c.id not in owned:
                    filtered.append(c)
            else:
                if c.rarity == self._active_filter:
                    filtered.append(c)

        cols = 3
        self.count_lbl.setText(f"Hiển thị: {len(filtered)}/{len(all_items)} nhân vật")
        for idx, char in enumerate(filtered):
            is_owned = char.id in owned
            is_equipped = char.id == equipped_id
            card = CharacterShopCard(char, is_owned, is_equipped, coins, shards)
            card.buyClicked.connect(self._on_buy_clicked)
            card.exchangeClicked.connect(self._on_exchange_clicked)
            card.equipClicked.connect(self._on_equip_clicked)

            row = idx // cols
            col = idx % cols
            self.cards_layout.addWidget(card, row, col)

        self.cards_layout.setRowStretch((len(filtered) // cols) + 1, 1)

    def _on_buy_core_pack(self, qty: int):
        outcome = self.service.buy_egg(qty)
        if outcome.ok:
            self.refresh()
            self.itemPurchased.emit()
            QMessageBox.information(self, "Nạp Lõi Thành Công", outcome.message)
        else:
            QMessageBox.information(self, "Nạp Lõi Năng Lượng", outcome.message)

    def _on_equip_clicked(self, char_id: str):
        outcome = self.service.equip(char_id)
        if outcome.ok:
            self.refresh()
            self.equipRequested.emit(char_id)

    def _on_buy_clicked(self, char_id: str):
        char = self.service.registry.get(char_id)
        if not char:
            return
        w = self.service.wallet()
        coins = int(w.get("coins", 0))
        if coins < char.price:
            needed = char.price - coins
            QMessageBox.information(
                self,
                "Chưa Đủ Pop Xu",
                f"Bạn cần thêm {needed:,} Xu để sở hữu {char.name}!\n\n"
                f"• Hiện có: {coins:,} Xu\n"
                f"• Giá niêm yết: {char.price:,} Xu\n\n"
                f"Mẹo kiếm thêm Xu:\n"
                f"- Điểm danh hằng ngày (+50 Xu/ngày)\n"
                f"- Tương tác giọng nói với Mascot (+5 Xu/lệnh)\n"
                f"- Mở Lõi Năng Lượng tại tab Triệu Hồi chỉ với {EGG_PRICE} Xu/lần",
            )
            return

        outcome = self.service.buy_character(char_id)
        if outcome.ok:
            QMessageBox.information(self, "Mở Khóa Thành Công", outcome.message)
            self.refresh()
            self.itemPurchased.emit()
        else:
            QMessageBox.information(self, "Cửa Hàng", outcome.message)

    def _on_exchange_clicked(self, char_id: str):
        char = self.service.registry.get(char_id)
        if not char:
            return
        r_info = RARITY_INFO.get(char.rarity, {})
        shard_cost = r_info.get("shard_cost", 100)
        w = self.service.wallet()
        shards = int(w.get("shards", 0))
        if shards < shard_cost:
            needed = shard_cost - shards
            QMessageBox.information(
                self,
                "Chưa Đủ Mảnh Nhân Vật",
                f"Bạn cần thêm {needed:,} Mảnh để quy đổi {char.name}!\n\n"
                f"• Hiện có: {shards:,} Mảnh\n"
                f"• Yêu cầu: {shard_cost:,} Mảnh\n\n"
                f"Mẹo nhận Mảnh:\n"
                f"- Khi Triệu Hồi Gacha trúng nhân vật đã sở hữu, hệ thống sẽ tự động tách thành Mảnh.",
            )
            return

        outcome = self.service.exchange_shards(char_id)
        if outcome.ok:
            QMessageBox.information(self, "Quy Đổi Thành Công", outcome.message)
            self.refresh()
            self.itemPurchased.emit()
        else:
            QMessageBox.information(self, "Quy Đổi Mảnh", outcome.message)
