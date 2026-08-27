import os
import json
import time
import shutil
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QTabWidget, QWidget, QListWidget, QFileDialog, QMessageBox
)

from view.ui.styles import DesignTokens

class MemoryDialog(QDialog):
    """Quản lý Memory cốt lõi và dữ liệu ngắn hạn của khách hàng."""
    def __init__(self, user_name: str, parent=None):
        super().__init__(parent)
        self.user_name = user_name
        self.memory_file = os.path.join(os.getcwd(), "database", "user_memory.json")
        self.asset_dir = os.path.join(os.getcwd(), "database", "assets")
        self.setWindowTitle(f"Bộ nhớ (Memory) - {self.user_name}")
        self.setFixedSize(600, 450)
        self.setStyleSheet(f"QDialog {{ background-color: {DesignTokens.BG_BASE}; color: {DesignTokens.TEXT_MAIN}; }}")
        
        self._ensure_paths()
        self._cleanup_old_assets()
        self._setup_ui()
        self._load_core_memory()
        self._load_assets()

    def _ensure_paths(self):
        os.makedirs(os.path.join(os.getcwd(), "database"), exist_ok=True)
        os.makedirs(self.asset_dir, exist_ok=True)
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump({"core_memory": ""}, f, ensure_ascii=False)

    def _cleanup_old_assets(self):
        """Xóa các file quá 30 ngày trong asset_dir."""
        now = time.time()
        for f in os.listdir(self.asset_dir):
            filepath = os.path.join(self.asset_dir, f)
            if os.path.isfile(filepath):
                # 30 days = 30 * 24 * 60 * 60 = 2592000
                if os.stat(filepath).st_mtime < now - 2592000:
                    try:
                        os.remove(filepath)
                    except:
                        pass

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            f"QTabWidget::pane {{ border: 1px solid {DesignTokens.BORDER}; border-radius: 8px; background: {DesignTokens.SURFACE_1}; }}"
            f"QTabBar::tab {{ background: {DesignTokens.SURFACE_2}; color: {DesignTokens.TEXT_MUTED}; padding: 8px 16px; border-top-left-radius: 4px; border-top-right-radius: 4px; }}"
            f"QTabBar::tab:selected {{ background: {DesignTokens.SURFACE_1}; color: {DesignTokens.CYAN_ACCENT}; font-weight: bold; }}"
        )
        
        self.core_tab = QWidget()
        self._setup_core_tab()
        
        self.asset_tab = QWidget()
        self._setup_asset_tab()
        
        self.tabs.addTab(self.core_tab, "Core Memory (Cốt lõi)")
        self.tabs.addTab(self.asset_tab, "Tài liệu (30 Ngày)")
        
        layout.addWidget(self.tabs)

        # Close Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Đóng")
        close_btn.setStyleSheet(f"QPushButton {{ background: {DesignTokens.SURFACE_3}; color: white; border-radius: 8px; padding: 6px 16px; }}")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)

    def _setup_core_tab(self):
        layout = QVBoxLayout(self.core_tab)
        layout.setContentsMargins(12, 12, 12, 12)
        
        desc = QLabel("Ghi chú về thói quen, nghề nghiệp, sở thích của bạn. POP sẽ dùng thông tin này để cá nhân hóa câu trả lời (Ghi nhớ vĩnh viễn).")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-style: italic; margin-bottom: 8px;")
        
        self.core_text = QTextEdit()
        self.core_text.setStyleSheet(f"QTextEdit {{ background: {DesignTokens.SURFACE_2}; border: none; color: {DesignTokens.TEXT_MAIN}; border-radius: 8px; padding: 8px; }}")
        
        save_btn = QPushButton("Lưu thay đổi")
        save_btn.setStyleSheet(f"QPushButton {{ background: {DesignTokens.CYAN}; color: black; font-weight: bold; border-radius: 8px; padding: 8px; }}")
        save_btn.clicked.connect(self._save_core_memory)
        
        layout.addWidget(desc)
        layout.addWidget(self.core_text)
        layout.addWidget(save_btn)

    def _setup_asset_tab(self):
        layout = QVBoxLayout(self.asset_tab)
        layout.setContentsMargins(12, 12, 12, 12)
        
        desc = QLabel("Kéo thả hoặc thêm tài liệu/ảnh vào đây. Gợi ý: Tải model LFM 2.5 3B VL để POP có thể đọc ảnh hiệu quả. Các file tại đây sẽ tự động xóa sau 30 ngày.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-style: italic; margin-bottom: 8px;")
        
        self.asset_list = QListWidget()
        self.asset_list.setStyleSheet(f"QListWidget {{ background: {DesignTokens.SURFACE_2}; border: none; color: {DesignTokens.TEXT_MAIN}; border-radius: 8px; padding: 4px; }}")
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Thêm Tệp...")
        add_btn.setStyleSheet(f"QPushButton {{ background: {DesignTokens.CYAN}; color: black; font-weight: bold; border-radius: 6px; padding: 6px; }}")
        add_btn.clicked.connect(self._add_asset)
        
        del_btn = QPushButton("Xóa Tệp")
        del_btn.setStyleSheet(f"QPushButton {{ background: {DesignTokens.SURFACE_3}; color: {DesignTokens.CORAL_ACCENT}; border-radius: 6px; padding: 6px; }}")
        del_btn.clicked.connect(self._del_asset)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        
        layout.addWidget(desc)
        layout.addWidget(self.asset_list)
        layout.addLayout(btn_layout)

    def _load_core_memory(self):
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.core_text.setPlainText(data.get("core_memory", ""))
        except:
            pass

    def _save_core_memory(self):
        data = {"core_memory": self.core_text.toPlainText()}
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            QMessageBox.information(self, "Thành công", "Đã lưu Core Memory thành công!")
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể lưu: {e}")

    def _load_assets(self):
        self.asset_list.clear()
        for f in os.listdir(self.asset_dir):
            if os.path.isfile(os.path.join(self.asset_dir, f)):
                self.asset_list.addItem(f)

    def _add_asset(self):
        filepaths, _ = QFileDialog.getOpenFileNames(self, "Chọn tài liệu/ảnh")
        if filepaths:
            for path in filepaths:
                filename = os.path.basename(path)
                target = os.path.join(self.asset_dir, filename)
                shutil.copy2(path, target)
            self._load_assets()

    def _del_asset(self):
        selected = self.asset_list.currentItem()
        if selected:
            filename = selected.text()
            filepath = os.path.join(self.asset_dir, filename)
            try:
                os.remove(filepath)
                self._load_assets()
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Không thể xóa tệp: {e}")
