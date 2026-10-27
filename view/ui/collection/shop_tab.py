"""
Shop Tab - Mascot Character Store.
Allows direct purchasing using Pop Coins or exchanging character Shards.
Styled with POP AI View design system and no emoji icons.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QMessageBox
)
from service.collection.character_registry import RARITY_INFO, CharacterDef
from service.collection.collection_service import CollectionService
from view.ui.collection.character_preview_widget import CharacterPreviewWidget
from view.ui.styles import DesignTokens


class CharacterShopCard(QFrame):
    """Product card displaying character visual avatar, info, rarity badge, and purchase options."""

    buyClicked = pyqtSignal(str)
    exchangeClicked = pyqtSignal(str)

    def __init__(self, char: CharacterDef, is_owned: bool, coins: int, shards: int, parent=None):
        super().__init__(parent)
        self.char = char
        self.is_owned = is_owned
        self.coins = coins
        self.shards = shards

        r_info = RARITY_INFO.get(char.rarity, {})
        r_color = r_info.get("color", "#94A3B8")
        r_label = r_info.get("label", "Thường")
        shard_cost = r_info.get("shard_cost", 100)

        self.setStyleSheet(f"""
            CharacterShopCard {{
                background: {DesignTokens.SURFACE_2};
                border: 1px solid;
                border-color: {DesignTokens.BORDER_GRADIENT};
                border-radius: 12px;
                padding: 10px;
            }}
            CharacterShopCard:hover {{
                border-color: {r_color};
                background: rgba(26, 38, 64, 0.85);
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Content Row: Avatar Preview (Left) + Details (Right)
        content_row = QHBoxLayout()
        content_row.setSpacing(12)

        # Mascot Avatar Preview
        self.preview = CharacterPreviewWidget(char, size=68)
        content_row.addWidget(self.preview, alignment=Qt.AlignmentFlag.AlignTop)

        # Details Column
        details_layout = QVBoxLayout()
        details_layout.setSpacing(4)

        # Header: Name + Rarity Tag
        hdr = QHBoxLayout()
        name_lbl = QLabel(char.name)
        name_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {DesignTokens.TEXT_MAIN};")
        hdr.addWidget(name_lbl)

        hdr.addStretch()

        tag = QLabel(r_label)
        tag.setStyleSheet(f"""
            background: rgba({QColor(r_color).red()}, {QColor(r_color).green()}, {QColor(r_color).blue()}, 0.15);
            color: {r_color};
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
            border: 1px solid {r_color};
        """)
        hdr.addWidget(tag)
        details_layout.addLayout(hdr)

        # Description
        desc_lbl = QLabel(char.description)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f"font-size: 11px; color: {DesignTokens.TEXT_SECONDARY}; min-height: 32px;")
        details_layout.addWidget(desc_lbl)

        content_row.addLayout(details_layout, stretch=1)
        layout.addLayout(content_row)

        layout.addStretch()

        # Purchase Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        if is_owned:
            owned_lbl = QLabel("Đã sở hữu")
            owned_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            owned_lbl.setStyleSheet(f"color: {DesignTokens.CYAN}; font-weight: 700; font-size: 12px; padding: 6px;")
            btn_row.addWidget(owned_lbl)
        else:
            can_coin = coins >= char.price
            buy_btn = QPushButton(f"Mua {char.price:,} Xu")
            buy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            buy_btn.setFixedHeight(32)
            if can_coin:
                buy_btn.setToolTip("Nhấn để mua ngay bằng Pop Coin")
                buy_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {DesignTokens.GRADIENT_BLUE_GREEN};
                        color: #040812;
                        font-size: 12px;
                        font-weight: 700;
                        border-radius: 6px;
                        border: none;
                        padding: 0 10px;
                    }}
                    QPushButton:hover {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0077D6, stop:1 #00E699);
                    }}
                """)
            else:
                buy_btn.setToolTip(f"Chưa đủ Xu (còn thiếu {char.price - coins:,} Xu) - Bấm để xem")
                buy_btn.setStyleSheet("""
                    QPushButton {
                        background: rgba(255, 255, 255, 0.05);
                        color: #94A3B8;
                        font-size: 12px;
                        font-weight: 700;
                        border-radius: 6px;
                        border: 1px dashed rgba(255, 255, 255, 0.18);
                        padding: 0 10px;
                    }
                    QPushButton:hover {
                        background: rgba(255, 255, 255, 0.10);
                        color: #F1F5F9;
                        border-color: rgba(255, 255, 255, 0.35);
                    }
                """)
            buy_btn.clicked.connect(lambda: self.buyClicked.emit(self.char.id))
            btn_row.addWidget(buy_btn, stretch=1)

            # Exchange with Shards button
            can_shard = shards >= shard_cost
            shard_btn = QPushButton(f"Đổi {shard_cost} Mảnh")
            shard_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            shard_btn.setFixedHeight(32)
            if can_shard:
                shard_btn.setToolTip("Nhấn để đổi ngay bằng Mảnh")
                shard_btn.setStyleSheet("""
                    QPushButton {
                        background: rgba(168, 85, 247, 0.35);
                        color: #FFFFFF;
                        font-size: 12px;
                        font-weight: 700;
                        border-radius: 6px;
                        border: 1px solid #A855F7;
                        padding: 0 8px;
                    }
                    QPushButton:hover {
                        background: rgba(168, 85, 247, 0.55);
                        border-color: #C084FC;
                    }
                """)
            else:
                shard_btn.setToolTip(f"Chưa đủ Mảnh (còn thiếu {shard_cost - shards} Mảnh) - Bấm để xem")
                shard_btn.setStyleSheet("""
                    QPushButton {
                        background: rgba(168, 85, 247, 0.06);
                        color: #64748B;
                        font-size: 12px;
                        font-weight: 700;
                        border-radius: 6px;
                        border: 1px dashed rgba(168, 85, 247, 0.22);
                        padding: 0 8px;
                    }
                    QPushButton:hover {
                        background: rgba(168, 85, 247, 0.14);
                        color: #D8B4FE;
                        border-color: rgba(168, 85, 247, 0.4);
                    }
                """)
            shard_btn.clicked.connect(lambda: self.exchangeClicked.emit(self.char.id))
            btn_row.addWidget(shard_btn, stretch=1)

        layout.addLayout(btn_row)


class ShopTab(QWidget):
    """Displays characters for sale and handles purchase transactions."""

    itemPurchased = pyqtSignal()

    def __init__(self, service: CollectionService, parent=None):
        super().__init__(parent)
        self.service = service
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(12)

        # Header note
        info_banner = QLabel("Mẹo: Mở trứng tiết kiệm hơn mua trực tiếp. Nhận nhân vật trùng lặp sẽ tự động chuyển thành Mảnh để đổi skin mong muốn.")
        info_banner.setWordWrap(True)
        info_banner.setStyleSheet("""
            background: rgba(56, 189, 248, 0.08);
            border: 1px solid rgba(56, 189, 248, 0.25);
            color: #7DD3FC;
            font-size: 11px;
            padding: 8px 14px;
            border-radius: 8px;
        """)
        layout.addWidget(info_banner)

        # Scroll Area for Character Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        self.cards_container = QWidget()
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(12)

        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll)

    def refresh(self):
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item is not None:
                w = item.widget()
                if w is not None:
                    w.deleteLater()

        w = self.service.wallet()
        coins = int(w.get("coins", 0))
        shards = int(w.get("shards", 0))
        owned = self.service.owned()
        items = self.service.registry.shop_items()

        cols = 2
        for idx, char in enumerate(items):
            is_owned = char.id in owned
            card = CharacterShopCard(char, is_owned, coins, shards)
            card.buyClicked.connect(self._on_buy_clicked)
            card.exchangeClicked.connect(self._on_exchange_clicked)

            row = idx // cols
            col = idx % cols
            self.cards_layout.addWidget(card, row, col)

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
                "Chưa Đủ Pop Coin",
                f"Bạn cần thêm {needed:,} Xu để mua {char.name}!\n\n"
                f"• Hiện có: {coins:,} Xu\n"
                f"• Giá bán: {char.price:,} Xu\n\n"
                f"💡 Mẹo kiếm thêm Xu:\n"
                f"- Điểm danh hàng ngày (+50 Xu/ngày)\n"
                f"- Ra lệnh / nói chuyện với Pop bằng giọng nói (+5 Xu/lệnh, tối đa 100 Xu/ngày)\n"
                f"- Thưởng chuỗi điểm danh 7 ngày tặng thêm trứng"
            )
            return

        outcome = self.service.buy_character(char_id)
        if outcome.ok:
            QMessageBox.information(self, "Mua Thành Công", outcome.message)
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
                "Chưa Đủ Mảnh",
                f"Bạn cần thêm {needed:,} Mảnh để đổi {char.name}!\n\n"
                f"• Hiện có: {shards:,} Mảnh\n"
                f"• Cần: {shard_cost:,} Mảnh\n\n"
                f"💡 Mẹo nhận Mảnh:\n"
                f"- Khi mở trứng tại tab 'Mở Trứng', nếu quay trúng nhân vật đã sở hữu sẽ tự động quy đổi thành Mảnh."
            )
            return

        outcome = self.service.exchange_shards(char_id)
        if outcome.ok:
            QMessageBox.information(self, "Đổi Mảnh Thành Công", outcome.message)
            self.refresh()
            self.itemPurchased.emit()
        else:
            QMessageBox.information(self, "Đổi Mảnh", outcome.message)
