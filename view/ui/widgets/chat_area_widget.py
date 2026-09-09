"""
POP Chat Area Widget - Central Chat Area with Top Bar, Messages Scroll Area, Action Confirmation Cards, and Thinking State Loader.
"""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QVariantAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QApplication, QGraphicsOpacityEffect
)

from view.ui.styles import DesignTokens
from view.ui.icons import get_pop_logo_pixmap, create_vector_icon
from view.ui.widgets.input_bar_widget import InputBarWidget
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
            f"QFrame {{ background-color: {DesignTokens.SURFACE_2}; border: none; border-radius: 14px; }}"
        )
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Header Title
        title_lbl = QLabel(self.title)
        title_lbl.setStyleSheet(f"color: {DesignTokens.CYAN_ACCENT}; font-weight: 700; font-size: 14px;")

        # Summary text
        summary_lbl = QLabel(self.summary)
        summary_lbl.setWordWrap(True)
        summary_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MAIN}; font-size: 13px;")

        # Action Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        confirm_btn = QPushButton(" Xác nhận & Thực thi")
        confirm_btn.setIcon(create_vector_icon("check", "#00FFAA", 14))
        confirm_btn.setFixedHeight(32)
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.setStyleSheet(
            f"QPushButton {{ background-color: {DesignTokens.BG_BASE}; color: #00FFAA; font-weight: 700; border: 1px solid #00CCFF; border-radius: 8px; padding: 0 14px; }}"
            f"QPushButton:hover {{ background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(0, 255, 170, 0.1), stop:1 rgba(0, 204, 255, 0.1)); border-color: #00FFAA; }}"
        )
        confirm_btn.clicked.connect(lambda: self.confirmed.emit(self.tool_name, self.tool_args))

        cancel_btn = QPushButton(" Hủy bỏ")
        cancel_btn.setIcon(create_vector_icon("close", "#FF4B6E", 14))
        cancel_btn.setFixedHeight(32)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(
            f"QPushButton {{ background: {DesignTokens.SURFACE_3}; color: {DesignTokens.CORAL_ACCENT}; border: 1px solid {DesignTokens.CORAL_ACCENT}; border-radius: 8px; padding: 0 14px; font-weight: 600; }}"
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
            f"QFrame {{ background-color: {DesignTokens.SURFACE_1}; border: none; border-radius: 14px; }}"
        )
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        title = QLabel(f"Tìm thấy {len(self.files)} tệp phù hợp:")
        title.setStyleSheet(f"color: {DesignTokens.CYAN_ACCENT}; font-size: 13px; font-weight: 700;")
        layout.addWidget(title)

        for f in self.files:
            file_row = QHBoxLayout()
            file_row.setSpacing(8)

            name_lbl = QLabel(f"{f.get('name', 'Tệp')}")
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
    """Animated Thinking Loader matching ChatGPT style."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._step = 0
        self._setup_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_dots)
        self.timer.start(400)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(10)

        self.text_lbl = QLabel("thinking")
        self.text_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 13px; font-style: italic; font-weight: 500;")

        layout.addWidget(self.text_lbl)
        layout.addStretch()

    def _animate_dots(self):
        self._step += 1
        dots = "." * (self._step % 4)
        self.text_lbl.setText(f"thinking{dots}")


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
                f"QFrame {{ background-color: {DesignTokens.SURFACE_2}; border: none; border-radius: 16px; border-top-right-radius: 4px; }}"
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
                f"QFrame {{ background-color: {DesignTokens.SURFACE_1}; border: none; border-radius: 16px; border-top-left-radius: 4px; }}"
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
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background: rgba(0,255,255,0.12); border-radius: 4px; }")
                
                def _handle_action(a=act_id):
                    if a == "copy":
                        cb = QApplication.clipboard()
                        if cb:
                            cb.setText(self.msg.text)
                    self.actionClicked.emit(a, self.msg.id)
                
                btn.clicked.connect(_handle_action)
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

    def __init__(self, parent=None, user_name: str = "bạn"):
        super().__init__(parent)
        self.user_name = user_name
        self.is_thinking = False
        self._is_centered = True
        self._is_animating = False
        self._pending_text = ""
        self.drop_anim = None
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ----------------------------------------------------
        # 1. TOP HEADER BAR
        # ----------------------------------------------------
        self.header_bar = QFrame()
        self.header_bar.setFixedHeight(54)
        self.header_bar.setStyleSheet("QFrame { background-color: transparent; border: none; }")
        hb_layout = QHBoxLayout(self.header_bar)
        hb_layout.setContentsMargins(16, 8, 16, 8)
        hb_layout.setSpacing(12)

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

        self.close_btn = QPushButton()
        self.close_btn.setIcon(create_vector_icon("close", "#FF4B6E", 12))
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setStyleSheet("QPushButton { border: none; } QPushButton:hover { background: rgba(255,75,110,0.25); border-radius: 4px; }")
        self.close_btn.clicked.connect(lambda: self.windowClose.emit())

        win_controls.addWidget(self.min_btn)
        win_controls.addWidget(self.max_btn)
        win_controls.addWidget(self.close_btn)

        hb_layout.addStretch()
        hb_layout.addWidget(self.panel_btn)
        hb_layout.addWidget(self.settings_btn)
        hb_layout.addLayout(win_controls)

        main_layout.addWidget(self.header_bar)

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
        # 3. TOP SPACER (Pushes greeting + input bar to center)
        # ----------------------------------------------------
        self.top_spacer = QWidget()
        self.top_spacer.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        main_layout.addWidget(self.top_spacer)

        # ----------------------------------------------------
        # 4. GREETING LABEL (Single line, right above input bar, no logo)
        # ----------------------------------------------------
        self.greeting_label = QLabel()
        self.greeting_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.greeting_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.greeting_label.setStyleSheet("background: transparent; border: none; padding-bottom: 14px;")
        self._update_greeting_text(1.0)
        main_layout.addWidget(self.greeting_label)

        # ----------------------------------------------------
        # 5. INPUT BAR
        # ----------------------------------------------------
        self.input_bar = InputBarWidget()
        self.input_bar.sendMessage.connect(self._handle_input_send)
        self.input_bar.voiceToggle.connect(lambda: self.voiceToggled.emit())
        self.input_bar.switchModel.connect(lambda m: self.switchModel.emit(m))
        main_layout.addWidget(self.input_bar)

        # ----------------------------------------------------
        # 6. BOTTOM SPACER (Pushes input bar up in empty state)
        # ----------------------------------------------------
        self.bottom_spacer = QWidget()
        self.bottom_spacer.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        main_layout.addWidget(self.bottom_spacer)

        # Default state: Centered
        self._reset_to_centered_state()

    def _update_greeting_text(self, opacity: float = 1.0):
        name = self.user_name if self.user_name and self.user_name != "bạn" else "bạn"
        a = max(0.0, min(1.0, float(opacity)))
        c_cyan = f"rgba(150, 215, 233, {a:.2f})"
        c_green = f"rgba(0, 255, 170, {a:.2f})"
        c_muted = f"rgba(126, 155, 180, {a:.2f})"
        html = (
            f"<div style='text-align: center; white-space: nowrap;'>"
            f"<span style='font-size: 24px; font-weight: 700; color: {c_cyan};'>Xin chào, </span>"
            f"<span style='font-size: 24px; font-weight: 700; color: {c_green};'>{name}</span>"
            f"<span style='font-size: 22px; font-weight: 400; color: {c_muted};'>! Tôi có thể giúp gì cho bạn hôm nay?</span>"
            f"</div>"
        )
        self.greeting_label.setText(html)

    def set_user_name(self, name: str):
        self.user_name = name
        self._update_greeting_text(1.0)

    def _recalculate_spacers(self):
        if not self._is_centered or self._is_animating:
            return
        total_h = self.height()
        header_h = self.header_bar.height() if hasattr(self, 'header_bar') else 54
        avail_h = max(0, total_h - header_h)

        # Greeting height (~40px) + Input bar height (~80px)
        content_h = 120
        remaining = max(0, avail_h - content_h)

        # Roughly 40% top, 60% bottom to feel naturally balanced in the upper-middle
        top_h = int(remaining * 0.40)
        bottom_h = max(0, remaining - top_h)

        self.top_spacer.setFixedHeight(top_h)
        self.bottom_spacer.setFixedHeight(bottom_h)

    def showEvent(self, event):
        super().showEvent(event)
        if self._is_centered and not self._is_animating:
            QTimer.singleShot(0, self._recalculate_spacers)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._is_centered and not self._is_animating:
            self._recalculate_spacers()

    def _handle_input_send(self, text: str):
        if not text.strip():
            return
        if self._is_centered:
            self._start_drop_animation(text)
        else:
            self.sendMessage.emit(text)

    def _start_drop_animation(self, pending_text: str):
        if self._is_animating:
            return
        self._is_animating = True
        self._pending_text = pending_text

        initial_bottom_h = max(10, self.bottom_spacer.height())
        initial_top_h = self.top_spacer.height()

        self.drop_anim = QVariantAnimation(self)
        self.drop_anim.setDuration(400)
        self.drop_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.drop_anim.setStartValue(0.0)
        self.drop_anim.setEndValue(1.0)

        def _on_anim_update(val):
            # 1. Fade greeting out via RGBA alpha
            self._update_greeting_text(max(0.0, 1.0 - float(val)))
            # 2. Expand top_spacer while shrinking bottom_spacer
            cur_bot = int(initial_bottom_h * (1.0 - float(val)))
            cur_top = initial_top_h + (initial_bottom_h - cur_bot)
            self.top_spacer.setFixedHeight(cur_top)
            self.bottom_spacer.setFixedHeight(cur_bot)

        def _on_anim_finished():
            self._is_animating = False
            self._set_docked_state()
            if self._pending_text:
                t = self._pending_text
                self._pending_text = ""
                self.sendMessage.emit(t)

        self.drop_anim.valueChanged.connect(_on_anim_update)
        self.drop_anim.finished.connect(_on_anim_finished)
        self.drop_anim.start()

    def _set_docked_state(self):
        if self.drop_anim and self.drop_anim.state() == QVariantAnimation.State.Running:
            self.drop_anim.stop()
        self._is_animating = False
        self._is_centered = False
        self.top_spacer.hide()
        self.greeting_label.hide()
        self.bottom_spacer.hide()
        self.scroll.show()
        self.scroll_to_bottom()

    def _reset_to_centered_state(self):
        if self.drop_anim and self.drop_anim.state() == QVariantAnimation.State.Running:
            self.drop_anim.stop()
        self._is_animating = False
        self._is_centered = True
        self.scroll.hide()
        self.top_spacer.show()
        self._update_greeting_text(1.0)
        self.greeting_label.show()
        self.bottom_spacer.show()
        self._recalculate_spacers()

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

        if len(session.messages) == 0:
            self._reset_to_centered_state()
        else:
            self._set_docked_state()

    def append_message(self, msg: ChatMessage):
        """Add a single message to the active view."""
        if self._is_centered and not self._is_animating:
            self._set_docked_state()

        bw = MessageBubbleWidget(msg)
        idx = self.messages_layout.indexOf(self.thinking_widget)
        if idx >= 0:
            self.messages_layout.insertWidget(idx, bw)
        else:
            self.messages_layout.addWidget(bw)
        self.scroll_to_bottom()

    def append_confirmation_card(self, title: str, summary: str, tool_name: str, tool_args: dict):
        """Append Action Confirmation Card to chat view."""
        if self._is_centered and not self._is_animating:
            self._set_docked_state()

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
        if self._is_centered and not self._is_animating:
            self._set_docked_state()

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
            if self._is_centered and not self._is_animating:
                self._set_docked_state()
            self.thinking_widget.show()
        else:
            self.thinking_widget.hide()
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        sb = self.scroll.verticalScrollBar()
        sb.setValue(sb.maximum())
        QTimer.singleShot(0, lambda: sb.setValue(sb.maximum()))
