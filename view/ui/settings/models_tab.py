import os
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QMessageBox, QFileDialog
)

from view.ui.styles import DesignTokens
from view.ui.icons import get_brand_logo_pixmap
from view.ui.settings.settings_config import save_user_settings


class ModelsTabWidget(QWidget):
    """Tab 2: Quản lý Models Cục Bộ (Kiểm tra, Xóa, Đổi thư mục)."""
    
    modelDownloaded = pyqtSignal()
    requestOpenDownloadTab = pyqtSignal()

    def __init__(self, user_settings: dict, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Title & Description
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title = QLabel("Quản Lý Models Cục Bộ")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT};")
        desc = QLabel("Quản lý danh sách các mô hình GGUF đã tải về máy, dung lượng và vị trí lưu trữ")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 12px;")

        title_box.addWidget(title)
        title_box.addWidget(desc)
        header_layout.addLayout(title_box, stretch=1)

        open_hub_btn = QPushButton("📥 Tải Thêm Model Mới")
        open_hub_btn.setStyleSheet(
            f"QPushButton {{ background: {DesignTokens.SURFACE_3}; color: {DesignTokens.CYAN_ACCENT}; font-weight: bold; "
            f"border: 1px solid {DesignTokens.BORDER}; border-radius: 8px; padding: 8px 14px; }}"
            f"QPushButton:hover {{ background: {DesignTokens.SURFACE_2}; border-color: {DesignTokens.CYAN}; }}"
        )
        open_hub_btn.clicked.connect(lambda: self.requestOpenDownloadTab.emit())
        header_layout.addWidget(open_hub_btn)

        layout.addLayout(header_layout)

        # Custom Directory Settings Section
        dir_frame = QFrame()
        dir_frame.setStyleSheet(f"QFrame {{ background: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; border-radius: 10px; padding: 10px; }}")
        df_layout = QHBoxLayout(dir_frame)
        df_layout.setContentsMargins(10, 6, 10, 6)

        dir_lbl = QLabel("Thư mục lưu trữ Models:")
        dir_lbl.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {DesignTokens.TEXT_MAIN};")

        self.txt_model_dir = QLineEdit(self.user_settings.get("model_dir", os.path.join(os.getcwd(), "LLM-agents")))
        self.txt_model_dir.setReadOnly(True)
        self.txt_model_dir.setStyleSheet(f"QLineEdit {{ background: {DesignTokens.SURFACE_2}; border: 1px solid {DesignTokens.BORDER}; border-radius: 6px; padding: 6px; font-size: 12px; color: {DesignTokens.CYAN_ACCENT}; }}")

        change_dir_btn = QPushButton("📁 Đổi thư mục...")
        change_dir_btn.setStyleSheet(f"QPushButton {{ background: {DesignTokens.SURFACE_3}; color: white; border-radius: 6px; padding: 6px 12px; font-size: 12px; }}")
        change_dir_btn.clicked.connect(self._change_model_directory)

        df_layout.addWidget(dir_lbl)
        df_layout.addWidget(self.txt_model_dir, stretch=1)
        df_layout.addWidget(change_dir_btn)

        layout.addWidget(dir_frame)

        # Local Installed Models List
        self.models_list_lbl = QLabel("📦 Các Model đã cài đặt cục bộ:")
        self.models_list_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {DesignTokens.TEXT_MUTED};")
        layout.addWidget(self.models_list_lbl)

        self.scroll_models = QScrollArea()
        self.scroll_models.setWidgetResizable(True)
        self.scroll_models.setFrameShape(QFrame.Shape.NoFrame)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)

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
            no_lbl = QLabel("Chưa có model nào trong thư mục. Bấm nút 'Tải Thêm Model Mới' ở trên để tìm & tải model!")
            no_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-style: italic; margin-top: 10px;")
            self.cards_layout.addWidget(no_lbl)
            self.cards_layout.addStretch()
            return

        count = 0
        for item in os.listdir(target_dir):
            if item.startswith('.'): continue
            full_p = os.path.join(target_dir, item)
            size_mb = os.path.getsize(full_p) / (1024 * 1024) if os.path.isfile(full_p) else 0

            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; border-radius: 8px; padding: 10px; }}")
            cl = QHBoxLayout(card)

            icon_lbl = QLabel()
            icon_lbl.setPixmap(get_brand_logo_pixmap(item, 32))
            cl.addWidget(icon_lbl)

            info_lbl = QLabel(f"<b>{item}</b><br><font color='#557088'>Dung lượng: {size_mb:.1f} MB • Local GGUF</font>")
            info_lbl.setStyleSheet("font-size: 13px;")
            cl.addWidget(info_lbl, stretch=1)

            del_btn = QPushButton("🗑️ Xóa Model")
            del_btn.setStyleSheet(f"QPushButton {{ background: rgba(255, 75, 110, 0.15); color: #FF4B6E; border: 1px solid #FF4B6E; border-radius: 6px; padding: 6px 12px; font-weight: bold; }} QPushButton:hover {{ background: rgba(255, 75, 110, 0.3); }}")
            del_btn.clicked.connect(lambda _, path=full_p: self._delete_local_model(path))
            cl.addWidget(del_btn)

            self.cards_layout.addWidget(card)
            count += 1

        self.models_list_lbl.setText(f"📦 Các Model đã cài đặt cục bộ ({count}):")
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
