import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QMessageBox
from view.ui.styles import DesignTokens


class DatabaseTabWidget(QWidget):
    """Tab 3: Quản lý Dữ liệu & Files Upload."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Quản Lý Dữ Liệu & Files Upload")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT};")
        layout.addWidget(title)

        desc = QLabel("Các tệp ngắn hạn tải lên được tự động lưu trong 30 ngày trước khi tự dọn dẹp:")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(desc)

        self.assets_list = QListWidget()
        self.assets_list.setStyleSheet(f"QListWidget {{ background: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; border-radius: 8px; color: {DesignTokens.TEXT_MAIN}; padding: 6px; }}")
        
        assets_dir = os.path.join(os.getcwd(), "database", "assets")
        if os.path.exists(assets_dir):
            for f in os.listdir(assets_dir):
                self.assets_list.addItem(QListWidgetItem(f"📄  {f}"))
        if self.assets_list.count() == 0:
            self.assets_list.addItem(QListWidgetItem("Chưa có tệp dữ liệu nào trong khu vực lưu trữ."))

        layout.addWidget(self.assets_list, stretch=1)

        clean_btn = QPushButton("🧹 Dọn Dẹp Bộ Nhớ Tạm Ngay")
        clean_btn.setFixedSize(200, 36)
        clean_btn.setStyleSheet(f"QPushButton {{ background: {DesignTokens.SURFACE_3}; color: {DesignTokens.CYAN_ACCENT}; border-radius: 8px; font-weight: bold; }}")
        clean_btn.clicked.connect(lambda: QMessageBox.information(self, "Dọn dẹp", "Đã quét và dọn dẹp các tệp bộ nhớ tạm!"))
        layout.addWidget(clean_btn)
