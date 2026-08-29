import os
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QMessageBox, QFileDialog
)

from view.ui.styles import DesignTokens
from view.ui.icons import get_brand_logo_pixmap
from view.ui.settings.settings_config import save_user_settings


class ModelsTabWidget(QWidget):
    """Tab 2: Quản lý Models Cục Bộ phong cách hiện đại, tinh tế."""
    
    modelDownloaded = pyqtSignal()
    requestOpenDownloadTab = pyqtSignal()

    def __init__(self, user_settings: dict, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header Title Bar
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        title = QLabel("Quản Lý Models Cục Bộ")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {DesignTokens.TEXT_MAIN}; letter-spacing: 0.5px;")
        desc = QLabel("Các mô hình AI định dạng GGUF đã được tải và sẵn sàng sử dụng trên máy tính")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 13px;")

        title_box.addWidget(title)
        title_box.addWidget(desc)
        header_layout.addLayout(title_box, stretch=1)

        open_hub_btn = QPushButton("+ Tải Model Mới")
        open_hub_btn.setFixedHeight(36)
        open_hub_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_hub_btn.setStyleSheet(
            f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #008EFF, stop:1 #00FFAA); "
            f"color: #03050B; font-weight: bold; font-size: 12px; border: none; border-radius: 8px; padding: 0 16px; }}"
            f"QPushButton:hover {{ background: #00FFAA; }}"
        )
        open_hub_btn.clicked.connect(lambda: self.requestOpenDownloadTab.emit())
        header_layout.addWidget(open_hub_btn)

        layout.addLayout(header_layout)

        # Storage Directory Card
        dir_card = QFrame()
        dir_card.setStyleSheet(
            f"QFrame {{ background: rgba(14, 20, 36, 0.65); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 10px; }}"
        )
        df_layout = QHBoxLayout(dir_card)
        df_layout.setContentsMargins(14, 10, 14, 10)
        df_layout.setSpacing(12)

        dir_title = QLabel("Thư mục lưu trữ:")
        dir_title.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {DesignTokens.TEXT_MUTED};")

        self.txt_model_dir = QLineEdit(self.user_settings.get("model_dir", os.path.join(os.getcwd(), "LLM-agents")))
        self.txt_model_dir.setReadOnly(True)
        self.txt_model_dir.setStyleSheet(
            f"QLineEdit {{ background: {DesignTokens.SURFACE_2}; border: 1px solid {DesignTokens.BORDER}; "
            f"border-radius: 6px; padding: 6px 10px; font-size: 12px; color: {DesignTokens.CYAN_ACCENT}; }}"
        )

        change_dir_btn = QPushButton("Đổi thư mục...")
        change_dir_btn.setFixedHeight(30)
        change_dir_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        change_dir_btn.setStyleSheet(
            f"QPushButton {{ background: {DesignTokens.SURFACE_3}; color: {DesignTokens.TEXT_MAIN}; "
            f"border: 1px solid {DesignTokens.BORDER}; border-radius: 6px; padding: 0 12px; font-size: 12px; }}"
            f"QPushButton:hover {{ background: {DesignTokens.SURFACE_2}; border-color: {DesignTokens.CYAN}; }}"
        )
        change_dir_btn.clicked.connect(self._change_model_directory)

        df_layout.addWidget(dir_title)
        df_layout.addWidget(self.txt_model_dir, stretch=1)
        df_layout.addWidget(change_dir_btn)

        layout.addWidget(dir_card)

        # Section Label with Count Badge
        self.models_list_lbl = QLabel("Danh sách mô hình đã cài đặt:")
        self.models_list_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {DesignTokens.TEXT_MUTED}; margin-top: 4px;")
        layout.addWidget(self.models_list_lbl)

        # Scroll Area for Model Cards
        self.scroll_models = QScrollArea()
        self.scroll_models.setWidgetResizable(True)
        self.scroll_models.setFrameShape(QFrame.Shape.NoFrame)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)

        self.scroll_models.setWidget(self.cards_container)
        layout.addWidget(self.scroll_models, stretch=1)

        self.reload_local_models()

    def _change_model_directory(self):
        new_dir = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu trữ Models", self.txt_model_dir.text())
        if new_dir:
            self.txt_model_dir.setText(new_dir)
            self.user_settings["model_dir"] = new_dir
            save_user_settings(self.user_settings)
            self.reload_local_models()
            QMessageBox.information(self, "Thành công", f"Đã đổi thư mục lưu model thành:\n{new_dir}")

    def reload_local_models(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        target_dir = self.user_settings.get("model_dir", os.path.join(os.getcwd(), "LLM-agents"))
        if not os.path.exists(target_dir) or not os.listdir(target_dir):
            empty_card = QFrame()
            empty_card.setStyleSheet("QFrame { background: rgba(14, 20, 36, 0.4); border: 1px dashed rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 24px; }")
            ec_layout = QVBoxLayout(empty_card)
            ec_lbl = QLabel("Chưa có mô hình nào trong thư mục máy tính.\nNhấp vào nút '+ Tải Model Mới' ở trên để khám phá & tải mô hình về.")
            ec_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ec_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 13px; line-height: 1.6;")
            ec_layout.addWidget(ec_lbl)
            self.cards_layout.addWidget(empty_card)
            self.models_list_lbl.setText("Danh sách mô hình đã cài đặt (0):")
            self.cards_layout.addStretch()
            return

        count = 0
        total_size_mb = 0.0
        for item in sorted(os.listdir(target_dir)):
            if item.startswith('.'): continue
            full_p = os.path.join(target_dir, item)
            size_mb = (os.path.getsize(full_p) / (1024 * 1024)) if os.path.isfile(full_p) else 0.0
            total_size_mb += size_mb

            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background: rgba(14, 20, 36, 0.65); border: 1px solid rgba(255, 255, 255, 0.08); "
                f"border-radius: 10px; padding: 12px 16px; }}"
                f"QFrame:hover {{ border-color: rgba(0, 255, 170, 0.25); background: rgba(18, 26, 46, 0.8); }}"
            )
            cl = QHBoxLayout(card)
            cl.setContentsMargins(4, 2, 4, 2)
            cl.setSpacing(14)

            icon_lbl = QLabel()
            icon_lbl.setPixmap(get_brand_logo_pixmap(item, 34))
            cl.addWidget(icon_lbl)

            info_box = QVBoxLayout()
            info_box.setSpacing(3)
            
            name_lbl = QLabel(item)
            name_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {DesignTokens.TEXT_MAIN};")

            size_str = f"{size_mb / 1024:.2f} GB" if size_mb >= 1024 else f"{size_mb:.1f} MB"
            sub_lbl = QLabel(f"<font color='#00FFAA'>● Sẵn sàng</font> &nbsp;•&nbsp; <font color='#8A9EB5'>Dung lượng: {size_str}</font> &nbsp;•&nbsp; <font color='#8A9EB5'>Định dạng GGUF</font>")
            sub_lbl.setStyleSheet("font-size: 11px;")

            info_box.addWidget(name_lbl)
            info_box.addWidget(sub_lbl)
            cl.addLayout(info_box, stretch=1)

            del_btn = QPushButton("Xóa")
            del_btn.setFixedHeight(28)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setStyleSheet(
                f"QPushButton {{ background: rgba(255, 75, 110, 0.12); color: #FF4B6E; border: 1px solid rgba(255, 75, 110, 0.3); "
                f"border-radius: 6px; padding: 0 14px; font-size: 11px; font-weight: 600; }}"
                f"QPushButton:hover {{ background: rgba(255, 75, 110, 0.28); border-color: #FF4B6E; }}"
            )
            del_btn.clicked.connect(lambda _, path=full_p: self._delete_local_model(path))
            cl.addWidget(del_btn)

            self.cards_layout.addWidget(card)
            count += 1

        total_str = f"{total_size_mb / 1024:.2f} GB" if total_size_mb >= 1024 else f"{total_size_mb:.1f} MB"
        self.models_list_lbl.setText(f"Danh sách mô hình đã cài đặt ({count} models • Tổng dung lượng: {total_str}):")
        self.cards_layout.addStretch()

    def _delete_local_model(self, path: str):
        if QMessageBox.question(self, "Xác nhận", f"Bạn có chắc muốn xóa model này khỏi đĩa cứng?\n\n{os.path.basename(path)}") == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isfile(path): os.remove(path)
                elif os.path.isdir(path): import shutil; shutil.rmtree(path)
                self.reload_local_models()
                self.modelDownloaded.emit()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể xóa model: {e}")
