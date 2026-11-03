"""
AttachedFileSquare Component - Thẻ preview tệp đính kèm hình vuông (58x58 px).
- Hiển thị badge định dạng (PNG, PDF, DOCX, PY...).
- Hiển thị thumbnail với hình ảnh hoặc vector icon theo từng loại tệp.
- Tooltip hiển thị tên tệp và kích thước (KB / MB).
- Nút đóng (X) nhỏ để gỡ tệp khỏi danh sách gửi.
"""

import os
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from view.ui.icons import create_vector_icon


class AttachedFileSquare(QFrame):
    """Compact square preview tile (hình vuông 3x3 ~ 58x58 px) matching modern AI chat specs."""

    removeRequested = pyqtSignal(str)

    def __init__(self, file_path: str = "", parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setFixedSize(58, 58)
        self.setStyleSheet(
            "QFrame { "
            "background: rgba(255, 255, 255, 0.08); "
            "border: 1px solid rgba(255, 255, 255, 0.18); "
            "border-radius: 12px; "
            "} "
            "QFrame:hover { "
            "background: rgba(255, 255, 255, 0.14); "
            "border-color: rgba(0, 255, 170, 0.50); "
            "}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 4, 4)
        layout.setSpacing(2)

        # Top row: Extension badge & close button
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(2)

        self.ext_badge = QLabel("FILE")
        self.ext_badge.setStyleSheet(
            "font-size: 9px; font-weight: 800; color: #00FFAA; border: none; background: transparent;"
        )
        top_row.addWidget(self.ext_badge)
        top_row.addStretch()

        self.remove_btn = QPushButton()
        self.remove_btn.setIcon(create_vector_icon("close", "#FFFFFF", 9))
        self.remove_btn.setIconSize(QSize(9, 9))
        self.remove_btn.setFixedSize(16, 16)
        self.remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_btn.setToolTip("Gỡ tệp này")
        self.remove_btn.setStyleSheet(
            "QPushButton { "
            "border: none; "
            "background: rgba(255, 255, 255, 0.20); "
            "border-radius: 8px; "
            "padding: 0px; "
            "margin: 0px; "
            "} "
            "QPushButton:hover { "
            "background: #F43F5E; "
            "}"
        )
        self.remove_btn.clicked.connect(lambda: self.removeRequested.emit(self.file_path))
        top_row.addWidget(self.remove_btn)

        layout.addLayout(top_row)

        # Center: Document vector icon
        self.icon_lbl = QLabel()
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(self.icon_lbl, stretch=1)

        if file_path:
            self.set_file(file_path)

    def set_file(self, file_path: str):
        self.file_path = file_path
        file_name = os.path.basename(file_path)
        ext = os.path.splitext(file_path)[1].lower().replace(".", "")
        if os.path.exists(file_path):
            size_kb = os.path.getsize(file_path) / 1024
            size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"
        else:
            size_str = "0 KB"

        self.setToolTip(f"{file_name}\n({size_str})")
        ext_upper = ext.upper()[:4] if ext else "FILE"
        self.ext_badge.setText(ext_upper)

        is_image = ext in ["png", "jpg", "jpeg", "webp", "bmp", "gif"]
        if is_image:
            color = "#38BDF8"  # Sky Blue for images
            self.ext_badge.setStyleSheet(
                f"font-size: 9px; font-weight: 800; color: {color}; border: none; background: transparent;"
            )
            pix = QPixmap(file_path)
            if not pix.isNull():
                thumb = pix.scaled(
                    38, 30,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.icon_lbl.setPixmap(thumb)
            else:
                self.icon_lbl.setPixmap(create_vector_icon("image", color, 22).pixmap(22, 22))
        else:
            if ext in ["pdf"]:
                color = "#F43F5E"  # Red / Coral
            elif ext in ["doc", "docx"]:
                color = "#008EFF"  # Blue
            elif ext in ["xls", "xlsx", "csv"]:
                color = "#00FFAA"  # Emerald Green
            elif ext in ["ppt", "pptx"]:
                color = "#F59E0B"  # Amber Orange
            elif ext in ["py", "js", "ts", "json", "html", "css", "cpp", "c", "java", "sql"]:
                color = "#A855F7"  # Purple for code
            else:
                color = "#94A3B8"  # Slate

            self.ext_badge.setStyleSheet(
                f"font-size: 9px; font-weight: 800; color: {color}; border: none; background: transparent;"
            )
            self.icon_lbl.setPixmap(create_vector_icon("file", color, 22).pixmap(22, 22))
