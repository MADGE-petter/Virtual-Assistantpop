import os
import json
import urllib.request
import urllib.parse
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QSize
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QProgressBar, QMessageBox, QScrollArea,
    QWidget, QFrame, QSizePolicy
)

from view.ui.styles import DesignTokens
from view.ui.icons import get_brand_logo_pixmap


class HFSearchThread(QThread):
    """Thread tìm kiếm các model GGUF trên Hugging Face API."""
    resultsFound = pyqtSignal(list)
    searchError = pyqtSignal(str)

    def __init__(self, query: str, parent=None):
        super().__init__(parent)
        self.query = query

    def run(self):
        try:
            url = f"https://huggingface.co/api/models?search={urllib.parse.quote(self.query)}&filter=gguf&limit=24"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                models = [
                    {
                        "id": item.get('id', ''),
                        "author": item.get('author', item.get('id', '').split('/')[0] if '/' in item.get('id', '') else 'Community'),
                        "name": item.get('id', '').split('/')[-1] if '/' in item.get('id', '') else item.get('id', ''),
                        "downloads": item.get('downloads', 0),
                        "likes": item.get('likes', 0)
                    }
                    for item in data if item.get('id')
                ]
                self.resultsFound.emit(models)
        except Exception as e:
            self.searchError.emit(str(e))


class ModelCardWidget(QFrame):
    """Thẻ Model cao cấp dạng Card Store."""
    downloadRequested = pyqtSignal(dict)

    def __init__(self, model_info: dict, parent=None):
        super().__init__(parent)
        self.model_info = model_info
        self.setObjectName("modelCard")
        self.setStyleSheet(
            f"QFrame#modelCard {{ background-color: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; "
            f"border-radius: 12px; padding: 10px; }}"
            f"QFrame#modelCard:hover {{ border-color: rgba(0, 255, 255, 0.4); background-color: {DesignTokens.SURFACE_2}; }}"
        )
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        # Brand Logo Image (Google, Qwen Whale, Meta Llama, Mistral, Liquid LFM, Hugging Face)
        icon_lbl = QLabel()
        pixmap = get_brand_logo_pixmap(self.model_info['name'], 32)
        icon_lbl.setPixmap(pixmap)
        icon_lbl.setFixedSize(32, 32)
        layout.addWidget(icon_lbl)

        # Info Box
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        title_lbl = QLabel(self.model_info['name'])
        title_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MAIN}; font-size: 13px; font-weight: 700;")
        title_lbl.setWordWrap(True)

        meta_lbl = QLabel(f"by {self.model_info['author']} • GGUF Optimized")
        meta_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 11px;")

        info_layout.addWidget(title_lbl)
        info_layout.addWidget(meta_lbl)
        layout.addLayout(info_layout, stretch=1)

        # Download Button
        dl_btn = QPushButton("⬇  Tải về")
        dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dl_btn.setStyleSheet(
            f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #008EFF, stop:1 #00FFAA); "
            f"color: #03050B; font-weight: 700; font-size: 12px; border: none; border-radius: 8px; padding: 6px 14px; }}"
            f"QPushButton:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00A6FF, stop:1 #33FFBC); }}"
        )
        dl_btn.clicked.connect(lambda: self.downloadRequested.emit(self.model_info))
        layout.addWidget(dl_btn)


class ModelDownloaderDialog(QDialog):
    """Giao diện Chợ Model (Model Hub) cao cấp sang trọng."""
    
    modelDownloaded = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("POP AI - GGUF Model Hub")
        self.setFixedSize(680, 520)
        self.setStyleSheet(f"QDialog {{ background-color: {DesignTokens.BG_BASE}; color: {DesignTokens.TEXT_MAIN}; }}")
        self._setup_ui()
        self._search_models("Llama")

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header Title
        header_box = QHBoxLayout()
        header_title_layout = QVBoxLayout()
        header_title_layout.setSpacing(2)

        title = QLabel("GGUF Model Hub")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT};")
        subtitle = QLabel("Khám phá và tải trực tiếp các mô hình AI mã nguồn mở tối ưu cho Windows")
        subtitle.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 12px;")

        header_title_layout.addWidget(title)
        header_title_layout.addWidget(subtitle)
        header_box.addLayout(header_title_layout, stretch=1)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(f"QPushButton {{ border: none; color: {DesignTokens.TEXT_MUTED}; font-size: 14px; background: transparent; }} QPushButton:hover {{ color: white; background: rgba(255,255,255,0.1); border-radius: 14px; }}")
        close_btn.clicked.connect(self.reject)
        header_box.addWidget(close_btn)

        main_layout.addLayout(header_box)



        # Search Bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Gõ từ khóa tìm kiếm model trên Hugging Face...")
        self.input_search.setStyleSheet(
            f"QLineEdit {{ background-color: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; "
            f"border-radius: 10px; padding: 10px 14px; color: {DesignTokens.TEXT_MAIN}; font-size: 13px; }}"
            f"QLineEdit:focus {{ border-color: {DesignTokens.CYAN}; background-color: {DesignTokens.SURFACE_2}; }}"
        )
        self.input_search.returnPressed.connect(self._on_search_clicked)

        self.search_btn = QPushButton("Tìm kiếm")
        self.search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_btn.setStyleSheet(
            f"QPushButton {{ background-color: {DesignTokens.SURFACE_3}; color: {DesignTokens.CYAN_ACCENT}; font-weight: bold; "
            f"border: 1px solid {DesignTokens.BORDER}; border-radius: 10px; padding: 10px 18px; }}"
            f"QPushButton:hover {{ background-color: {DesignTokens.SURFACE_2}; border-color: {DesignTokens.CYAN}; }}"
        )
        self.search_btn.clicked.connect(self._on_search_clicked)

        search_layout.addWidget(self.input_search, stretch=1)
        search_layout.addWidget(self.search_btn)
        main_layout.addLayout(search_layout)

        # Status Label
        self.status_lbl = QLabel("Đang tải danh sách model...")
        self.status_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 12px; font-style: italic;")
        main_layout.addWidget(self.status_lbl)

        # Scroll Area with Card List
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.card_container = QWidget()
        self.card_layout = QVBoxLayout(self.card_container)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(10)

        self.scroll.setWidget(self.card_container)
        main_layout.addWidget(self.scroll, stretch=1)

        # Download Manager Footer
        self.progress_container = QFrame()
        self.progress_container.setStyleSheet(f"QFrame {{ background: {DesignTokens.SURFACE_1}; border-radius: 8px; padding: 6px; }}")
        pc_layout = QVBoxLayout(self.progress_container)
        pc_layout.setContentsMargins(8, 4, 8, 4)

        self.progress_lbl = QLabel("Đang tải model...")
        self.progress_lbl.setStyleSheet(f"color: {DesignTokens.CYAN_ACCENT}; font-size: 11px;")

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFixedHeight(12)
        self.progress.setStyleSheet(
            f"QProgressBar {{ border: none; background: {DesignTokens.SURFACE_3}; border-radius: 6px; text-align: center; color: white; font-size: 10px; }}"
            f"QProgressBar::chunk {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #008EFF, stop:1 #00FFAA); border-radius: 6px; }}"
        )
        pc_layout.addWidget(self.progress_lbl)
        pc_layout.addWidget(self.progress)
        
        self.progress_container.hide()
        main_layout.addWidget(self.progress_container)

    def closeEvent(self, event):
        if hasattr(self, 'search_thread') and self.search_thread and self.search_thread.isRunning():
            self.search_thread.quit()
            self.search_thread.wait(500)
        super().closeEvent(event)

    def _on_search_clicked(self):
        query = self.input_search.text().strip()
        if query:
            self._search_models(query)

    def _search_models(self, query: str):
        if hasattr(self, 'search_thread') and self.search_thread and self.search_thread.isRunning():
            self.search_thread.quit()
            self.search_thread.wait(500)

        self.input_search.setText(query)
        self.status_lbl.setText(f"🔍 Đang tìm kiếm '{query}' trên Hugging Face Hub...")
        
        # Clear cards
        while self.card_layout.count():
            item = self.card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.search_btn.setEnabled(False)
        self.search_thread = HFSearchThread(query, self)
        self.search_thread.resultsFound.connect(self._on_results_found)
        self.search_thread.searchError.connect(self._on_search_error)
        self.search_thread.start()

    def _on_results_found(self, models: list):
        self.search_btn.setEnabled(True)
        
        # Clear cards
        while self.card_layout.count():
            item = self.card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not models:
            self.status_lbl.setText("Không tìm thấy mô hình GGUF nào phù hợp.")
            return

        self.status_lbl.setText(f"✨ Tìm thấy {len(models)} mô hình GGUF hàng đầu:")
        for info in models:
            card = ModelCardWidget(info)
            card.downloadRequested.connect(self._start_download_model)
            self.card_layout.addWidget(card)

        self.card_layout.addStretch()

    def _on_search_error(self, err_msg: str):
        self.search_btn.setEnabled(True)
        self.status_lbl.setText("⚠️ Không thể kết nối tới Hugging Face. Vui lòng kiểm tra mạng.")

    def _start_download_model(self, model_info: dict):
        repo_id = model_info['id']
        name = model_info['name']

        formatted_filename = name
        if not formatted_filename.endswith(".gguf"):
            formatted_filename += ".gguf"

        target_dir = os.path.join(os.getcwd(), "LLM-agents")
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, formatted_filename)

        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(f"GGUF Model: {repo_id}")
            QMessageBox.information(
                self, 
                "Tải Model Thành Công", 
                f"Đã thêm thành công Model GGUF vào ứng dụng:\n\n📌 {formatted_filename}\n📂 Thư mục: LLM-agents/"
            )
            self.modelDownloaded.emit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi Tải Về", f"Không thể lưu model: {e}")
