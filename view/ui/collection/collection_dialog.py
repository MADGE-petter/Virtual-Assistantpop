"""
Collection Dialog - Standalone popup window for the Mascot collection system.
Styled to match POP AI View with specular glass panels, gradient accents, and no emoji icons.
"""

from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFrame, QMessageBox
)
from service.collection.character_registry import CharacterDef
from service.collection.collection_service import CollectionService, get_collection_service
from view.ui.collection.egg_tab import EggTab
from view.ui.collection.inventory_tab import InventoryTab
from view.ui.collection.shop_tab import ShopTab
from view.ui.styles import DesignTokens


class CollectionDialog(QDialog):
    """Main Collection popup dialog opened via Mascot right-click."""

    characterEquipped = pyqtSignal(object)  # Emits CharacterDef

    def __init__(self, user_key: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.service = get_collection_service(user_key)

        self.setWindowTitle("Bộ Sưu Tập Mascot")
        self.setFixedSize(820, 600)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint
        )

        self.setStyleSheet(f"""
            CollectionDialog {{
                background-color: {DesignTokens.BG_BASE};
                color: {DesignTokens.TEXT_MAIN};
                font-family: {DesignTokens.FONT_FAMILY};
            }}
        """)

        self._init_ui()
        self.refresh_wallet()

        # Listen to service equip events
        self.service.on_equip_changed(self._on_service_equipped)

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 16, 18, 18)
        root_layout.setSpacing(12)

        # ---------------- Header Bar: Title & Wallet ----------------
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_frame.setStyleSheet(f"""
            QFrame#headerFrame {{
                background: {DesignTokens.SURFACE_2};
                border: 1px solid;
                border-color: {DesignTokens.BORDER_GRADIENT};
                border-radius: 12px;
                padding: 8px 14px;
            }}
            QFrame#headerFrame QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 4, 10, 4)
        header_layout.setSpacing(12)

        # Title
        title_lbl = QLabel("BỘ SƯU TẬP MASCOT")
        title_lbl.setStyleSheet(f"""
            font-size: 15px;
            font-weight: 800;
            color: {DesignTokens.CYAN};
            letter-spacing: 0.8px;
        """)
        header_layout.addWidget(title_lbl)

        header_layout.addStretch()

        # Wallet: Pop Coins
        self.coins_lbl = QLabel("Xu: 0")
        self.coins_lbl.setToolTip("Xu - Dùng để mua trứng hoặc mua trực tiếp nhân vật")
        self.coins_lbl.setStyleSheet(f"""
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            padding: 5px 12px;
            font-size: 12px;
            font-weight: 700;
            color: #FCD34D;
        """)
        header_layout.addWidget(self.coins_lbl)

        # Wallet: Shards
        self.shards_lbl = QLabel("Mảnh: 0")
        self.shards_lbl.setToolTip("Mảnh Nhân Vật - Nhận được khi mở trùng, dùng đổi nhân vật hiếm")
        self.shards_lbl.setStyleSheet(f"""
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            padding: 5px 12px;
            font-size: 12px;
            font-weight: 700;
            color: #C084FC;
        """)
        header_layout.addWidget(self.shards_lbl)

        # Daily Claim button
        self.daily_btn = QPushButton("Điểm Danh")
        self.daily_btn.setFixedHeight(30)
        self.daily_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.daily_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 255, 170, 0.12);
                border: 1px solid rgba(0, 255, 170, 0.6);
                color: {DesignTokens.CYAN};
                font-size: 11px;
                font-weight: 700;
                border-radius: 8px;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                background: rgba(0, 255, 170, 0.24);
                border-color: {DesignTokens.CYAN};
            }}
            QPushButton:disabled {{
                background: rgba(255, 255, 255, 0.03);
                border-color: rgba(255, 255, 255, 0.08);
                color: #64748B;
            }}
        """)
        self.daily_btn.clicked.connect(self._on_daily_claim_clicked)
        header_layout.addWidget(self.daily_btn)

        root_layout.addWidget(header_frame)

        # ---------------- Custom Navigation TabBar ----------------
        tab_frame = QFrame()
        tab_frame.setObjectName("tabFrame")
        tab_frame.setStyleSheet(f"""
            QFrame#tabFrame {{
                background: rgba(15, 23, 42, 0.60);
                border: 1px solid;
                border-color: {DesignTokens.BORDER_GRADIENT};
                border-radius: 10px;
                padding: 3px;
            }}
        """)
        tab_layout = QHBoxLayout(tab_frame)
        tab_layout.setContentsMargins(4, 4, 4, 4)
        tab_layout.setSpacing(6)

        self.tab_buttons = []
        tabs_meta = [
            ("Lõi Nguyên Tử", 0),
            ("Cửa Hàng", 1),
            ("Kho Đồ", 2),
        ]
        for label, idx in tabs_meta:
            btn = QPushButton(label)
            btn.setFixedHeight(34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=idx: self._switch_tab(i))
            tab_layout.addWidget(btn, stretch=1)
            self.tab_buttons.append(btn)

        root_layout.addWidget(tab_frame)

        # ---------------- Central Stack Views ----------------
        self.stack = QStackedWidget()

        self.egg_tab = EggTab(self.service)
        self.egg_tab.eggOpened.connect(self._on_egg_opened)
        self.egg_tab.buyEggRequested.connect(self.refresh_wallet)
        self.stack.addWidget(self.egg_tab)

        self.shop_tab = ShopTab(self.service)
        self.shop_tab.itemPurchased.connect(self._on_item_purchased)
        self.stack.addWidget(self.shop_tab)

        self.inventory_tab = InventoryTab(self.service)
        self.inventory_tab.equipChanged.connect(self._on_equip_changed)
        self.stack.addWidget(self.inventory_tab)

        root_layout.addWidget(self.stack, stretch=1)

        self._switch_tab(0)

    def _switch_tab(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.tab_buttons):
            if i == index:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {DesignTokens.GRADIENT_BLUE_GREEN};
                        color: #040812;
                        font-weight: 700;
                        border-radius: 8px;
                        border: none;
                        font-size: 13px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {DesignTokens.TEXT_SECONDARY};
                        font-weight: 600;
                        border-radius: 8px;
                        border: none;
                        font-size: 13px;
                    }}
                    QPushButton:hover {{
                        background: rgba(255, 255, 255, 0.05);
                        color: #FFFFFF;
                    }}
                """)

    def refresh_wallet(self):
        w = self.service.wallet()
        coins = int(w.get("coins", 0))
        shards = int(w.get("shards", 0))

        self.coins_lbl.setText(f"Xu: {coins:,}")
        self.shards_lbl.setText(f"Mảnh: {shards:,}")

        # Daily status
        from datetime import date
        today_iso = date.today().isoformat()
        last_daily = w.get("last_daily")
        streak = int(w.get("streak", 0))
        if last_daily == today_iso:
            self.daily_btn.setText(f"Đã Điểm Danh ({streak} ngày)")
            self.daily_btn.setEnabled(False)
        else:
            self.daily_btn.setText("Điểm Danh (+50 Xu)")
            self.daily_btn.setEnabled(True)

        self.egg_tab.refresh()

    def _on_daily_claim_clicked(self):
        msg = self.service.claim_daily()
        if msg:
            self.refresh_wallet()
            QMessageBox.information(self, "Điểm Danh Hằng Ngày", msg)

    def _on_egg_opened(self):
        self.refresh_wallet()
        self.shop_tab.refresh()
        self.inventory_tab.refresh()

    def _on_item_purchased(self):
        self.refresh_wallet()
        self.inventory_tab.refresh()

    def _on_equip_changed(self, char_id: str):
        char = self.service.registry.get(char_id)
        if char:
            self.characterEquipped.emit(char)

    def _on_service_equipped(self, char: CharacterDef):
        self.characterEquipped.emit(char)
