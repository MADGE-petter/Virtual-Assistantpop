"""
POP SidebarWidget - Single Unified Left Sidebar handling both Chat Mode and Settings Navigation.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QEvent
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QScrollArea, QFrame, QSizePolicy, QStackedWidget, QListWidget, QListWidgetItem,
    QGraphicsOpacityEffect, QGraphicsDropShadowEffect
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


class AvatarPopupMenu(QWidget):
    """Menu Popup người dùng màu đen tuyền không viền chữ trắng, tự đóng khi click ra ngoài."""

    profileClicked = pyqtSignal()
    settingsClicked = pyqtSignal()
    modelsClicked = pyqtSignal()
    logoutClicked = pyqtSignal()
    menuClosed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(260, 185)
        self._setup_ui()

    def closeEvent(self, event):
        self.menuClosed.emit()
        super().closeEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange and not self.isActiveWindow():
            self.close()
        super().changeEvent(event)

    def _setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(6, 6, 6, 6)

        container = QFrame()
        container.setStyleSheet(
            f"QFrame {{"
            f"  background-color: #000000;"
            f"  border: none;"
            f"  border-radius: 12px;"
            f"}}"
        )
        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)

        def _create_btn(text: str, handler):
            btn = QPushButton(text)
            btn.setFixedHeight(34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                f"QPushButton {{"
                f"  background: transparent;"
                f"  color: #FFFFFF;"
                f"  font-size: 13px;"
                f"  font-weight: 600;"
                f"  text-align: left;"
                f"  padding-left: 14px;"
                f"  border: none;"
                f"  border-radius: 8px;"
                f"}}"
                f"QPushButton:hover {{"
                f"  background: rgba(255, 255, 255, 0.12);"
                f"  color: #FFFFFF;"
                f"}}"
            )
            btn.clicked.connect(lambda: [self.close(), handler()])
            return btn

        btn_prof = _create_btn("Hồ sơ & Bộ nhớ", self.profileClicked.emit)
        btn_set = _create_btn("Cài đặt chung", self.settingsClicked.emit)
        btn_mod = _create_btn("Quản lý Models", self.modelsClicked.emit)

        btn_sep = QFrame()
        btn_sep.setFrameShape(QFrame.Shape.HLine)
        btn_sep.setStyleSheet("background-color: rgba(255, 255, 255, 0.12); max-height: 1px; margin: 2px 4px; border: none;")

        btn_out = _create_btn("Đăng xuất", self.logoutClicked.emit)
        btn_out.setStyleSheet(
            f"QPushButton {{"
            f"  background: transparent;"
            f"  color: #FFFFFF;"
            f"  font-size: 13px;"
            f"  font-weight: 600;"
            f"  text-align: left;"
            f"  padding-left: 14px;"
            f"  border: none;"
            f"  border-radius: 8px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: rgba(255, 75, 110, 0.25);"
            f"  color: #FF4B6E;"
            f"}}"
        )

        layout.addWidget(btn_prof)
        layout.addWidget(btn_set)
        layout.addWidget(btn_mod)
        layout.addWidget(btn_sep)
        layout.addWidget(btn_out)

        root_layout.addWidget(container)

    def show_animated(self, target_pos: QPoint):
        start_pos = QPoint(target_pos.x(), target_pos.y() + 8)
        self.setWindowOpacity(0.0)
        self.move(start_pos)
        self.show()
        self.raise_()

        self._anim_group = QParallelAnimationGroup(self)

        pos_anim = QPropertyAnimation(self, b"pos")
        pos_anim.setDuration(160)
        pos_anim.setStartValue(start_pos)
        pos_anim.setEndValue(target_pos)
        pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        op_anim = QPropertyAnimation(self, b"windowOpacity")
        op_anim.setDuration(160)
        op_anim.setStartValue(0.0)
        op_anim.setEndValue(1.0)
        op_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._anim_group.addAnimation(pos_anim)
        self._anim_group.addAnimation(op_anim)
        self._anim_group.start()


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
            def mouseReleaseEvent(self, event):
                if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
                    self.clicked.emit()
                super().mouseReleaseEvent(event)
                
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
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00FFAA, stop:1 #008EFF); "
            f"color: #03050B; font-weight: 800; font-size: 14px; border-radius: 17px; border: 1.5px solid rgba(0, 255, 170, 0.4);"
        )

        self.user_text_container = QWidget()
        utc_layout = QVBoxLayout(self.user_text_container)
        utc_layout.setContentsMargins(0, 0, 0, 0)
        utc_layout.setSpacing(2)

        self.user_name_lbl = QLabel(self.user_name)
        self.user_name_lbl.setStyleSheet(f"color: #FFFFFF; font-weight: 700; font-size: 13px;")

        self.user_sub_lbl = QLabel("Tùy chọn tài khoản ▲")
        self.user_sub_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 11px;")

        utc_layout.addWidget(self.user_name_lbl)
        utc_layout.addWidget(self.user_sub_lbl)

        profile_layout.addWidget(self.avatar_lbl)
        profile_layout.addWidget(self.user_text_container, stretch=1)

        main_layout.addWidget(self.profile_container)

        self._avatar_menu = None
        self._last_menu_closed_time = 0.0

    def _toggle_avatar_menu(self):
        """Bật / Tắt menu khi bấm vào avatar: nếu đang mở thì đóng, nếu đang đóng thì mở."""
        import time
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

        global_pt = self.profile_container.mapToGlobal(QPoint(0, 0))
        target_x = global_pt.x() + 8
        target_y = global_pt.y() - self._avatar_menu.height() - 6
        self._avatar_menu.show_animated(QPoint(target_x, target_y))

    def _on_avatar_menu_closed(self):
        import time
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
            self.user_text_container.hide()
        else:
            self.brand_text_container.show()
            self.new_chat_btn.setText(" ←  Quay lại Chat" if self.current_mode == 1 else " +  New Chat")
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
