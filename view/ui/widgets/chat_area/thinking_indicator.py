"""
Thinking Indicator Widget - Animated thinking loader dots.
"""

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel

from view.ui.styles import DesignTokens


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
        self.text_lbl.setStyleSheet(
            f"color: {DesignTokens.TEXT_MUTED}; font-size: 13px; font-style: italic; font-weight: 500;"
        )

        layout.addWidget(self.text_lbl)
        layout.addStretch()

    def _animate_dots(self):
        self._step += 1
        dots = "." * (self._step % 4)
        self.text_lbl.setText(f"thinking{dots}")
