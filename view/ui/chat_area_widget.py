"""
POP Chat Area Widget - Central Chat Area with Top Bar, Messages Scroll Area, Action Confirmation Cards, and Thinking State Loader.
"""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QScrollArea, QFrame, QSizePolicy, QApplication
)

from view.ui.styles import DesignTokens
from view.ui.icons import get_pop_logo_pixmap, create_vector_icon
from view.ui.input_bar_widget import InputBarWidget
from model.pop_chat_model import ChatMessage, ConversationSession


class ActionConfirmationCardWidget(QFrame):
    """Human-in-the-Loop Confirmation Card Widget displaying action summary & execution approval buttons."""

    confirmed = pyqtSignal(str, dict)
    cancelled = pyqtSignal()

    def __init__(self, title: str, summary: str, tool_name: str, tool_args: dict, parent=None):
        super().__init__(parent)
        self.tool_name = tool_name
        self.tool_args = tool_args
        self.title = title
        self.summary = summary

        self.setStyleSheet(
            f"QFrame {{ background-color: {DesignTokens.SURFACE_2}; border: 1px solid {DesignTokens.CYAN}; border-radius: 14px; }}"
        )
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Header Title
        title_lbl = QLabel(f"⚠️ {self.title}")
        title_lbl.setStyleSheet(f"color: {DesignTokens.CYAN_ACCENT}; font-weight: 700; font-size: 14px;")

        # Summary text
        summary_lbl = QLabel(self.summary)
        summary_lbl.setWordWrap(True)
        summary_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MAIN}; font-size: 13px;")

        # Action Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        confirm_btn = QPushButton("✓ Xác nhận & Thực thi")
        confirm_btn.setHeight = 34
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.setStyleSheet(
            f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #008EFF, stop:1 #00FFAA); color: #03050B; font-weight: 700; border: none; border-radius: 8px; padding: 6px 14px; }}"
            f"QPushButton:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00A6FF, stop:1 #33FFBC); }}"
        )
        confirm_btn.clicked.connect(lambda: self.confirmed.emit(self.tool_name, self.tool_args))

        cancel_btn = QPushButton("✕ Hủy bỏ")
        cancel_btn.setHeight = 34
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(
            f"QPushButton {{ background: {DesignTokens.SURFACE_3}; color: {DesignTokens.CORAL_ACCENT}; border: 1px solid {DesignTokens.CORAL_ACCENT}; border-radius: 8px; padding: 6px 14px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: rgba(255, 75, 110, 0.2); }}"
        )
        cancel_btn.clicked.connect(lambda: self.cancelled.emit())

        btn_box.addWidget(confirm_btn)
        btn_box.addWidget(cancel_btn)
        btn_box.addStretch()

        layout.addWidget(title_lbl)
        layout.addWidget(summary_lbl)
        layout.addLayout(btn_box)


class FilePreviewCardWidget(QFrame):
    """File Preview Card displaying search results with action buttons."""

    openFileRequested = pyqtSignal(str)

    def __init__(self, files: list, parent=None):
        super().__init__(parent)
        self.files = files
        self.setStyleSheet(
            f"QFrame {{ background-color: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; border-radius: 14px; }}"
        )
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        title = QLabel(f"📁 Tìm thấy {len(self.files)} tệp phù hợp:")
        title.setStyleSheet(f"color: {DesignTokens.CYAN_ACCENT}; font-size: 13px; font-weight: 700;")
        layout.addWidget(title)

        for f in self.files:
            file_row = QHBoxLayout()
            file_row.setSpacing(8)

            name_lbl = QLabel(f"📄 {f.get('name', 'Tệp')}")
            name_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MAIN}; font-weight: 600; font-size: 13px;")

            size_lbl = QLabel(f.get('size', ''))
            size_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 11px;")

            open_btn = QPushButton("Mở tệp")
            open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            open_btn.setStyleSheet(f"QPushButton {{ background: {DesignTokens.SURFACE_3}; color: {DesignTokens.CYAN}; border: none; border-radius: 6px; padding: 4px 8px; font-size: 11px; }}")
            open_btn.clicked.connect(lambda _, p=f.get('path'): self.openFileRequested.emit(p))

            file_row.addWidget(name_lbl, stretch=1)
            file_row.addWidget(size_lbl)
            file_row.addWidget(open_btn)

            row_w = QWidget()
            row_w.setLayout(file_row)
            layout.addWidget(row_w)


class ThinkingIndicatorWidget(QWidget):
    """Animated Thinking Loader matching po spec annotation #10 ('POP is thinking...')."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dot_count = 1
        self._setup_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_dots)
        self.timer.start(450)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(10)

        self.logo_lbl = QLabel()
        self.logo_lbl.setPixmap(get_pop_logo_pixmap(24))

        self.text_lbl = QLabel("POP đang suy nghĩ...")
        self.text_lbl.setStyleSheet(f"color: {DesignTokens.CYAN_ACCENT}; font-size: 13px; font-weight: 500;")

        layout.addWidget(self.logo_lbl)
        layout.addWidget(self.text_lbl)
        layout.addStretch()

    def _animate_dots(self):
        self._dot_count = (self._dot_count % 3) + 1
        dots = "." * self._dot_count
        self.text_lbl.setText(f"POP đang suy nghĩ{dots}")


class MessageBubbleWidget(QWidget):
    """Single Message Bubble Widget (User or AI) matching po #8 & #9."""

    actionClicked = pyqtSignal(str, str)

    def __init__(self, msg: ChatMessage, parent=None):
        super().__init__(parent)
        self.msg = msg
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 6, 12, 6)

        is_user = (self.msg.sender == "user")

        if is_user:
            main_layout.addStretch()

            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background-color: {DesignTokens.SURFACE_2}; border: 1px solid rgba(0, 255, 255, 0.2); border-radius: 16px; border-top-right-radius: 4px; }}"
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 10, 14, 10)
            card_layout.setSpacing(4)

            time_lbl = QLabel(self.msg.timestamp)
            time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            time_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 10px;")

            text_lbl = QLabel(self.msg.text)
            text_lbl.setWordWrap(True)
            text_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MAIN}; font-size: 14px; line-height: 1.4;")

            card_layout.addWidget(time_lbl)
            card_layout.addWidget(text_lbl)

            avatar_lbl = QLabel()
            avatar_lbl.setPixmap(create_vector_icon("user", "#96D7E9", 32).pixmap(32, 32))
            avatar_lbl.setFixedSize(32, 32)

            main_layout.addWidget(card)
            main_layout.addWidget(avatar_lbl, alignment=Qt.AlignmentFlag.AlignTop)

        else:
            avatar_lbl = QLabel()
            avatar_lbl.setPixmap(get_pop_logo_pixmap(32))
            avatar_lbl.setFixedSize(32, 32)

            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background-color: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; border-radius: 16px; border-top-left-radius: 4px; }}"
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 12, 16, 12)
            card_layout.setSpacing(8)

            header_layout = QHBoxLayout()
            header_layout.setSpacing(8)

            name_lbl = QLabel("POP")
            name_lbl.setStyleSheet(f"color: {DesignTokens.CYAN_ACCENT}; font-size: 13px; font-weight: 700;")

            time_lbl = QLabel(self.msg.timestamp)
            time_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 11px;")

            header_layout.addWidget(name_lbl)
            header_layout.addWidget(time_lbl)
            header_layout.addStretch()

            text_lbl = QLabel(self.msg.text)
            text_lbl.setWordWrap(True)
            text_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MAIN}; font-size: 14px; line-height: 1.5;")

            toolbar_layout = QHBoxLayout()
            toolbar_layout.setSpacing(6)

            actions = [
                ("copy", "Sao chép"),
                ("like", "Hữu ích"),
                ("dislike", "Chưa tốt"),
                ("retry", "Tạo lại câu trả lời")
            ]
            for act_id, tooltip in actions:
                btn = QPushButton()
                btn.setIcon(create_vector_icon(act_id, "#557088", 16))
                btn.setFixedSize(26, 26)
                btn.setToolTip(tooltip)
                btn.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background: rgba(255,255,255,0.08); border-radius: 4px; }")
                btn.clicked.connect(lambda _, a=act_id: self.actionClicked.emit(a, self.msg.id))
                toolbar_layout.addWidget(btn)

            toolbar_layout.addStretch()

            card_layout.addLayout(header_layout)
            card_layout.addWidget(text_lbl)
            card_layout.addLayout(toolbar_layout)

            main_layout.addWidget(avatar_lbl, alignment=Qt.AlignmentFlag.AlignTop)
            main_layout.addWidget(card, stretch=1)


class ChatAreaWidget(QWidget):
    """Central Chat Area Widget containing Header Bar, Message Scroll Area, Action Cards, and Input Bar."""

    sendMessage = pyqtSignal(str)
    voiceToggled = pyqtSignal()
    stopGeneration = pyqtSignal()
    switchModel = pyqtSignal(str)
    openSettings = pyqtSignal()
    toggleRightPanel = pyqtSignal()
    windowMinimize = pyqtSignal()
    windowMaximize = pyqtSignal()
    windowClose = pyqtSignal()
    executeToolRequested = pyqtSignal(str, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_thinking = False
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ----------------------------------------------------
        # 1. TOP HEADER BAR
        # ----------------------------------------------------
        header_bar = QFrame()
        header_bar.setFixedHeight(54)
        header_bar.setStyleSheet(f"QFrame {{ background-color: rgba(8, 15, 22, 0.6); border-bottom: 1px solid {DesignTokens.BORDER}; }}")
        hb_layout = QHBoxLayout(header_bar)
        hb_layout.setContentsMargins(16, 8, 16, 8)
        hb_layout.setSpacing(12)

        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "LFM2.5 2.6B (Local)",
            "LFM2.5 7B (Local)",
            "GPT-4o Mini (Cloud)",
            "Claude 3.5 Sonnet (Cloud)"
        ])
        self.model_combo.setFixedWidth(190)
        self.model_combo.currentTextChanged.connect(lambda m: self.switchModel.emit(m))

        self.date_pill = QLabel("18 Tháng 8, 2026")
        self.date_pill.setStyleSheet(f"background-color: {DesignTokens.SURFACE_2}; color: {DesignTokens.TEXT_MUTED}; border-radius: 12px; padding: 4px 12px; font-size: 11px; font-weight: 500;")

        self.status_badge = QLabel("🟢 READY")
        self.status_badge.setStyleSheet(f"background-color: rgba(0, 255, 170, 0.1); color: {DesignTokens.CYAN_ACCENT}; border: 1px solid rgba(0, 255, 170, 0.3); border-radius: 12px; padding: 4px 10px; font-size: 11px; font-weight: 600;")

        self.voice_btn = QPushButton()
        self.voice_btn.setIcon(create_vector_icon("waveform", "#00FFAA", 18))
        self.voice_btn.setFixedSize(32, 32)
        self.voice_btn.setToolTip("Bật chế độ giọng nói")
        self.voice_btn.setStyleSheet("QPushButton { border: none; background: rgba(0,255,255,0.08); border-radius: 8px; } QPushButton:hover { background: rgba(0,255,255,0.2); }")
        self.voice_btn.clicked.connect(lambda: self.voiceToggled.emit())

        self.panel_btn = QPushButton()
        self.panel_btn.setIcon(create_vector_icon("panel_toggle", "#96D7E9", 18))
        self.panel_btn.setFixedSize(32, 32)
        self.panel_btn.setToolTip("Bật/tắt bảng giám sát hệ thống")
        self.panel_btn.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background: rgba(255,255,255,0.08); border-radius: 8px; }")
        self.panel_btn.clicked.connect(lambda: self.toggleRightPanel.emit())

        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(create_vector_icon("settings", "#96D7E9", 18))
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.setToolTip("Cài đặt")
        self.settings_btn.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background: rgba(255,255,255,0.08); border-radius: 8px; }")
        self.settings_btn.clicked.connect(lambda: self.openSettings.emit())

        win_controls = QHBoxLayout()
        win_controls.setSpacing(4)

        self.min_btn = QPushButton("─")
        self.min_btn.setFixedSize(28, 28)
        self.min_btn.setStyleSheet("QPushButton { border: none; color: #96D7E9; font-weight: bold; } QPushButton:hover { background: rgba(255,255,255,0.1); border-radius: 4px; }")
        self.min_btn.clicked.connect(lambda: self.windowMinimize.emit())

        self.max_btn = QPushButton("□")
        self.max_btn.setFixedSize(28, 28)
        self.max_btn.setStyleSheet("QPushButton { border: none; color: #96D7E9; font-weight: bold; } QPushButton:hover { background: rgba(255,255,255,0.1); border-radius: 4px; }")
        self.max_btn.clicked.connect(lambda: self.windowMaximize.emit())

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setStyleSheet("QPushButton { border: none; color: #FF4B6E; font-weight: bold; } QPushButton:hover { background: rgba(255,75,110,0.25); border-radius: 4px; }")
        self.close_btn.clicked.connect(lambda: self.windowClose.emit())

        win_controls.addWidget(self.min_btn)
        win_controls.addWidget(self.max_btn)
        win_controls.addWidget(self.close_btn)

        hb_layout.addWidget(self.model_combo)
        hb_layout.addStretch()
        hb_layout.addWidget(self.date_pill)
        hb_layout.addStretch()
        hb_layout.addWidget(self.status_badge)
        hb_layout.addWidget(self.voice_btn)
        hb_layout.addWidget(self.panel_btn)
        hb_layout.addWidget(self.settings_btn)
        hb_layout.addLayout(win_controls)

        main_layout.addWidget(header_bar)

        # ----------------------------------------------------
        # 2. MESSAGES SCROLL AREA
        # ----------------------------------------------------
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(20, 16, 20, 16)
        self.messages_layout.setSpacing(16)

        self.scroll.setWidget(self.messages_container)
        main_layout.addWidget(self.scroll, stretch=1)

        self.thinking_widget = ThinkingIndicatorWidget()
        self.thinking_widget.hide()
        self.messages_layout.addWidget(self.thinking_widget)

        # ----------------------------------------------------
        # 3. INPUT BAR
        # ----------------------------------------------------
        self.input_bar = InputBarWidget()
        self.input_bar.sendMessage.connect(lambda text: self.sendMessage.emit(text))
        self.input_bar.voiceToggle.connect(lambda: self.voiceToggled.emit())

        main_layout.addWidget(self.input_bar)

    def load_session(self, session: ConversationSession):
        """Render all messages from a conversation session."""
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            if item.widget() and item.widget() != self.thinking_widget:
                item.widget().deleteLater()

        for msg in session.messages:
            bw = MessageBubbleWidget(msg)
            self.messages_layout.addWidget(bw)

        self.messages_layout.addWidget(self.thinking_widget)
        self.messages_layout.addStretch()
        self.scroll_to_bottom()

    def append_message(self, msg: ChatMessage):
        """Add a single message to the active view."""
        bw = MessageBubbleWidget(msg)
        idx = self.messages_layout.indexOf(self.thinking_widget)
        if idx >= 0:
            self.messages_layout.insertWidget(idx, bw)
        else:
            self.messages_layout.addWidget(bw)
        self.scroll_to_bottom()

    def append_confirmation_card(self, title: str, summary: str, tool_name: str, tool_args: dict):
        """Append Action Confirmation Card to chat view."""
        card = ActionConfirmationCardWidget(title, summary, tool_name, tool_args)
        card.confirmed.connect(lambda t_name, t_args: self.executeToolRequested.emit(t_name, t_args))
        idx = self.messages_layout.indexOf(self.thinking_widget)
        if idx >= 0:
            self.messages_layout.insertWidget(idx, card)
        else:
            self.messages_layout.addWidget(card)
        self.scroll_to_bottom()

    def append_file_preview_card(self, files: list):
        """Append File Preview Card to chat view."""
        card = FilePreviewCardWidget(files)
        idx = self.messages_layout.indexOf(self.thinking_widget)
        if idx >= 0:
            self.messages_layout.insertWidget(idx, card)
        else:
            self.messages_layout.addWidget(card)
        self.scroll_to_bottom()

    def set_thinking(self, thinking: bool):
        self.is_thinking = thinking
        if thinking:
            self.thinking_widget.show()
        else:
            self.thinking_widget.hide()
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        QApplication.processEvents()
        sb = self.scroll.verticalScrollBar()
        sb.setValue(sb.maximum())
