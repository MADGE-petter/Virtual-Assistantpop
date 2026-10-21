"""
MessageTextEdit Component - Ô nhập liệu tin nhắn đa dòng cho Input Bar.
- Hỗ trợ Shift + Enter để xuống dòng.
- Enter để phát tín hiệu gửi tin nhắn (sendRequested).
- Tự động ẩn hiện thanh cuộn và trong suốt theo phong cách POP Assistant.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QTextEdit


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
