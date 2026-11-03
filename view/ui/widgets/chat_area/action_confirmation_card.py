"""
Action Confirmation Card Widget - Human-in-the-Loop Confirmation Card.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

from view.ui.styles import DesignTokens
from view.ui.icons import create_vector_icon


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
            f"QFrame {{ background: transparent; border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; border-radius: 14px; }}"
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
        confirm_btn.setIcon(create_vector_icon("check", "#040812", 14))
        confirm_btn.setFixedHeight(32)
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.setStyleSheet(
            f"QPushButton {{ background: {DesignTokens.GRADIENT_BLUE_GREEN}; color: #040812; font-weight: 700; border: none; border-radius: 8px; padding: 0 14px; }}"
            f"QPushButton:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0077D6, stop:1 #00E699); }}"
        )
        confirm_btn.clicked.connect(lambda: self.confirmed.emit(self.tool_name, self.tool_args))

        cancel_btn = QPushButton(" Hủy bỏ")
        cancel_btn.setIcon(create_vector_icon("close", DesignTokens.CORAL_ACCENT, 14))
        cancel_btn.setFixedHeight(32)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {DesignTokens.CORAL_ACCENT}; border: 1px solid rgba(244, 63, 94, 0.3); border-radius: 8px; padding: 0 14px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: rgba(244, 63, 94, 0.2); border-color: {DesignTokens.CORAL_ACCENT}; }}"
        )
        cancel_btn.clicked.connect(lambda: self.cancelled.emit())

        btn_box.addWidget(confirm_btn)
        btn_box.addWidget(cancel_btn)
        btn_box.addStretch()

        layout.addWidget(title_lbl)
        layout.addWidget(summary_lbl)
        layout.addLayout(btn_box)
