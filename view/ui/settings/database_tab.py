import os
import shutil
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QFrame, QMessageBox, QFileDialog
)
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
from view.ui.styles import DesignTokens


class DatabaseTabWidget(QWidget):
    """Tab 3: Quản lý Dữ liệu & Files Upload theo phong cách Dashboard công nghệ cao."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.assets_dir = os.path.join(os.getcwd(), "database", "assets")
        os.makedirs(self.assets_dir, exist_ok=True)
        self._setup_ui()
        self._reload_file_list()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        # Header
        title_box = QVBoxLayout()
        title_box.setSpacing(6)

        title_row = QHBoxLayout()
        title = QLabel("Quản Lý Dữ Liệu & Tệp Đính Kèm")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {DesignTokens.TEXT_MAIN}; letter-spacing: 0.5px;")

        badge = QLabel("STORAGE & ASSETS")
        badge.setStyleSheet(
            f"background: rgba(0, 204, 255, 0.12); color: {DesignTokens.CYAN}; font-size: 11px; "
            f"font-weight: 700; border-radius: 4px; padding: 2px 8px; border: 1px solid rgba(0, 204, 255, 0.25);"
        )
        title_row.addWidget(title)
        title_row.addWidget(badge)
        title_row.addStretch()

        desc = QLabel("Các tệp tài liệu, hình ảnh đính kèm khi trò chuyện được lưu trữ an toàn trong thư mục máy tính")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 13px;")

        title_box.addLayout(title_row)
        title_box.addWidget(desc)
        layout.addLayout(title_box)

        # Statistics Cards Row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)

        self.card_files = self._create_stat_card("TỔNG TỆP TIN", "0 tệp", "Trong thư mục assets")
        self.card_size = self._create_stat_card("DUNG LƯỢNG", "0.0 MB", "Chiếm dụng đĩa cứng")
        self.card_policy = self._create_stat_card("CHÍNH SÁCH", "30 Ngày", "Tự động dọn tệp rác")

        stats_row.addWidget(self.card_files[0])
        stats_row.addWidget(self.card_size[0])
        stats_row.addWidget(self.card_policy[0])
        layout.addLayout(stats_row)

        # Section Label
        sec_lbl = QLabel("Danh sách tệp dữ liệu trong kho tạm:")
        sec_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {DesignTokens.TEXT_MUTED}; margin-top: 4px;")
        layout.addWidget(sec_lbl)

        # File List Box
        self.assets_list = QListWidget()
        self.assets_list.setStyleSheet(
            f"QListWidget {{ background: rgba(16, 22, 31, 0.75); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 12px; color: {DesignTokens.TEXT_MAIN}; padding: 8px; font-size: 13px; outline: none; }}"
            f"QListWidget::item {{ padding: 10px 14px; border-radius: 8px; margin-bottom: 4px; background: rgba(21, 28, 39, 0.4); border: 1px solid rgba(255, 255, 255, 0.04); }}"
            f"QListWidget::item:hover {{ background: rgba(0, 255, 170, 0.08); border-color: rgba(0, 255, 170, 0.25); color: #FFFFFF; }}"
        )
        self.assets_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.assets_list, stretch=1)

        # Action Bar
        bottom_bar = QHBoxLayout()
        
        self.status_feedback = QLabel("")
        self.status_feedback.setStyleSheet(f"color: {DesignTokens.CYAN_ACCENT}; font-size: 13px; font-weight: 600;")
        self.status_feedback.hide()
        bottom_bar.addWidget(self.status_feedback)

        bottom_bar.addStretch()

        open_folder_btn = QPushButton("Mở Thư Mục")
        open_folder_btn.setFixedHeight(36)
        open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_folder_btn.setStyleSheet(
            f"QPushButton {{ background: {DesignTokens.SURFACE_2}; color: {DesignTokens.TEXT_MAIN}; "
            f"border: 1px solid {DesignTokens.BORDER}; border-radius: 8px; font-weight: 500; font-size: 12px; padding: 0 16px; }}"
            f"QPushButton:hover {{ background: {DesignTokens.SURFACE_3}; border-color: {DesignTokens.CYAN}; color: {DesignTokens.CYAN_ACCENT}; }}"
        )
        open_folder_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(self.assets_dir)))
        bottom_bar.addWidget(open_folder_btn)

        clean_btn = QPushButton("Dọn Dẹp Bộ Nhớ Tạm")
        clean_btn.setFixedHeight(36)
        clean_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clean_btn.setStyleSheet(
            f"QPushButton {{ background: rgba(255, 75, 110, 0.12); color: {DesignTokens.CORAL_ACCENT}; "
            f"border: 1px solid rgba(255, 75, 110, 0.3); border-radius: 8px; font-weight: 600; font-size: 12px; padding: 0 18px; }}"
            f"QPushButton:hover {{ background: rgba(255, 75, 110, 0.25); color: #FFFFFF; border-color: {DesignTokens.CORAL_ACCENT}; }}"
        )
        clean_btn.clicked.connect(self._clean_temp_files)
        bottom_bar.addWidget(clean_btn)

        layout.addLayout(bottom_bar)

    def _create_stat_card(self, title: str, value: str, sub: str):
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: rgba(16, 22, 31, 0.75); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 12px; padding: 12px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(12, 10, 12, 10)
        cl.setSpacing(4)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {DesignTokens.TEXT_MUTED}; letter-spacing: 0.5px;")

        lbl_v = QLabel(value)
        lbl_v.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {DesignTokens.CYAN_ACCENT};")

        lbl_s = QLabel(sub)
        lbl_s.setStyleSheet(f"font-size: 11px; color: {DesignTokens.TEXT_MUTED};")

        cl.addWidget(lbl_t)
        cl.addWidget(lbl_v)
        cl.addWidget(lbl_s)
        return card, lbl_v

    def _reload_file_list(self):
        from view.ui.icons import create_vector_icon
        from PyQt6.QtCore import QSize
        self.assets_list.clear()
        self.assets_list.setIconSize(QSize(18, 18))
        total_size = 0.0
        count = 0

        if os.path.exists(self.assets_dir):
            for f in sorted(os.listdir(self.assets_dir)):
                full_p = os.path.join(self.assets_dir, f)
                if os.path.isfile(full_p):
                    count += 1
                    sz = os.path.getsize(full_p)
                    total_size += sz
                    sz_str = f"{sz / 1024:.1f} KB" if sz < 1024 * 1024 else f"{sz / (1024*1024):.2f} MB"
                    
                    file_icon = create_vector_icon("file", "#E6F4FF", 18)
                    item = QListWidgetItem(file_icon, f"  {f}    ({sz_str})")
                    item.setData(Qt.ItemDataRole.UserRole, full_p)
                    self.assets_list.addItem(item)

        if count == 0:
            empty_item = QListWidgetItem("Chưa có tệp tài liệu hay hình ảnh nào trong thư mục lưu trữ tạm thời.")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.assets_list.addItem(empty_item)

        self.card_files[1].setText(f"{count} tệp")
        size_mb = total_size / (1024 * 1024)
        self.card_size[1].setText(f"{size_mb:.1f} MB")

    def _on_item_double_clicked(self, item: QListWidgetItem):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path and os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def _clean_temp_files(self):
        if not os.path.exists(self.assets_dir) or not os.listdir(self.assets_dir):
            self.status_feedback.setText("Thư mục lưu trữ tạm thời đã trống.")
            self.status_feedback.show()
            QTimer.singleShot(2500, lambda: self.status_feedback.hide())
            return

        confirm = QMessageBox(self)
        confirm.setWindowTitle("Xác nhận dọn dẹp")
        confirm.setText("Bạn có chắc muốn xóa tất cả tệp dữ liệu tạm thời trong thư mục assets?")
        confirm.setIcon(QMessageBox.Icon.Question)
        confirm.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm.setDefaultButton(QMessageBox.StandardButton.No)
        if confirm.exec() == QMessageBox.StandardButton.Yes:
            try:
                for f in os.listdir(self.assets_dir):
                    fp = os.path.join(self.assets_dir, f)
                    if os.path.isfile(fp): os.remove(fp)
                    elif os.path.isdir(fp): shutil.rmtree(fp)
                self._reload_file_list()
                self.status_feedback.setText("Đã dọn dẹp bộ nhớ tạm thành công.")
                self.status_feedback.show()
                QTimer.singleShot(2600, lambda: self.status_feedback.hide())
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể dọn dẹp: {e}")
