"""
Message Bubble Widget - Single user or AI message bubble with markdown/file attachments and actions.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QEasingCurve, QPropertyAnimation
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QApplication, QGraphicsOpacityEffect, QTextEdit
)

from view.ui.styles import DesignTokens
from view.ui.icons import get_pop_logo_pixmap, create_vector_icon
from model.pop_chat_model import ChatMessage


class MessageBubbleWidget(QWidget):
    """Single Message Bubble Widget (User or AI)."""

    actionClicked = pyqtSignal(str, str)
    retryRequested = pyqtSignal(str)

    def __init__(self, msg: ChatMessage, parent=None):
        super().__init__(parent)
        self.msg = msg
        self.card = None
        self._fade_anim = None
        self._setup_ui()

    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        if hasattr(self, 'card') and self.card:
            available_w = self.width() - 36
            if available_w > 80:
                is_user = (self.msg.sender == "user")
                cap = 600 if is_user else 740
                max_w = max(160, min(cap, int(available_w * 0.88)))
                self.card.setMaximumWidth(max_w)

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 4, 16, 4)
        main_layout.setSpacing(12)

        is_user = (self.msg.sender == "user")

        if is_user:
            main_layout.addStretch(1)

            card = QFrame()
            self.card = card
            card.setObjectName("userCard")
            card.setMaximumWidth(600)
            card.setMinimumWidth(80)
            card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            card.setStyleSheet(
                f"#userCard {{ background-color: rgba(12, 19, 34, 0.94); border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; border-radius: 16px; border-top-right-radius: 4px; }}"
                f"#userCard QLabel {{ border: none; background: transparent; }}"
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 10, 14, 10)
            card_layout.setSpacing(6)

            time_lbl = QLabel(self.msg.timestamp)
            time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            time_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 10px;")
            card_layout.addWidget(time_lbl)

            raw_text = self.msg.text
            if raw_text.startswith("📎 ["):
                self._render_user_attachment_card(card_layout, raw_text)
            else:
                text_lbl = QLabel(raw_text)
                text_lbl.setWordWrap(True)
                text_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MAIN}; font-size: 14px; line-height: 1.45;")
                card_layout.addWidget(text_lbl)

            main_layout.addWidget(card)

        else:
            avatar_lbl = QLabel()
            avatar_lbl.setPixmap(get_pop_logo_pixmap(28))
            avatar_lbl.setFixedSize(32, 32)
            avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            avatar_lbl.setStyleSheet(
                f"background: transparent; border-radius: 16px; border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT};"
            )

            card = QFrame()
            self.card = card
            card.setObjectName("botCard")
            card.setMaximumWidth(740)
            card.setMinimumWidth(100)
            card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

            is_warning = self.msg.text.startswith("⚠️")
            is_model_missing = "Model++" in self.msg.text or "Mô hình AI" in self.msg.text
            if is_warning:
                card.setStyleSheet(
                    "QFrame#botCard { background-color: rgba(35, 20, 10, 0.92); border: 1px solid rgba(245, 158, 11, 0.45); border-radius: 16px; border-top-left-radius: 4px; }"
                    "QFrame#botCard QLabel { border: none; background: transparent; }"
                )
            elif is_model_missing:
                card.setStyleSheet(
                    "QFrame#botCard { background-color: rgba(14, 25, 42, 0.92); border: 1px solid rgba(56, 189, 248, 0.40); border-radius: 16px; border-top-left-radius: 4px; }"
                    "QFrame#botCard QLabel { border: none; background: transparent; }"
                )
            else:
                card.setStyleSheet(
                    f"#botCard {{ background-color: rgba(12, 19, 34, 0.88); border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; border-radius: 16px; border-top-left-radius: 4px; }}"
                    f"#botCard QLabel {{ border: none; background: transparent; }}"
                )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 12, 16, 12)
            card_layout.setSpacing(8)

            header_layout = QHBoxLayout()
            header_layout.setSpacing(8)

            name_lbl = QLabel("POP" if not is_warning else "POP • Cảnh báo")
            name_color = DesignTokens.CORAL_ACCENT if is_warning else DesignTokens.CYAN_ACCENT
            name_lbl.setStyleSheet(f"color: {name_color}; font-size: 13px; font-weight: 700;")

            time_lbl = QLabel(self.msg.timestamp)
            time_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 11px;")

            header_layout.addWidget(name_lbl)
            header_layout.addWidget(time_lbl)
            header_layout.addStretch()

            text_lbl = QLabel(self.msg.text)
            text_lbl.setWordWrap(True)
            text_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MAIN}; font-size: 14px; line-height: 1.5;")
            card_layout.addLayout(header_layout)
            card_layout.addWidget(text_lbl)

            if is_model_missing:
                actions_row = QHBoxLayout()
                actions_row.setSpacing(10)

                hub_btn = QPushButton(" Mở kho mô hình (Model++)")
                hub_btn.setIcon(create_vector_icon("download", "#00FFAA", 14))
                hub_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                hub_btn.setStyleSheet(
                    "QPushButton { background: rgba(0, 255, 170, 0.12); color: #00FFAA; "
                    "border: 1px solid rgba(0, 255, 170, 0.35); border-radius: 8px; "
                    "padding: 8px 14px; font-size: 12px; font-weight: 600; } "
                    "QPushButton:hover { background: rgba(0, 255, 170, 0.22); border-color: #00FFAA; }"
                )
                def _open_hub():
                    win = self.window()
                    if win and hasattr(win, "navigation") and hasattr(win.navigation, "open_settings_page"):
                        win.navigation.open_settings_page(2)
                    elif win and hasattr(win, "_open_settings_page"):
                        getattr(win, "_open_settings_page")(2)
                hub_btn.clicked.connect(_open_hub)
                actions_row.addWidget(hub_btn)

                retry_btn = QPushButton(" Thử lại (Retry)")
                retry_btn.setIcon(create_vector_icon("retry", "#38BDF8", 14))
                retry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                retry_btn.setStyleSheet(
                    "QPushButton { background: rgba(56, 189, 248, 0.12); color: #38BDF8; "
                    "border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 8px; "
                    "padding: 8px 14px; font-size: 12px; font-weight: 600; } "
                    "QPushButton:hover { background: rgba(56, 189, 248, 0.22); border-color: #38BDF8; }"
                )
                retry_btn.clicked.connect(lambda: self.retryRequested.emit(self.msg.id))
                actions_row.addWidget(retry_btn)
                actions_row.addStretch()

                card_layout.addLayout(actions_row)

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
                btn.setIcon(create_vector_icon(act_id, DesignTokens.TEXT_MUTED, 15))
                btn.setFixedSize(26, 26)
                btn.setToolTip(tooltip)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet(
                    "QPushButton { border: none; background: transparent; } "
                    "QPushButton:hover { background: rgba(0, 229, 255, 0.12); border-radius: 6px; }"
                )
                
                def _handle_action(a=act_id):
                    if a == "copy":
                        cb = QApplication.clipboard()
                        if cb:
                            cb.setText(self.msg.text)
                    elif a == "retry":
                        self.retryRequested.emit(self.msg.id)
                    self.actionClicked.emit(a, self.msg.id)
                
                btn.clicked.connect(_handle_action)
                toolbar_layout.addWidget(btn)

            toolbar_layout.addStretch()
            card_layout.addLayout(toolbar_layout)

            main_layout.addWidget(avatar_lbl, alignment=Qt.AlignmentFlag.AlignTop)
            main_layout.addWidget(card)
            main_layout.addStretch(1)

    def _render_user_attachment_card(self, card_layout: QVBoxLayout, raw_text: str):
        """Render user message containing file attachments with clean cards and prompt."""
        lines = raw_text.strip().splitlines()
        header_line = lines[0] if lines else ""

        file_names = []
        if ":" in header_line:
            files_part = header_line.split(":", 1)[1].rstrip("]").strip()
            file_names = [f.strip() for f in files_part.split(",") if f.strip()]

        prompt_text = ""
        if "===" in raw_text:
            last_block = raw_text.split("===")[-1].strip()
            if last_block.startswith("["):
                last_block = last_block.split("]", 1)[-1].strip()
            prompt_text = last_block
        elif "---" in raw_text:
            prompt_text = raw_text.split("---")[-1].strip()

        if not prompt_text:
            prompt_text = "Phân tích và tóm tắt nội dung tệp tin."

        # File Pills Container
        files_widget = QWidget()
        files_widget.setMinimumWidth(0)
        files_widget.setStyleSheet("background: transparent; border: none;")
        files_layout = QHBoxLayout(files_widget)
        files_layout.setContentsMargins(0, 0, 0, 0)
        files_layout.setSpacing(6)

        for fname in file_names:
            pill = QFrame()
            pill.setMaximumWidth(220)
            pill.setMinimumWidth(0)
            pill.setToolTip(fname)
            pill.setStyleSheet(
                "QFrame { background: rgba(0, 255, 170, 0.08); border: 1px solid rgba(0, 255, 170, 0.28); border-radius: 8px; padding: 2px 8px; }"
            )
            pill_layout = QHBoxLayout(pill)
            pill_layout.setContentsMargins(4, 2, 4, 2)
            pill_layout.setSpacing(4)

            ext = fname.split(".")[-1].lower() if "." in fname else ""
            if ext in ["png", "jpg", "jpeg", "webp", "bmp"]:
                icon_type = "image"
                color = "#38BDF8"
            else:
                icon_type = "file"
                color = "#00FFAA"

            f_icon = QLabel()
            f_icon.setPixmap(create_vector_icon(icon_type, color, 14).pixmap(14, 14))
            f_icon.setStyleSheet("border: none; background: transparent;")
            pill_layout.addWidget(f_icon)

            fm = QFontMetrics(self.font())
            elided_name = fm.elidedText(fname, Qt.TextElideMode.ElideMiddle, 160)
            f_lbl = QLabel(elided_name)
            f_lbl.setToolTip(fname)
            f_lbl.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: 600; border: none; background: transparent;")
            pill_layout.addWidget(f_lbl)

            files_layout.addWidget(pill)

        files_layout.addStretch()
        card_layout.addWidget(files_widget)

        # Prompt text
        prompt_lbl = QLabel(prompt_text)
        prompt_lbl.setWordWrap(True)
        prompt_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MAIN}; font-size: 14px; line-height: 1.45; font-weight: 500;")
        card_layout.addWidget(prompt_lbl)

        # Collapsible details toggle
        toggle_btn = QPushButton("▶ Xem chi tiết nội dung tệp đã trích xuất")
        toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_btn.setStyleSheet(
            "QPushButton { border: none; background: transparent; color: #64748B; font-size: 11px; text-align: left; padding: 2px 0; } "
            "QPushButton:hover { color: #00FFAA; }"
        )

        content_box = QTextEdit()
        content_box.setReadOnly(True)
        content_box.setPlainText(raw_text)
        content_box.setMaximumHeight(160)
        content_box.setStyleSheet(
            "QTextEdit { background: rgba(0, 0, 0, 0.35); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; color: #94A3B8; font-size: 11px; padding: 6px; }"
        )
        content_box.hide()

        def _toggle():
            if content_box.isHidden():
                content_box.show()
                toggle_btn.setText("▼ Thu gọn nội dung tệp")
            else:
                content_box.hide()
                toggle_btn.setText("▶ Xem chi tiết nội dung tệp đã trích xuất")

        toggle_btn.clicked.connect(_toggle)
        card_layout.addWidget(toggle_btn)
        card_layout.addWidget(content_box)

    def animate_fade_in(self):
        """Smooth subtle fade-in animation for newly appended message bubbles."""
        op = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(op)
        self._fade_anim = QPropertyAnimation(op, b"opacity")
        self._fade_anim.setDuration(220)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _cleanup():
            # Release graphics effect after fade to restore hardware clipping
            self.setGraphicsEffect(None)

        self._fade_anim.finished.connect(_cleanup)
        self._fade_anim.start()
