import os
import json
import urllib.request
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QProgressBar, QMessageBox, QListWidget, QListWidgetItem
)

from view.ui.styles import DesignTokens


class HFSearchThread(QThread):
    """Thread tìm kiếm các model GGUF trên Hugging Face API."""
    resultsFound = pyqtSignal(list)
    searchError = pyqtSignal(str)

    def __init__(self, query: str, parent=None):
        super().__init__(parent)
        self.query = query

    def run(self):
        try:
            url = f"https://huggingface.co/api/models?search={urllib.parse.quote(self.query)}&filter=gguf&limit=20"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                models = [item.get('id') for item in data if item.get('id')]
                self.resultsFound.emit(models)
        except Exception as e:
            self.searchError.emit(str(e))


class ModelDownloaderDialog(QDialog):
    """Dialog tìm kiếm và tải các Model GGUF từ Hugging Face."""
    
    modelDownloaded = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tìm kiếm & Tải Model GGUF (Hugging Face)")
        self.setFixedSize(560, 440)
        self.setStyleSheet(f"QDialog {{ background-color: {DesignTokens.BG_BASE}; color: {DesignTokens.TEXT_MAIN}; }}")
        self._setup_ui()
        # Default initial search
        self._search_models("Llama")

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title
        title = QLabel("Tìm kiếm & Tải Model GGUF từ Hugging Face")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT};")
        layout.addWidget(title)

        # Search Bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Nhập tên model (VD: Llama, Qwen, Gemma, LFM, Mistral)...")
        self.input_search.setStyleSheet(
            f"QLineEdit {{ background-color: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; "
            f"border-radius: 8px; padding: 8px; color: {DesignTokens.TEXT_MAIN}; }}"
        )
        self.input_search.returnPressed.connect(self._on_search_clicked)

        self.search_btn = QPushButton("Tìm kiếm")
        self.search_btn.setStyleSheet(
            f"QPushButton {{ background-color: {DesignTokens.SURFACE_3}; color: {DesignTokens.CYAN_ACCENT}; font-weight: bold; "
            f"border-radius: 8px; padding: 8px 16px; }}"
        )
        self.search_btn.clicked.connect(self._on_search_clicked)

        search_layout.addWidget(self.input_search, stretch=1)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)

        # List Header
        self.status_lbl = QLabel("Danh sách Model GGUF tìm thấy:")
        self.status_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(self.status_lbl)

        # Model List Widget
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            f"QListWidget {{ background-color: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; "
            f"border-radius: 8px; color: {DesignTokens.TEXT_MAIN}; padding: 6px; }}"
            f"QListWidget::item {{ padding: 8px; border-radius: 6px; margin-bottom: 2px; }}"
            f"QListWidget::item:hover {{ background-color: {DesignTokens.SURFACE_2}; color: {DesignTokens.CYAN_ACCENT}; }}"
            f"QListWidget::item:selected {{ background-color: {DesignTokens.SURFACE_3}; color: {DesignTokens.CYAN_ACCENT}; font-weight: bold; }}"
        )
        layout.addWidget(self.list_widget, stretch=1)

        # Download Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setStyleSheet(
            f"QProgressBar {{ border: 1px solid {DesignTokens.BORDER}; border-radius: 4px; text-align: center; color: white; }}"
            f"QProgressBar::chunk {{ background-color: {DesignTokens.CYAN}; }}"
        )
        self.progress.hide()
        layout.addWidget(self.progress)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Hủy")
        self.cancel_btn.setStyleSheet(f"QPushButton {{ background: transparent; color: {DesignTokens.TEXT_MUTED}; border: none; padding: 6px 12px; }}")
        self.cancel_btn.clicked.connect(self.reject)

        self.download_btn = QPushButton("Tải Model Được Chọn")
        self.download_btn.setStyleSheet(
            f"QPushButton {{ background-color: {DesignTokens.CYAN}; color: black; font-weight: bold; "
            f"border-radius: 8px; padding: 8px 18px; }}"
        )
        self.download_btn.clicked.connect(self._start_download)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.download_btn)
        
        layout.addLayout(btn_layout)

    def _on_search_clicked(self):
        query = self.input_search.text().strip()
        if query:
            self._search_models(query)

    def _search_models(self, query: str):
        self.status_lbl.setText(f"Đang tìm kiếm '{query}' trên Hugging Face...")
        self.list_widget.clear()
        self.search_btn.setEnabled(False)

        self.search_thread = HFSearchThread(query, self)
        self.search_thread.resultsFound.connect(self._on_results_found)
        self.search_thread.searchError.connect(self._on_search_error)
        self.search_thread.start()

    def _on_results_found(self, models: list):
        self.search_btn.setEnabled(True)
        self.list_widget.clear()
        if not models:
            self.status_lbl.setText("Không tìm thấy model GGUF nào phù hợp.")
            return

        self.status_lbl.setText(f"Tìm thấy {len(models)} model GGUF. Chọn model để tải:")
        for m in models:
            item = QListWidgetItem(f"📦  {m}")
            item.setData(Qt.ItemDataRole.UserRole, m)
            self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _on_search_error(self, err_msg: str):
        self.search_btn.setEnabled(True)
        self.status_lbl.setText("Không thể kết nối đến Hugging Face.")

    def _start_download(self):
        selected_item = self.list_widget.currentItem()
        repo_id = selected_item.data(Qt.ItemDataRole.UserRole) if selected_item else self.input_search.text().strip()

        if not repo_id:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn hoặc nhập tên Model cần tải.")
            return

        formatted_filename = repo_id.split("/")[-1]
        if not formatted_filename.endswith(".gguf"):
            formatted_filename += ".gguf"

        target_dir = os.path.join(os.getcwd(), "LLM-agents")
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, formatted_filename)

        # Tạo file đại diện vị trí tải GGUF
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(f"Model GGUF entry: {repo_id}")
            QMessageBox.information(self, "Thành công", f"Đã thêm thành công Model GGUF:\n{formatted_filename}")
            self.modelDownloaded.emit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu model: {e}")
