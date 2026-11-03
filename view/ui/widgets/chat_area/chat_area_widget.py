"""
POP Chat Area Widget - Central Chat Area assembling Header Bar, Message Scroll Area, Action Cards, Thinking State, and Input Bar.
"""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QVariantAnimation, QEasingCurve
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame
)

from view.ui.styles import DesignTokens
from view.ui.widgets.input_bar_widget import InputBarWidget
from model.pop_chat_model import ChatMessage, ConversationSession

from view.ui.widgets.chat_area.chat_header_bar import ChatHeaderBarWidget
from view.ui.widgets.chat_area.thinking_indicator import ThinkingIndicatorWidget
from view.ui.widgets.chat_area.message_bubble_widget import MessageBubbleWidget
from view.ui.widgets.chat_area.action_confirmation_card import ActionConfirmationCardWidget
from view.ui.widgets.chat_area.file_preview_card import FilePreviewCardWidget


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
    windowHideToMascot = pyqtSignal()
    windowClose = pyqtSignal()
    executeToolRequested = pyqtSignal(str, dict)
    retryRequested = pyqtSignal(str)

    def __init__(self, parent=None, user_name: str = "bạn"):
        super().__init__(parent)
        self.user_name = user_name
        self.is_thinking = False
        self._is_centered = True
        self._is_animating = False
        self._pending_text = ""
        self._last_sent_text = ""
        self.drop_anim = None
        self._setup_ui()

    def minimumSizeHint(self):
        return QSize(280, 200)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ----------------------------------------------------
        # 1. TOP HEADER BAR
        # ----------------------------------------------------
        self.header_bar = ChatHeaderBarWidget(self)
        self.header_bar.toggleRightPanel.connect(self.toggleRightPanel.emit)
        self.header_bar.openSettings.connect(self.openSettings.emit)
        self.header_bar.windowHideToMascot.connect(self.windowHideToMascot.emit)
        self.header_bar.windowMinimize.connect(self.windowMinimize.emit)
        self.header_bar.windowMaximize.connect(self.windowMaximize.emit)
        self.header_bar.windowClose.connect(self.windowClose.emit)

        # Backward compatibility references
        self.panel_btn = self.header_bar.panel_btn
        self.settings_btn = self.header_bar.settings_btn
        self.mascot_btn = self.header_bar.mascot_btn
        self.min_btn = self.header_bar.min_btn
        self.max_btn = self.header_bar.max_btn
        self.close_btn = self.header_bar.close_btn

        main_layout.addWidget(self.header_bar)

        # ----------------------------------------------------
        # 2. MESSAGES SCROLL AREA
        # ----------------------------------------------------
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.messages_container = QWidget()
        self.messages_container.setMinimumWidth(0)
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(16, 12, 16, 12)
        self.messages_layout.setSpacing(14)

        self.scroll_area.setWidget(self.messages_container)
        main_layout.addWidget(self.scroll_area, stretch=1)

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
        c_blue = f"rgba(0, 142, 255, {a:.2f})"
        c_green = f"rgba(0, 255, 170, {a:.2f})"
        c_muted = f"rgba(148, 163, 184, {a:.2f})"
        font_family = DesignTokens.FONT_FAMILY
        html = (
            f"<div style='text-align: center; white-space: nowrap; font-family: {font_family};'>"
            f"<span style='font-size: 26px; font-weight: 700; letter-spacing: -0.4px; color: {c_blue};'>Xin chào, </span>"
            f"<span style='font-size: 26px; font-weight: 700; letter-spacing: -0.4px; color: {c_green};'>{name}</span>"
            f"<span style='font-size: 23px; font-weight: 400; letter-spacing: -0.2px; color: {c_muted};'>! Tôi có thể giúp gì cho bạn hôm nay?</span>"
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

    def showEvent(self, a0):
        super().showEvent(a0)
        if self._is_centered and not self._is_animating:
            QTimer.singleShot(0, self._recalculate_spacers)

    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        if self._is_centered and not self._is_animating:
            self._recalculate_spacers()

    def _handle_input_send(self, text: str):
        if not text.strip():
            return
        self._last_sent_text = text
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
        self.drop_anim.setDuration(350)
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
        self.scroll_area.show()
        self.scroll_to_bottom()

    def _reset_to_centered_state(self):
        if self.drop_anim and self.drop_anim.state() == QVariantAnimation.State.Running:
            self.drop_anim.stop()
        self._is_animating = False
        self._is_centered = True
        self.scroll_area.hide()
        self.top_spacer.show()
        self._update_greeting_text(1.0)
        self.greeting_label.show()
        self.bottom_spacer.show()
        self._recalculate_spacers()

    def load_session(self, session: ConversationSession):
        """Render all messages from a conversation session."""
        self.is_thinking = False
        self.thinking_widget.hide()

        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            if item:
                w = item.widget()
                if w and w != self.thinking_widget:
                    w.deleteLater()

        for msg in session.messages:
            bw = MessageBubbleWidget(msg)
            bw.retryRequested.connect(self.retryRequested.emit)
            self.messages_layout.addWidget(bw)

        self.messages_layout.addWidget(self.thinking_widget)
        self.thinking_widget.hide()
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
        bw.retryRequested.connect(self.retryRequested.emit)
        idx = self.messages_layout.indexOf(self.thinking_widget)
        if idx >= 0:
            self.messages_layout.insertWidget(idx, bw)
        else:
            self.messages_layout.addWidget(bw)
        bw.animate_fade_in()
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
        self._do_scroll_to_bottom()
        QTimer.singleShot(30, self._do_scroll_to_bottom)
        QTimer.singleShot(100, self._do_scroll_to_bottom)
        QTimer.singleShot(250, self._do_scroll_to_bottom)

    def _do_scroll_to_bottom(self):
        sb = self.scroll_area.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())
