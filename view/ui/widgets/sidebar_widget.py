"""
POP SidebarWidget - Single Unified Left Sidebar handling both Chat Mode and Settings Navigation.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QScrollArea, QFrame, QSizePolicy, QStackedWidget, QListWidget, QListWidgetItem
)

from view.ui.styles import DesignTokens
from view.ui.icons import get_pop_logo_pixmap, get_pop_logo_icon, create_vector_icon
from model.pop_chat_model import PopChatModel, ConversationSession


class ConversationItemWidget(QFrame):
    """Single Conversation Item Widget in Left Sidebar."""

    clicked = pyqtSignal(str)
    deleteRequested = pyqtSignal(str)

    def __init__(self, session: ConversationSession, is_active: bool = False, is_collapsed: bool = False, parent=None):
        super().__init__(parent)
        self.session = session
        self.is_active = is_active
        self.is_collapsed = is_collapsed
        self.setFixedHeight(38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)

        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(create_vector_icon("search" if self.is_active else "dots", "#00FFAA" if self.is_active else "#557088", 16).pixmap(16, 16))
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_lbl = QLabel(self.session.title)
        self.title_lbl.setStyleSheet(
            f"color: {DesignTokens.TEXT_MAIN if self.is_active else DesignTokens.TEXT_SECONDARY}; "
            f"font-size: 13px; font-weight: {'600' if self.is_active else '400'};"
        )
        self.title_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.time_lbl = QLabel(self.session.timestamp)
        self.time_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 10px;")

        self.dots_btn = QPushButton()
        self.dots_btn.setIcon(create_vector_icon("dots", "#96D7E9", 12))
        self.dots_btn.setFixedSize(20, 20)
        self.dots_btn.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background: rgba(255,255,255,0.1); border-radius: 4px; }")

        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.title_lbl)
        layout.addWidget(self.time_lbl)
        layout.addWidget(self.dots_btn)

        self._update_collapsed_state(self.is_collapsed)
        self._update_style()

    def _update_collapsed_state(self, collapsed: bool):
        self.is_collapsed = collapsed
        if collapsed:
            self.title_lbl.hide()
            self.time_lbl.hide()
            self.dots_btn.hide()
            self.setToolTip(self.session.title)
        else:
            self.title_lbl.show()
            self.time_lbl.show()
            self.dots_btn.show()
            self.setToolTip("")

    def _update_style(self):
        if self.is_active:
            self.setStyleSheet(
                f"QFrame {{ background-color: {DesignTokens.SURFACE_2}; border: none; border-radius: 8px; }}"
            )
        else:
            self.setStyleSheet(
                f"QFrame {{ background-color: transparent; border: none; border-radius: 8px; }}"
                f"QFrame:hover {{ background-color: {DesignTokens.SURFACE_1}; }}"
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.session.id)
        super().mousePressEvent(event)


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

    def __init__(self, chat_model: PopChatModel, user_name: str, parent=None):
        super().__init__(parent)
        self.chat_model = chat_model
        self.user_name = user_name
        self.is_collapsed = False
        self.current_mode = 0  # 0: Chat Mode, 1: Settings Mode

        self.setMinimumWidth(280)
        self.setMaximumWidth(280)
        self.setObjectName("sidebar")
        self._setup_ui()
        self.reload_conversations()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 14, 10, 14)
        main_layout.setSpacing(12)

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
            f"QPushButton {{ background-color: {DesignTokens.BG_BASE}; color: #00FFAA; border: 1px solid #00CCFF; border-radius: 10px; font-weight: 600; text-align: left; padding-left: 12px; }}"
            f"QPushButton:hover {{ background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(0, 255, 170, 0.1), stop:1 rgba(0, 204, 255, 0.1)); border-color: #00FFAA; }}"
        )
        self.new_chat_btn.clicked.connect(self._on_top_btn_clicked)
        main_layout.addWidget(self.new_chat_btn)

        # ----------------------------------------------------
        # 3. CENTRAL BODY STACK (Chat Mode vs Settings Mode)
        # ----------------------------------------------------
        self.body_stack = QStackedWidget()
        self.body_stack.setStyleSheet("QStackedWidget { background: transparent; }")

        # Page 0: Conversation Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)

        self.scroll.setWidget(self.list_container)
        self.body_stack.addWidget(self.scroll)

        # Page 1: Settings Navigation List
        self.settings_nav_list = QListWidget()
        self.settings_nav_list.setStyleSheet(
            f"QListWidget {{ background: transparent; border: none; font-size: 13px; outline: none; }}"
            f"QListWidget::item {{ padding: 11px 14px; border-radius: 10px; margin-bottom: 4px; color: {DesignTokens.TEXT_MAIN}; }}"
            f"QListWidget::item:hover {{ background: rgba(0, 255, 170, 0.08); color: {DesignTokens.CYAN}; }}"
            f"QListWidget::item:selected {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 255, 170, 0.2), stop:1 rgba(0, 142, 255, 0.2)); "
            f"color: {DesignTokens.CYAN_ACCENT}; font-weight: bold; border-left: 3px solid {DesignTokens.CYAN_ACCENT}; }}"
        )

        nav_items = [
            "Cài đặt chung",
            "Quản lý Models",
            "Tải & Tìm kiếm Model",
            "Dữ liệu & Files",
            "Quy tắc Ngữ cảnh",
            "Hồ sơ người dùng",
            "Thông số máy"
        ]
        for item in nav_items:
            self.settings_nav_list.addItem(QListWidgetItem(item))

        self.settings_nav_list.currentRowChanged.connect(self._on_settings_tab_clicked)
        self.body_stack.addWidget(self.settings_nav_list)

        main_layout.addWidget(self.body_stack, stretch=1)

        # ----------------------------------------------------
        # 4. NAVIGATION / OPTIONS MENU (Settings & Models Buttons)
        # ----------------------------------------------------
        self.nav_container = QWidget()
        nav_layout = QVBoxLayout(self.nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(4)

        self.settings_btn = self._create_nav_button("Settings", "settings", self._on_settings_clicked)
        self.models_btn = self._create_nav_button("Models", "command", self._on_models_clicked)

        nav_layout.addWidget(self.settings_btn)
        nav_layout.addWidget(self.models_btn)

        main_layout.addWidget(self.nav_container)

        # Separator line
        self.sep_line = QFrame()
        self.sep_line.setFrameShape(QFrame.Shape.HLine)
        self.sep_line.setStyleSheet(f"background-color: {DesignTokens.BORDER}; max-height: 1px;")
        main_layout.addWidget(self.sep_line)

        # ----------------------------------------------------
        # 5. USER PROFILE CARD
        # ----------------------------------------------------
        class ClickableWidget(QWidget):
            clicked = pyqtSignal()
            def mousePressEvent(self, event):
                if event.button() == Qt.MouseButton.LeftButton:
                    self.clicked.emit()
                super().mousePressEvent(event)
                
        self.profile_container = ClickableWidget()
        self.profile_container.setCursor(Qt.CursorShape.PointingHandCursor)
        self.profile_container.clicked.connect(lambda: self.memoryClicked.emit())
        
        profile_layout = QHBoxLayout(self.profile_container)
        profile_layout.setContentsMargins(4, 2, 4, 2)
        profile_layout.setSpacing(8)

        # Avatar circle
        first_char = self.user_name[0].upper() if self.user_name else "T"
        self.avatar_lbl = QLabel(first_char)
        self.avatar_lbl.setFixedSize(32, 32)
        self.avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_lbl.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00FFAA, stop:1 #008EFF); "
            f"color: #03050B; font-weight: 700; font-size: 13px; border-radius: 16px;"
        )

        self.user_text_container = QWidget()
        utc_layout = QVBoxLayout(self.user_text_container)
        utc_layout.setContentsMargins(0, 0, 0, 0)
        utc_layout.setSpacing(0)

        self.user_name_lbl = QLabel(self.user_name)
        self.user_name_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MAIN}; font-weight: 600; font-size: 13px;")

        self.user_sub_lbl = QLabel("Tài khoản người dùng")
        self.user_sub_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 11px;")

        utc_layout.addWidget(self.user_name_lbl)
        utc_layout.addWidget(self.user_sub_lbl)

        profile_layout.addWidget(self.avatar_lbl)
        profile_layout.addWidget(self.user_text_container, stretch=1)

        main_layout.addWidget(self.profile_container)

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
                f"QPushButton {{ background-color: {DesignTokens.SURFACE_2}; color: {DesignTokens.CYAN_ACCENT}; border: 1px solid {DesignTokens.CYAN}; border-radius: 10px; font-weight: 600; text-align: left; padding-left: 12px; }}"
                f"QPushButton:hover {{ background-color: {DesignTokens.SURFACE_3}; border-color: #00FFAA; color: #FFFFFF; }}"
            )
        else:
            if self.is_collapsed:
                self.new_chat_btn.setText(" +")
                self.new_chat_btn.setToolTip("Tạo cuộc trò chuyện mới")
            else:
                self.new_chat_btn.setText(" +  New Chat")
                self.new_chat_btn.setToolTip("Tạo cuộc trò chuyện mới")
            self.new_chat_btn.setStyleSheet(
                f"QPushButton {{ background-color: {DesignTokens.BG_BASE}; color: #00FFAA; border: 1px solid #00CCFF; border-radius: 10px; font-weight: 600; text-align: left; padding-left: 12px; }}"
                f"QPushButton:hover {{ background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(0, 255, 170, 0.1), stop:1 rgba(0, 204, 255, 0.1)); border-color: #00FFAA; }}"
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
        w = 64 if self.is_collapsed else 280
        self.setMinimumWidth(w)
        self.setMaximumWidth(w)

        if self.is_collapsed:
            self.brand_text_container.hide()
            self.new_chat_btn.setText(" ←" if self.current_mode == 1 else " +")
            self.settings_btn.setText("")
            self.models_btn.setText("")
            self.user_text_container.hide()
        else:
            self.brand_text_container.show()
            self.new_chat_btn.setText(" ←  Quay lại Chat" if self.current_mode == 1 else " +  New Chat")
            self.settings_btn.setText("   Settings")
            self.models_btn.setText("   Models")
            self.user_text_container.show()
            self.settings_btn.setText("   Settings")
            self.models_btn.setText("   Models")
            self.user_text_container.show()

        self.reload_conversations()
        self.toggleCollapsed.emit()

    def reload_conversations(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        categorized = self.chat_model.get_categorized_sessions()
        for cat_name, sessions in categorized.items():
            if not sessions:
                continue

            if not self.is_collapsed:
                header = QLabel(cat_name.upper())
                header.setStyleSheet(
                    f"color: {DesignTokens.TEXT_MUTED}; font-size: 10px; font-weight: 700; "
                    f"letter-spacing: 1px; padding: 4px 2px 2px 2px;"
                )
                self.list_layout.addWidget(header)

            for s in sessions:
                is_active = (s.id == self.chat_model.active_session_id) or getattr(s, 'is_active', False)
                item_w = ConversationItemWidget(s, is_active, self.is_collapsed)
                item_w.clicked.connect(self._on_item_clicked)
                self.list_layout.addWidget(item_w)

        self.list_layout.addStretch()

    def _on_item_clicked(self, session_id: str):
        self.set_mode(0)
        self.chat_model.set_active_session(session_id)
        self.reload_conversations()
        self.conversationSelected.emit(session_id)
