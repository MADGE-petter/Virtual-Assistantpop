"""
POP SidebarWidget - Single Unified Left Sidebar handling both Chat Mode and Settings Navigation.
"""

import time
from PyQt6.QtCore import (
    Qt, pyqtSignal, QSize, QPoint, QEasingCurve, QVariantAnimation
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QStackedWidget, QListWidget, QListWidgetItem
)

from view.ui.styles import DesignTokens
from view.ui.icons import get_pop_logo_icon, create_vector_icon
from model.pop_chat_model import PopChatModel
from view.ui.widgets.sidebar.conversation_item import ConversationItemWidget
from view.ui.widgets.sidebar.avatar_popup_menu import AvatarPopupMenu


class SidebarWidget(QWidget):
    """Single Unified Left Sidebar Container Widget."""

    newChatRequested = pyqtSignal()
    backToChatRequested = pyqtSignal()
    conversationSelected = pyqtSignal(str)
    deleteConversationRequested = pyqtSignal(str)
    settingsClicked = pyqtSignal()
    modelsClicked = pyqtSignal()
    settingsTabSelected = pyqtSignal(int)
    voiceModeClicked = pyqtSignal()
    toggleCollapsed = pyqtSignal()
    memoryClicked = pyqtSignal()
    logoutRequested = pyqtSignal()

    def __init__(self, chat_model: PopChatModel, user_name: str, parent=None):
        super().__init__(parent)
        self.chat_model = chat_model
        self.user_name = user_name
        self.is_collapsed = False
        self.current_mode = 0  # 0: Chat Mode, 1: Settings Mode

        self.setMinimumWidth(260)
        self.setMaximumWidth(260)
        self.setObjectName("sidebar")
        self._setup_ui()
        self.reload_conversations()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 12, 10, 12)
        main_layout.setSpacing(10)

        # ----------------------------------------------------
        # 1. BRAND HEADER (POP Logo + AI Assistant)
        # ----------------------------------------------------
        brand_layout = QHBoxLayout()
        brand_layout.setContentsMargins(4, 0, 4, 0)
        brand_layout.setSpacing(8)

        self.logo_btn = QPushButton()
        self.logo_btn.setIcon(get_pop_logo_icon(34))
        self.logo_btn.setIconSize(QSize(34, 34))
        self.logo_btn.setFixedSize(34, 34)
        self.logo_btn.setToolTip("Thu gọn/Mở rộng sidebar")
        self.logo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logo_btn.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background: rgba(255,255,255,0.08); border-radius: 17px; }")
        self.logo_btn.clicked.connect(self._toggle_collapse)

        self.brand_text_container = QWidget()
        btc_layout = QVBoxLayout(self.brand_text_container)
        btc_layout.setContentsMargins(0, 0, 0, 0)
        btc_layout.setSpacing(0)

        self.title_lbl = QLabel("POP")
        self.title_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MAIN}; font-size: 18px; font-weight: 700; letter-spacing: 1px;")

        self.subtitle_lbl = QLabel("AI Assistant")
        self.subtitle_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 11px; font-weight: 500;")

        btc_layout.addWidget(self.title_lbl)
        btc_layout.addWidget(self.subtitle_lbl)

        brand_layout.addWidget(self.logo_btn)
        brand_layout.addWidget(self.brand_text_container, stretch=1)

        main_layout.addLayout(brand_layout)

        # ----------------------------------------------------
        # 2. TOP ACTION BUTTON (+ New Chat / ← Quay lại Chat)
        # ----------------------------------------------------
        self.new_chat_btn = QPushButton(" +  New Chat")
        self.new_chat_btn.setFixedHeight(36)
        self.new_chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_chat_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {DesignTokens.CYAN_ACCENT}; border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; border-radius: 10px; font-weight: 600; text-align: left; padding-left: 12px; font-size: 13px; }}"
            f"QPushButton:hover {{ background: rgba(255, 255, 255, 0.04); border-color: {DesignTokens.BORDER_GRADIENT_HOVER}; color: #FFFFFF; }}"
        )
        self.new_chat_btn.clicked.connect(self._on_top_btn_clicked)
        main_layout.addWidget(self.new_chat_btn)

        # ----------------------------------------------------
        # 3. CENTRAL BODY STACK (Chat Mode vs Settings Mode)
        # ----------------------------------------------------
        self.body_stack = QStackedWidget()
        self.body_stack.setStyleSheet("QStackedWidget { background: transparent; }")

        # Page 0: Conversation Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)

        self.scroll_area.setWidget(self.list_container)
        self.body_stack.addWidget(self.scroll_area)

        # Page 1: Settings Navigation List
        self.settings_nav_list = QListWidget()
        self.settings_nav_list.setStyleSheet(
            f"QListWidget {{ background: transparent; border: none; font-size: 13px; outline: none; }}"
            f"QListWidget::item {{ padding: 11px 14px; border-radius: 10px; margin-bottom: 4px; color: {DesignTokens.TEXT_MAIN}; border: 1px solid transparent; }}"
            f"QListWidget::item:hover {{ background: rgba(255, 255, 255, 0.03); border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; color: {DesignTokens.CYAN}; }}"
            f"QListWidget::item:selected {{ background: transparent; "
            f"color: {DesignTokens.CYAN_ACCENT}; font-weight: bold; border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; border-left: 3px solid {DesignTokens.CYAN_ACCENT}; }}"
        )

        nav_items = [
            ("settings", "Cài đặt chung"),
            ("bot", "Quản lý Models"),
            ("download", "Tải & Tìm kiếm Model"),
            ("folder", "Dữ liệu & Files"),
            ("rules", "Quy tắc Ngữ cảnh"),
            ("user", "Hồ sơ người dùng"),
            ("monitor", "Thông số máy")
        ]
        self.settings_nav_list.setIconSize(QSize(18, 18))
        for icon_key, item_text in nav_items:
            icon = create_vector_icon(icon_key, "gradient", 18)
            self.settings_nav_list.addItem(QListWidgetItem(icon, f"  {item_text}"))

        self.settings_nav_list.currentRowChanged.connect(self._on_settings_tab_clicked)
        self.body_stack.addWidget(self.settings_nav_list)

        main_layout.addWidget(self.body_stack, stretch=1)

        # Separator line
        self.sep_line = QFrame()
        self.sep_line.setFrameShape(QFrame.Shape.HLine)
        self.sep_line.setStyleSheet(f"background-color: rgba(255, 255, 255, 0.08); max-height: 1px;")
        main_layout.addWidget(self.sep_line)

        # ----------------------------------------------------
        # 4. USER PROFILE CARD (Clickable to toggle Menu)
        # ----------------------------------------------------
        class ClickableWidget(QWidget):
            clicked = pyqtSignal()
            def mouseReleaseEvent(self, a0):
                if a0 and a0.button() == Qt.MouseButton.LeftButton and self.rect().contains(a0.position().toPoint()):
                    self.clicked.emit()
                super().mouseReleaseEvent(a0)
                
        self.profile_container = ClickableWidget()
        self.profile_container.setCursor(Qt.CursorShape.PointingHandCursor)
        self.profile_container.clicked.connect(self._toggle_avatar_menu)
        
        profile_layout = QHBoxLayout(self.profile_container)
        profile_layout.setContentsMargins(6, 6, 6, 6)
        profile_layout.setSpacing(10)

        # Avatar circle
        first_char = self.user_name[0].upper() if self.user_name else "U"
        self.avatar_lbl = QLabel(first_char)
        self.avatar_lbl.setFixedSize(34, 34)
        self.avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_lbl.setStyleSheet(
            f"background: {DesignTokens.GRADIENT_BLUE_GREEN}; "
            f"color: #040812; font-weight: 700; font-size: 14px; border-radius: 17px; border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT};"
        )

        self.user_text_container = QWidget()
        utc_layout = QVBoxLayout(self.user_text_container)
        utc_layout.setContentsMargins(0, 0, 0, 0)
        utc_layout.setSpacing(2)
        utc_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.user_name_lbl = QLabel(self.user_name)
        self.user_name_lbl.setStyleSheet(f"color: #FFFFFF; font-weight: 700; font-size: 14px;")

        utc_layout.addWidget(self.user_name_lbl)

        profile_layout.addWidget(self.avatar_lbl)
        profile_layout.addWidget(self.user_text_container, stretch=1)

        main_layout.addWidget(self.profile_container)

        self._avatar_menu = None
        self._last_menu_closed_time = 0.0

    def _toggle_avatar_menu(self):
        """Bật / Tắt menu khi bấm vào avatar: nếu đang mở thì đóng, nếu đang đóng thì mở."""
        now = time.time()
        if self._avatar_menu and self._avatar_menu.isVisible():
            self._avatar_menu.close()
            return
        if (now - self._last_menu_closed_time) < 0.28:
            return

        if self._avatar_menu is None:
            self._avatar_menu = AvatarPopupMenu(self.window())
            self._avatar_menu.profileClicked.connect(lambda: self.settingsTabSelected.emit(5))
            self._avatar_menu.settingsClicked.connect(lambda: self.settingsTabSelected.emit(0))
            self._avatar_menu.modelsClicked.connect(lambda: self.settingsTabSelected.emit(1))
            self._avatar_menu.logoutClicked.connect(lambda: self.logoutRequested.emit())
            self._avatar_menu.menuClosed.connect(self._on_avatar_menu_closed)

        # Căn chỉnh menu thẳng hàng max sang mép trái của Avatar/Sidebar và hạ thấp vừa vặn trên vạch phân cách
        prof_pt = self.profile_container.mapToGlobal(QPoint(0, 0))
        sep_pt = self.sep_line.mapToGlobal(QPoint(0, 0))
        target_x = prof_pt.x()
        target_y = sep_pt.y() - self._avatar_menu.height() - 4
        self._avatar_menu.show_animated(QPoint(target_x, target_y))

    def _on_avatar_menu_closed(self):
        self._last_menu_closed_time = time.time()

    def set_mode(self, mode: int, selected_tab: int = 0):
        """Mode 0: Chat Mode (Conversation List), Mode 1: Settings Mode (Settings Tabs)."""
        self.current_mode = mode
        self.body_stack.setCurrentIndex(mode)
        
        if mode == 1:
            self.settings_nav_list.setCurrentRow(selected_tab)
            if self.is_collapsed:
                self.new_chat_btn.setText(" ←")
                self.new_chat_btn.setToolTip("Quay lại màn hình chính")
            else:
                self.new_chat_btn.setText(" ←  Quay lại Chat")
                self.new_chat_btn.setToolTip("Thoát cài đặt về giao diện trò chuyện")
            self.new_chat_btn.setStyleSheet(
                f"QPushButton {{ background-color: {DesignTokens.SURFACE_2}; color: {DesignTokens.TEXT_MAIN}; border: 1px solid {DesignTokens.BORDER}; border-radius: 10px; font-weight: 600; text-align: left; padding-left: 12px; font-size: 13px; }}"
                f"QPushButton:hover {{ background-color: {DesignTokens.SURFACE_3}; border-color: rgba(0, 229, 255, 0.4); color: #FFFFFF; }}"
            )
        else:
            if self.is_collapsed:
                self.new_chat_btn.setText(" +")
                self.new_chat_btn.setToolTip("Tạo cuộc trò chuyện mới")
            else:
                self.new_chat_btn.setText(" +  New Chat")
                self.new_chat_btn.setToolTip("Tạo cuộc trò chuyện mới")
            self.new_chat_btn.setStyleSheet(
                f"QPushButton {{ background-color: rgba(0, 230, 153, 0.08); color: {DesignTokens.CYAN_ACCENT}; border: 1px solid rgba(0, 230, 153, 0.28); border-radius: 10px; font-weight: 600; text-align: left; padding-left: 12px; font-size: 13px; }}"
                f"QPushButton:hover {{ background-color: rgba(0, 230, 153, 0.16); border-color: {DesignTokens.CYAN_ACCENT}; color: #FFFFFF; }}"
            )

    def _on_top_btn_clicked(self):
        if self.current_mode == 1:
            self.set_mode(0)
            self.backToChatRequested.emit()
        else:
            self.newChatRequested.emit()

    def _on_settings_clicked(self):
        self.set_mode(1, 0)
        self.settingsClicked.emit()

    def _on_models_clicked(self):
        self.set_mode(1, 1)
        self.modelsClicked.emit()

    def _on_settings_tab_clicked(self, row: int):
        if row >= 0:
            self.settingsTabSelected.emit(row)

    def _create_nav_button(self, text: str, icon_type: str, handler) -> QPushButton:
        btn = QPushButton(f"   {text}")
        btn.setFixedHeight(34)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setIcon(create_vector_icon(icon_type, "#96D7E9", 16))
        btn.setIconSize(QSize(16, 16))
        btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: {DesignTokens.TEXT_MAIN}; border: none; text-align: left; padding-left: 8px; font-size: 13px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {DesignTokens.SURFACE_1}; border-radius: 8px; }}"
        )
        if handler:
            btn.clicked.connect(handler)
        return btn

    def _toggle_collapse(self):
        self.is_collapsed = not self.is_collapsed
        start_w = self.width()
        target_w = 64 if self.is_collapsed else 260

        if hasattr(self, '_anim') and self._anim and self._anim.state() == QVariantAnimation.State.Running:
            self._anim.stop()

        if self.is_collapsed:
            self.brand_text_container.hide()
            self.user_text_container.hide()
            self.new_chat_btn.setText(" ←" if self.current_mode == 1 else " +")
            self.new_chat_btn.setToolTip("Quay lại Chat" if self.current_mode == 1 else "New Chat")
        else:
            self.new_chat_btn.setText(" ←  Quay lại Chat" if self.current_mode == 1 else " +  New Chat")
            self.new_chat_btn.setToolTip("Thoát cài đặt về giao diện trò chuyện" if self.current_mode == 1 else "Tạo cuộc trò chuyện mới")

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(220)
        self._anim.setStartValue(start_w)
        self._anim.setEndValue(target_w)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _on_step(val):
            w = int(val)
            self.setMinimumWidth(w)
            self.setMaximumWidth(w)

        def _on_finish():
            self.setMinimumWidth(target_w)
            self.setMaximumWidth(target_w)
            if not self.is_collapsed:
                self.brand_text_container.show()
                self.user_text_container.show()
            self.reload_conversations()
            self.toggleCollapsed.emit()

        self._anim.valueChanged.connect(_on_step)
        self._anim.finished.connect(_on_finish)
        self._anim.start()

    def reload_conversations(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item:
                w = item.widget()
                if w:
                    w.deleteLater()

        categorized = self.chat_model.get_categorized_sessions()
        for cat_name, sessions in categorized.items():
            if not sessions:
                continue

            if not self.is_collapsed:
                header = QLabel(cat_name.upper())
                header.setStyleSheet(
                    "color: #64748B; font-size: 11px; font-weight: 600; "
                    "letter-spacing: 0.5px; padding: 10px 8px 4px 8px; border: none; background: transparent;"
                )
                self.list_layout.addWidget(header)

            for s in sessions:
                is_active = (s.id == self.chat_model.active_session_id) or getattr(s, 'is_active', False)
                item_w = ConversationItemWidget(s, is_active, self.is_collapsed)
                item_w.clicked.connect(self._on_item_clicked)
                item_w.deleteRequested.connect(self.deleteConversationRequested.emit)
                self.list_layout.addWidget(item_w)

        self.list_layout.addStretch()

    def _on_item_clicked(self, session_id: str):
        self.set_mode(0)
        self.chat_model.set_active_session(session_id)
        self.reload_conversations()
        self.conversationSelected.emit(session_id)
