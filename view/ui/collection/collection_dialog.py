"""
Collection Dialog - Standalone popup window for the Mascot Collection System.
Styled with POP AI Design System: Frameless, Starfield cosmic background,
pure Black & White aesthetic, rounded glassmorphism containers and glowing accents.
"""

from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QMouseEvent, QColor
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFrame, QMessageBox, QGraphicsDropShadowEffect, QWidget
)
from service.collection.character_registry import CharacterDef
from service.collection.collection_service import get_collection_service
from view.ui.collection.egg_tab import EggTab
from view.ui.collection.inventory_tab import InventoryTab
from view.ui.collection.shop_tab import ShopTab
from view.ui.styles import DesignTokens
from view.ui.icons import get_pop_logo_pixmap, create_vector_icon
from view.ui.widgets.starfield_widget import StarfieldWidget


class CollectionDialog(QDialog):
    """Main Collection popup dialog opened via Mascot right-click."""

    characterEquipped = pyqtSignal(object)  # Emits CharacterDef

    def __init__(self, user_key: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.service = get_collection_service(user_key)
        self._drag_pos = QPoint()

        self.setWindowTitle("Bộ Sưu Tập & Triệu Hồi Mascot")
        self.setFixedSize(980, 680)

        # Frameless Window with Translucent Background matching POP UI
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._init_ui()
        self.refresh_wallet()

        self.service.on_equip_changed(self._on_service_equipped)

    def _init_ui(self):
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(12, 12, 12, 12)

        # 1. Cosmic Starfield Background
        self.starfield = StarfieldWidget(self, star_count=32)
        self.starfield.setGeometry(0, 0, 980, 680)
        self.starfield.lower()

        # 2. Glassmorphic Central Obsidian Container (Bo góc 16px, Trắng + Đen)
        self.container_box = QFrame()
        self.container_box.setObjectName("container_box")
        self.container_box.setStyleSheet(f"""
            QFrame#container_box {{
                background-color: #000000;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 16px;
            }}
        """)

        # Subtle Glowing Cyan/White Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setColor(QColor(0, 255, 180, 40))
        shadow.setOffset(0, 6)
        self.container_box.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(self.container_box)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # ---------------- 3. Top Draggable Header Bar ----------------
        self.header_bar = QFrame()
        self.header_bar.setFixedHeight(46)
        self.header_bar.setStyleSheet("""
            QFrame {
                background: rgba(10, 14, 22, 0.95);
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.10);
            }
        """)
        hb_layout = QHBoxLayout(self.header_bar)
        hb_layout.setContentsMargins(16, 0, 16, 0)
        hb_layout.setSpacing(10)

        logo_lbl = QLabel()
        logo_lbl.setPixmap(get_pop_logo_pixmap(22))
        hb_layout.addWidget(logo_lbl)

        win_title = QLabel("POP AI — BỘ SƯU TẬP & TRIỆU HỒI MASCOT")
        win_title.setStyleSheet("""
            font-size: 13px;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: 1px;
            border: none;
            background: transparent;
        """)
        hb_layout.addWidget(win_title, stretch=1)

        close_btn = QPushButton()
        close_btn.setIcon(create_vector_icon("close", "#E2E8F0", 14))
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 7px;
            }
            QPushButton:hover {
                background: rgba(244, 63, 94, 0.35);
                border-color: #F43F5E;
            }
        """)
        close_btn.clicked.connect(self.close)
        hb_layout.addWidget(close_btn)

        container_layout.addWidget(self.header_bar)

        # ---------------- 4. Inner Content Area ----------------
        content_wrapper = QWidget()
        content_wrapper.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(content_wrapper)
        self._content_layout.setContentsMargins(16, 12, 16, 14)
        self._content_layout.setSpacing(12)

        # Navigation + Currency Bar (Bo góc 12px)
        self.top_bar = QFrame()
        self.top_bar.setObjectName("topBar")
        self.top_bar.setFixedHeight(50)
        self.top_bar.setStyleSheet("""
            QFrame#topBar {
                background: #090D15;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
            }
            QFrame#topBar QLabel {
                border: none;
                background: transparent;
            }
        """)
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(8, 6, 12, 6)
        top_layout.setSpacing(10)

        # Left: High-contrast Black & White Segmented Navigation Pill
        nav_pill = QFrame()
        nav_pill.setObjectName("navPill")
        nav_pill.setStyleSheet("""
            QFrame#navPill {
                background: #030509;
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 9px;
            }
        """)
        nav_layout = QHBoxLayout(nav_pill)
        nav_layout.setContentsMargins(4, 4, 4, 4)
        nav_layout.setSpacing(6)

        self.tab_buttons = []
        tabs_meta = [
            ("Triệu Hồi Gacha", 0),
            ("Kho Nhân Vật", 1),
            ("Cửa Hàng", 2),
        ]
        for label, idx in tabs_meta:
            btn = QPushButton(label)
            btn.setFixedHeight(30)
            btn.setMinimumWidth(128)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=idx: self._switch_tab(i))
            nav_layout.addWidget(btn)
            self.tab_buttons.append(btn)

        top_layout.addWidget(nav_pill)
        top_layout.addStretch()

        # Right: Crisp High-Contrast Currency Badges
        pill_base_style = """
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 8px;
            padding: 5px 12px;
            font-size: 12px;
            font-weight: 700;
        """

        self.coins_lbl = QLabel("Xu: 0")
        self.coins_lbl.setToolTip("Pop Xu — Dùng để mua Lõi Năng Lượng hoặc mở khóa nhân vật")
        self.coins_lbl.setStyleSheet(pill_base_style + "color: #FACC15;")
        top_layout.addWidget(self.coins_lbl)

        self.shards_lbl = QLabel("Mảnh: 0")
        self.shards_lbl.setToolTip("Mảnh Nhân Vật — Nhận khi quay trùng, dùng quy đổi nhân vật hiếm")
        self.shards_lbl.setStyleSheet(pill_base_style + "color: #C084FC;")
        top_layout.addWidget(self.shards_lbl)

        self.eggs_lbl = QLabel("Lõi: 0")
        self.eggs_lbl.setVisible(False)

        self._content_layout.addWidget(self.top_bar)

        # ---------------- 5. Central Stack Views ----------------
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")

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

        self._content_layout.addWidget(self.stack, stretch=1)
        container_layout.addWidget(content_wrapper, stretch=1)
        base_layout.addWidget(self.container_box)

        self._switch_tab(0)

    # ---------------- Window Dragging Support ----------------
    def mousePressEvent(self, a0: Optional[QMouseEvent]):
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            if a0.position().y() <= 48:
                self._drag_pos = a0.globalPosition().toPoint() - self.frameGeometry().topLeft()
                a0.accept()
                return
        super().mousePressEvent(a0)

    def mouseMoveEvent(self, a0: Optional[QMouseEvent]):
        if a0 and a0.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(a0.globalPosition().toPoint() - self._drag_pos)
            a0.accept()
            return
        super().mouseMoveEvent(a0)

    def mouseReleaseEvent(self, a0: Optional[QMouseEvent]):
        self._drag_pos = QPoint()
        super().mouseReleaseEvent(a0)

    def _on_gacha_fullscreen_changed(self, is_fullscreen: bool):
        self.top_bar.setVisible(not is_fullscreen)
        if hasattr(self, "header_bar"):
            self.header_bar.setVisible(not is_fullscreen)
        if is_fullscreen:
            self._content_layout.setContentsMargins(0, 0, 0, 0)
            self._content_layout.setSpacing(0)
        else:
            self._content_layout.setContentsMargins(16, 12, 16, 14)
            self._content_layout.setSpacing(12)

    def _switch_tab(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.tab_buttons):
            if i == index:
                # Active: Contrast Crisp White Button with Black Text
                btn.setStyleSheet("""
                    QPushButton {
                        background: #FFFFFF;
                        color: #000000;
                        font-weight: 800;
                        border-radius: 7px;
                        border: none;
                        font-size: 12px;
                        padding: 0 16px;
                    }
                """)
            else:
                # Inactive: Minimal Obsidian Dark with Silver Text
                btn.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        color: #94A3B8;
                        font-weight: 600;
                        border-radius: 7px;
                        border: none;
                        font-size: 12px;
                        padding: 0 16px;
                    }
                    QPushButton:hover {
                        background: rgba(255, 255, 255, 0.08);
                        color: #FFFFFF;
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
