"""
POP Input Bar Widget - Glowing Chat Input Container matching po spec annotation #11.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QSize
from PyQt6.QtGui import QKeyEvent, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFrame
)

from view.ui.styles import DesignTokens
from view.ui.icons import create_vector_icon


class MessageTextEdit(QTextEdit):
    """Custom Multi-line TextEdit with Shift+Enter / Enter key handler."""

    sendRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Nhập tin nhắn cho POP...")
        self.setFixedHeight(38)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(
            "QTextEdit { border: none; background: transparent; font-size: 14px; color: #E6F4FF; padding: 4px 0; }"
        )

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.sendRequested.emit()
                event.accept()
        else:
            super().keyPressEvent(event)


class InputBarWidget(QWidget):
    """Bottom input box container matching annotation #11 with responsive layout scaling."""

    sendMessage = pyqtSignal(str)
    voiceToggle = pyqtSignal()
    attachmentClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 4, 16, 10)
        main_layout.setSpacing(6)

        # ----------------------------------------------------
        # GLOWING INPUT CONTAINER
        # ----------------------------------------------------
        self.input_frame = QFrame()
        self.input_frame.setObjectName("inputFrame")
        self.input_frame.setMaximumWidth(960)
        self.input_frame.setStyleSheet(
            f"QFrame#inputFrame {{ background-color: rgba(16, 22, 31, 0.9); border: 1px solid rgba(0, 255, 255, 0.3); border-radius: 24px; }}"
            f"QFrame#inputFrame:hover {{ border-color: rgba(0, 255, 255, 0.6); }}"
        )
        box_layout = QHBoxLayout(self.input_frame)
        box_layout.setContentsMargins(14, 6, 10, 6)
        box_layout.setSpacing(10)

        # Attachment Button (Paperclip)
        self.attach_btn = QPushButton()
        self.attach_btn.setIcon(create_vector_icon("attachment", "#96D7E9", 20))
        self.attach_btn.setFixedSize(36, 36)
        self.attach_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.attach_btn.setToolTip("Tải lên tệp / ảnh")
        self.attach_btn.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background: rgba(255,255,255,0.08); border-radius: 18px; }")
        self.attach_btn.clicked.connect(lambda: self.attachmentClicked.emit())

        # Text Input Area
        self.text_edit = MessageTextEdit()
        self.text_edit.sendRequested.connect(self._handle_send)

        # Voice Microphone Button
        self.mic_btn = QPushButton()
        self.mic_btn.setIcon(create_vector_icon("mic", "#96D7E9", 20))
        self.mic_btn.setFixedSize(36, 36)
        self.mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mic_btn.setToolTip("Bật/tắt micro")
        self.mic_btn.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background: rgba(0,255,255,0.12); border-radius: 18px; }")
        self.mic_btn.clicked.connect(lambda: self.voiceToggle.emit())

        # Send Button (Cyan filled circle)
        self.send_btn = QPushButton()
        self.send_btn.setIcon(create_vector_icon("send", "#03050B", 18))
        self.send_btn.setFixedSize(36, 36)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setToolTip("Gửi tin nhắn")
        self.send_btn.setStyleSheet(
            f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #008EFF, stop:1 #00FFAA); border: none; border-radius: 18px; }}"
            f"QPushButton:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00A6FF, stop:1 #33FFBC); }}"
        )
        self.send_btn.clicked.connect(self._handle_send)

        box_layout.addWidget(self.attach_btn)
        box_layout.addWidget(self.text_edit, stretch=1)
        box_layout.addWidget(self.mic_btn)
        box_layout.addWidget(self.send_btn)

        # Center input frame container
        frame_wrapper = QHBoxLayout()
        frame_wrapper.setContentsMargins(0, 0, 0, 0)
        frame_wrapper.addStretch()
        frame_wrapper.addWidget(self.input_frame, stretch=10)
        frame_wrapper.addStretch()

        main_layout.addLayout(frame_wrapper)

        # ----------------------------------------------------
        # KEYBOARD SHORTCUT / DISCLAIMER CAPTION
        # ----------------------------------------------------
        self.sub_text_lbl = QLabel("Enter để gửi • Shift + Enter để xuống dòng")
        self.sub_text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_text_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 11px;")
        main_layout.addWidget(self.sub_text_lbl)

    def _handle_send(self):
        text = self.text_edit.toPlainText().strip()
        if text:
            self.sendMessage.emit(text)
            self.text_edit.clear()

    def set_listening(self, is_listening: bool):
        """Update microphone button color state when active."""
        if is_listening:
            self.mic_btn.setIcon(create_vector_icon("mic", "#00FFAA", 20))
            self.mic_btn.setStyleSheet("QPushButton { background: rgba(0, 255, 170, 0.2); border-radius: 18px; }")
        else:
            self.mic_btn.setIcon(create_vector_icon("mic", "#96D7E9", 20))
            self.mic_btn.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background: rgba(0,255,255,0.12); border-radius: 18px; }")
