"""
File Preview Card Widget - Displays search results with action buttons.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget

from view.ui.styles import DesignTokens


class FilePreviewCardWidget(QFrame):
    """File Preview Card displaying search results with action buttons."""

    openFileRequested = pyqtSignal(str)

    def __init__(self, files: list, parent=None):
        super().__init__(parent)
        self.files = files
        self.setStyleSheet(
            f"QFrame {{ background: transparent; border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; border-radius: 14px; }}"
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
            open_btn.setStyleSheet(
                f"QPushButton {{ background: {DesignTokens.SURFACE_3}; color: {DesignTokens.CYAN}; border: none; border-radius: 6px; padding: 4px 8px; font-size: 11px; }}"
            )
            open_btn.clicked.connect(lambda _, p=f.get('path'): self.openFileRequested.emit(p))

            file_row.addWidget(name_lbl, stretch=1)
            file_row.addWidget(size_lbl)
            file_row.addWidget(open_btn)

            row_w = QWidget()
            row_w.setLayout(file_row)
            layout.addWidget(row_w)
