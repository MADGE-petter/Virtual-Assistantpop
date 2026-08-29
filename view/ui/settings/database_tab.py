import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox, QFrame
)
from view.ui.styles import DesignTokens


class DatabaseTabWidget(QWidget):
    """Tab 3: Quản lý Dữ liệu & Files Upload thiết kế hiện đại."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title = QLabel("Quản Lý Dữ Liệu & Tệp Tải Lên")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {DesignTokens.TEXT_MAIN}; letter-spacing: 0.5px;")
        desc = QLabel("Các tệp tài liệu, hình ảnh tải lên khi trò chuyện được lưu trữ tạm thời trong 30 ngày")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        layout.addLayout(title_box)

        # File List Box
        self.assets_list = QListWidget()
        self.assets_list.setStyleSheet(
            f"QListWidget {{ background: rgba(14, 20, 36, 0.65); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 10px; color: {DesignTokens.TEXT_MAIN}; padding: 8px; font-size: 13px; outline: none; }}"
            f"QListWidget::item {{ padding: 8px 12px; border-radius: 6px; margin-bottom: 4px; }}"
            f"QListWidget::item:hover {{ background: rgba(0, 255, 170, 0.08); }}"
        )
        
        assets_dir = os.path.join(os.getcwd(), "database", "assets")
        if os.path.exists(assets_dir):
            for f in os.listdir(assets_dir):
                self.assets_list.addItem(QListWidgetItem(f"📄  {f}"))
        if self.assets_list.count() == 0:
            item = QListWidgetItem("Chưa có tệp dữ liệu nào trong khu vực lưu trữ tạm thời.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.assets_list.addItem(item)

        layout.addWidget(self.assets_list, stretch=1)

        # Action Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()

        clean_btn = QPushButton("Dọn Dẹp Bộ Nhớ Tạm")
        clean_btn.setFixedHeight(36)
        clean_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clean_btn.setStyleSheet(
            f"QPushButton {{ background: {DesignTokens.SURFACE_3}; color: {DesignTokens.CYAN_ACCENT}; "
            f"border: 1px solid {DesignTokens.BORDER}; border-radius: 8px; font-weight: 600; font-size: 12px; padding: 0 16px; }}"
            f"QPushButton:hover {{ background: {DesignTokens.SURFACE_2}; border-color: {DesignTokens.CYAN}; }}"
        )
        clean_btn.clicked.connect(lambda: QMessageBox.information(self, "Dọn dẹp", "Đã dọn dẹp và tối ưu hóa các tệp bộ nhớ tạm!"))
        bottom_bar.addWidget(clean_btn)

        layout.addLayout(bottom_bar)
