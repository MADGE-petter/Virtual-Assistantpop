"""
Collection Dialog - Standalone popup window for the Mascot Collection System.
Styled with a Flat 2D design system and natural, muted matte colors.
"""

from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFrame, QMessageBox
)
from service.collection.character_registry import CharacterDef
from service.collection.collection_service import get_collection_service
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

        self.setWindowTitle("Bộ Sưu Tập & Triệu Hồi Mascot")
        self.setFixedSize(940, 640)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint
        )

        self.setStyleSheet(f"""
            CollectionDialog {{
                background-color: #181A20;
                color: #E5E7EB;
                font-family: {DesignTokens.FONT_FAMILY};
            }}
        """)

        self._init_ui()
        self.refresh_wallet()

        self.service.on_equip_changed(self._on_service_equipped)

    def _init_ui(self):
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(16, 14, 16, 14)
        self._root_layout.setSpacing(12)

        # ---------------- Flat 2D Top Bar: Navigation (Left) + Wallet & Check-in (Right) ----------------
        self.top_bar = QFrame()
        top_bar = self.top_bar
        top_bar.setObjectName("unifiedTopBar")
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet("""
            QFrame#unifiedTopBar {
                background: #22252E;
                border: 1px solid #2E323E;
                border-radius: 10px;
            }
            QFrame#unifiedTopBar QLabel {
                border: none;
                background: transparent;
            }
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(8, 6, 10, 6)
        top_layout.setSpacing(8)

        # Left: Flat 2D Segmented Navigation Container
        nav_pill = QFrame()
        nav_pill.setObjectName("navPill")
        nav_pill.setStyleSheet("""
            QFrame#navPill {
                background: #181A20;
                border: 1px solid #2A2E39;
                border-radius: 8px;
            }
        """)
        nav_layout = QHBoxLayout(nav_pill)
        nav_layout.setContentsMargins(3, 3, 3, 3)
        nav_layout.setSpacing(4)

        self.tab_buttons = []
        tabs_meta = [
            ("Triệu Hồi Gacha", 0),
            ("Kho Nhân Vật", 1),
            ("Cửa Hàng", 2),
        ]
        for label, idx in tabs_meta:
            btn = QPushButton(label)
            btn.setFixedHeight(30)
            btn.setMinimumWidth(124)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=idx: self._switch_tab(i))
            nav_layout.addWidget(btn)
            self.tab_buttons.append(btn)

        top_layout.addWidget(nav_pill)
        top_layout.addStretch()

        # Right: Flat 2D Currency Badges with natural muted tones
        pill_base_style = """
            background: #181A20;
            border: 1px solid #2E323E;
            border-radius: 6px;
            padding: 5px 11px;
            font-size: 12px;
            font-weight: 700;
        """

        self.coins_lbl = QLabel("Xu: 0")
        self.coins_lbl.setToolTip("Pop Xu — Dùng để mua Lõi Năng Lượng hoặc mở khóa nhân vật")
        self.coins_lbl.setStyleSheet(pill_base_style + "color: #D4A359;")
        top_layout.addWidget(self.coins_lbl)

        self.shards_lbl = QLabel("Mảnh: 0")
        self.shards_lbl.setToolTip("Mảnh Nhân Vật — Nhận khi quay trùng, dùng quy đổi nhân vật hiếm")
        self.shards_lbl.setStyleSheet(pill_base_style + "color: #A78BFA;")
        top_layout.addWidget(self.shards_lbl)

        self.eggs_lbl = QLabel("Lõi: 0")
        self.eggs_lbl.setVisible(False)

        self._root_layout.addWidget(top_bar)

        # ---------------- Central Stack Views ----------------
        self.stack = QStackedWidget()

        self.egg_tab = EggTab(self.service)
        self.daily_btn = self.egg_tab.daily_btn
        self.egg_tab.eggOpened.connect(self._on_egg_opened)
        self.egg_tab.buyEggRequested.connect(self.refresh_wallet)
        self.egg_tab.equipRequested.connect(self._on_equip_changed)
        self.egg_tab.fullscreenModeChanged.connect(self._on_gacha_fullscreen_changed)
        self.stack.addWidget(self.egg_tab)

        self.inventory_tab = InventoryTab(self.service)
        self.inventory_tab.equipChanged.connect(self._on_equip_changed)
        self.stack.addWidget(self.inventory_tab)

        self.shop_tab = ShopTab(self.service)
        self.shop_tab.itemPurchased.connect(self._on_item_purchased)
        self.shop_tab.equipRequested.connect(self._on_equip_changed)
        self.stack.addWidget(self.shop_tab)

        self._root_layout.addWidget(self.stack, stretch=1)

        self._switch_tab(0)

    def _on_gacha_fullscreen_changed(self, is_fullscreen: bool):
        self.top_bar.setVisible(not is_fullscreen)
        if is_fullscreen:
            self._root_layout.setContentsMargins(0, 0, 0, 0)
            self._root_layout.setSpacing(0)
        else:
            self._root_layout.setContentsMargins(16, 14, 16, 14)
            self._root_layout.setSpacing(12)

    def _switch_tab(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.tab_buttons):
            if i == index:
                btn.setStyleSheet("""
                    QPushButton {
                        background: #3D6B8E;
                        color: #F3F4F6;
                        font-weight: 700;
                        border-radius: 6px;
                        border: none;
                        font-size: 12px;
                        padding: 0 14px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        color: #9CA3AF;
                        font-weight: 600;
                        border-radius: 6px;
                        border: none;
                        font-size: 12px;
                        padding: 0 14px;
                    }
                    QPushButton:hover {
                        background: #22252E;
                        color: #E5E7EB;
                    }
                """)

    def refresh_wallet(self):
        w = self.service.wallet()
        coins = int(w.get("coins", 0))
        shards = int(w.get("shards", 0))
        eggs = int(w.get("eggs", 0))

        self.coins_lbl.setText(f"Xu: {coins:,}")
        self.shards_lbl.setText(f"Mảnh: {shards:,}")
        self.eggs_lbl.setText(f"Lõi: {eggs:,}")

        self.egg_tab.refresh()
        self.shop_tab.refresh()

    def _on_daily_claim_clicked(self):
        msg = self.service.claim_daily()
        if msg:
            self.refresh_wallet()
            self.shop_tab.refresh()
            QMessageBox.information(self, "Điểm Danh Hằng Ngày", msg)

    def _on_egg_opened(self):
        self.refresh_wallet()
        self.shop_tab.refresh()
        self.inventory_tab.refresh()

    def _on_item_purchased(self):
        self.refresh_wallet()
        self.shop_tab.refresh()
        self.inventory_tab.refresh()

    def _on_equip_changed(self, char_id: str):
        self.refresh_wallet()
        self.shop_tab.refresh()
        self.inventory_tab.refresh()
        char = self.service.registry.get(char_id)
        if char:
            self.characterEquipped.emit(char)

    def _on_service_equipped(self, char: CharacterDef):
        self.refresh_wallet()
        self.characterEquipped.emit(char)
