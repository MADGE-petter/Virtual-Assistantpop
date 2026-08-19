"""
POP Sidebar Widget - Collapsible Left Sidebar matching po specifications with clean layout form handling.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QScrollArea, QFrame, QSizePolicy
)

from view.ui.styles import DesignTokens
from view.ui.icons import get_pop_logo_pixmap, create_vector_icon
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

        # Chat Icon / Bullet Indicator
        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(create_vector_icon("search" if self.is_active else "dots", "#00FFAA" if self.is_active else "#557088", 16).pixmap(16, 16))
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title Label
        self.title_lbl = QLabel(self.session.title)
        self.title_lbl.setStyleSheet(
            f"color: {DesignTokens.TEXT_MAIN if self.is_active else DesignTokens.TEXT_SECONDARY}; "
            f"font-size: 13px; font-weight: {'600' if self.is_active else '400'};"
        )
        self.title_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Timestamp Label
        self.time_lbl = QLabel(self.session.timestamp)
        self.time_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 10px;")

        # Options Button (3 dots)
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
                f"QFrame {{ background-color: rgba(0, 255, 255, 0.08); border: 1px solid rgba(0, 255, 255, 0.4); border-radius: 8px; }}"
            )
        else:
            self.setStyleSheet(
                f"QFrame {{ background-color: transparent; border: 1px solid transparent; border-radius: 8px; }}"
                f"QFrame:hover {{ background-color: {DesignTokens.SURFACE_2}; border-color: rgba(30, 38, 52, 0.8); }}"
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.session.id)
        super().mousePressEvent(event)


class SidebarWidget(QWidget):
    """Left Sidebar Container Widget with Smooth Form Collapse Handling."""

    newChatRequested = pyqtSignal()
    conversationSelected = pyqtSignal(str)
    deleteConversationRequested = pyqtSignal(str)
    searchChanged = pyqtSignal(str)
    settingsClicked = pyqtSignal()
    modelsClicked = pyqtSignal()
    voiceModeClicked = pyqtSignal()
    toggleCollapsed = pyqtSignal()

    def __init__(self, chat_model: PopChatModel, parent=None):
        super().__init__(parent)
        self.chat_model = chat_model
        self.is_collapsed = False

        self.setMinimumWidth(280)
        self.setMaximumWidth(280)
        self.setObjectName("sidebar")
        self._setup_ui()

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

        self.logo_lbl = QLabel()
        self.logo_lbl.setPixmap(get_pop_logo_pixmap(34))
        self.logo_lbl.setFixedSize(34, 34)

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

        self.collapse_btn = QPushButton()
        self.collapse_btn.setIcon(create_vector_icon("sidebar_toggle", "#557088", 16))
        self.collapse_btn.setFixedSize(28, 28)
        self.collapse_btn.setToolTip("Thu gọn sidebar")
        self.collapse_btn.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background: rgba(255,255,255,0.08); border-radius: 6px; }")
        self.collapse_btn.clicked.connect(self._toggle_collapse)

        brand_layout.addWidget(self.logo_lbl)
        brand_layout.addWidget(self.brand_text_container, stretch=1)
        brand_layout.addWidget(self.collapse_btn)

        main_layout.addLayout(brand_layout)

        # ----------------------------------------------------
        # 2. NEW CHAT BUTTON (po #2)
        # ----------------------------------------------------
        self.new_chat_btn = QPushButton(" +  New Chat")
        self.new_chat_btn.setFixedHeight(36)
        self.new_chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_chat_btn.setStyleSheet(
            f"QPushButton {{ background-color: {DesignTokens.SURFACE_2}; color: {DesignTokens.TEXT_MAIN}; border: 1px solid rgba(0, 255, 255, 0.25); border-radius: 10px; font-weight: 600; text-align: left; padding-left: 12px; }}"
            f"QPushButton:hover {{ background-color: {DesignTokens.SURFACE_3}; border-color: {DesignTokens.CYAN}; color: #FFFFFF; }}"
        )
        self.new_chat_btn.clicked.connect(lambda: self.newChatRequested.emit())
        main_layout.addWidget(self.new_chat_btn)

        # ----------------------------------------------------
        # 3. SEARCH CONVERSATIONS FIELD (po #3)
        # ----------------------------------------------------
        self.search_container = QFrame()
        self.search_container.setFixedHeight(36)
        self.search_container.setStyleSheet(
            f"QFrame {{ background-color: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; border-radius: 10px; }}"
            f"QFrame:focus-within {{ border-color: {DesignTokens.CYAN}; }}"
        )
        sc_layout = QHBoxLayout(self.search_container)
        sc_layout.setContentsMargins(8, 2, 8, 2)
        sc_layout.setSpacing(6)

        search_icon = QLabel()
        search_icon.setPixmap(create_vector_icon("search", "#557088", 14).pixmap(14, 14))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tìm kiếm cuộc trò chuyện")
        self.search_input.setStyleSheet("QLineEdit { border: none; background: transparent; font-size: 12px; }")
        self.search_input.textChanged.connect(lambda t: self.searchChanged.emit(t))

        self.shortcut_badge = QLabel("⌘ K")
        self.shortcut_badge.setStyleSheet(f"background-color: {DesignTokens.SURFACE_3}; color: {DesignTokens.TEXT_MUTED}; border-radius: 4px; padding: 2px 4px; font-size: 10px; font-weight: 600;")

        sc_layout.addWidget(search_icon)
        sc_layout.addWidget(self.search_input, stretch=1)
        sc_layout.addWidget(self.shortcut_badge)

        main_layout.addWidget(self.search_container)

        # ----------------------------------------------------
        # 4. CATEGORIZED CONVERSATIONS SCROLL AREA (po #4)
        # ----------------------------------------------------
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)

        self.scroll.setWidget(self.list_container)
        main_layout.addWidget(self.scroll, stretch=1)

        # ----------------------------------------------------
        # 5. NAVIGATION / OPTIONS MENU (po #5)
        # ----------------------------------------------------
        self.nav_container = QWidget()
        nav_layout = QVBoxLayout(self.nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(4)

        self.settings_btn = self._create_nav_button("Settings", "settings", self.settingsClicked)
        self.models_btn = self._create_nav_button("Models", "search", self.modelsClicked)
        self.voice_mode_btn = self._create_nav_button("Voice Mode", "waveform", self.voiceModeClicked)

        nav_layout.addWidget(self.settings_btn)
        nav_layout.addWidget(self.models_btn)
        nav_layout.addWidget(self.voice_mode_btn)

        main_layout.addWidget(self.nav_container)

        # Separator line
        self.sep_line = QFrame()
        self.sep_line.setFrameShape(QFrame.Shape.HLine)
        self.sep_line.setStyleSheet(f"background-color: {DesignTokens.BORDER}; max-height: 1px;")
        main_layout.addWidget(self.sep_line)

        # ----------------------------------------------------
        # 6. USER PROFILE CARD (po #6)
        # ----------------------------------------------------
        self.profile_container = QWidget()
        profile_layout = QHBoxLayout(self.profile_container)
        profile_layout.setContentsMargins(4, 2, 4, 2)
        profile_layout.setSpacing(8)

        # Avatar circle "T"
        self.avatar_lbl = QLabel("T")
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

        self.user_name_lbl = QLabel("Tuấn")
        self.user_name_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MAIN}; font-weight: 600; font-size: 13px;")

        self.user_email_lbl = QLabel("tuanh.dev@gmail.com")
        self.user_email_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 11px;")

        utc_layout.addWidget(self.user_name_lbl)
        utc_layout.addWidget(self.user_email_lbl)

        profile_layout.addWidget(self.avatar_lbl)
        profile_layout.addWidget(self.user_text_container, stretch=1)

        main_layout.addWidget(self.profile_container)

        # Initial render of conversation items
        self.reload_conversations()

    def _create_nav_button(self, text: str, icon_type: str, signal) -> QPushButton:
        btn = QPushButton(f"   {text}")
        btn.setFixedHeight(34)
        btn.setIcon(create_vector_icon(icon_type, "#96D7E9", 16))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {DesignTokens.TEXT_SECONDARY}; border: none; border-radius: 8px; text-align: left; padding-left: 10px; font-size: 13px; font-weight: 500; }}"
            f"QPushButton:hover {{ background: {DesignTokens.SURFACE_2}; color: {DesignTokens.TEXT_MAIN}; }}"
        )
        btn.clicked.connect(lambda: signal.emit())
        return btn

    def reload_conversations(self, filter_text: str = ""):
        """Render session list grouped by Today, Yesterday, 7 Days Ago."""
        while self.list_layout.count():
            child = self.list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        sessions = self.chat_model.sessions
        if filter_text:
            sessions = [s for s in sessions if filter_text.lower() in s.title.lower()]

        categories = ["Hôm nay", "Hôm qua", "7 ngày trước"]
        for cat in categories:
            cat_sessions = [s for s in sessions if s.category == cat]
            if not cat_sessions:
                continue

            if not self.is_collapsed:
                header_lbl = QLabel(cat)
                header_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 10px; font-weight: 700; text-transform: uppercase; margin-top: 4px;")
                self.list_layout.addWidget(header_lbl)

            for session in cat_sessions:
                is_active = (session.id == self.chat_model.active_session_id)
                item_widget = ConversationItemWidget(session, is_active=is_active, is_collapsed=self.is_collapsed)
                item_widget.clicked.connect(self._on_item_clicked)
                item_widget.deleteRequested.connect(self._on_item_deleted)
                self.list_layout.addWidget(item_widget)

        self.list_layout.addStretch()

    def _on_item_clicked(self, session_id: str):
        self.chat_model.active_session_id = session_id
        self.reload_conversations()
        self.conversationSelected.emit(session_id)

    def _on_item_deleted(self, session_id: str):
        self.chat_model.delete_session(session_id)
        self.reload_conversations()
        self.deleteConversationRequested.emit(session_id)

    def _toggle_collapse(self):
        self.is_collapsed = not self.is_collapsed
        if self.is_collapsed:
            self.setMinimumWidth(64)
            self.setMaximumWidth(64)

            self.brand_text_container.hide()
            self.search_container.hide()
            self.user_text_container.hide()

            self.new_chat_btn.setText("+")
            self.new_chat_btn.setToolTip("Cuộc trò chuyện mới")
            self.new_chat_btn.setStyleSheet(
                f"QPushButton {{ background-color: {DesignTokens.SURFACE_2}; color: {DesignTokens.CYAN}; border: 1px solid rgba(0, 255, 255, 0.25); border-radius: 10px; font-size: 18px; font-weight: 700; text-align: center; padding: 0px; }}"
                f"QPushButton:hover {{ background-color: {DesignTokens.SURFACE_3}; border-color: {DesignTokens.CYAN}; }}"
            )

            self.settings_btn.setText("")
            self.settings_btn.setToolTip("Settings")

            self.models_btn.setText("")
            self.models_btn.setToolTip("Models")

            self.voice_mode_btn.setText("")
            self.voice_mode_btn.setToolTip("Voice Mode")

        else:
            self.setMinimumWidth(280)
            self.setMaximumWidth(280)

            self.brand_text_container.show()
            self.search_container.show()
            self.user_text_container.show()

            self.new_chat_btn.setText(" +  New Chat")
            self.new_chat_btn.setToolTip("")
            self.new_chat_btn.setStyleSheet(
                f"QPushButton {{ background-color: {DesignTokens.SURFACE_2}; color: {DesignTokens.TEXT_MAIN}; border: 1px solid rgba(0, 255, 255, 0.25); border-radius: 10px; font-weight: 600; text-align: left; padding-left: 12px; }}"
                f"QPushButton:hover {{ background-color: {DesignTokens.SURFACE_3}; border-color: {DesignTokens.CYAN}; color: #FFFFFF; }}"
            )

            self.settings_btn.setText("   Settings")
            self.settings_btn.setToolTip("")

            self.models_btn.setText("   Models")
            self.models_btn.setToolTip("")

            self.voice_mode_btn.setText("   Voice Mode")
            self.voice_mode_btn.setToolTip("")

        self.reload_conversations()
        self.toggleCollapsed.emit()
