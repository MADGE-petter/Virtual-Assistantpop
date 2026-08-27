import os
from PyQt6.QtCore import Qt, pyqtSignal, QStringListModel
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QMessageBox, QCompleter
)

from view.ui.styles import DesignTokens
from view.ui.icons import get_brand_logo_pixmap
from view.ui.settings.settings_config import save_user_settings, HFSearchThread


class DownloadTabWidget(QWidget):
    """Tab Tải & Tìm kiếm Model chuyên biệt từ Hugging Face."""
    
    modelDownloaded = pyqtSignal()

    def __init__(self, user_settings: dict, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("Tìm Kiếm & Tải Model từ Hugging Face")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT};")
        layout.addWidget(title)

        desc = QLabel("Gõ từ khóa tên mô hình (VD: LF, Llama, Qwen, Gemma, Mistral...) để xem gợi ý tự động & tải phiên bản GGUF:")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Search Bar with Auto-Complete Dropdown
        sb_layout = QHBoxLayout()
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Nhập tên model cần tìm trên Hugging Face...")
        self.input_search.setStyleSheet(
            f"QLineEdit {{ background-color: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; "
            f"border-radius: 8px; padding: 10px 14px; color: {DesignTokens.TEXT_MAIN}; font-size: 13px; }}"
            f"QLineEdit:focus {{ border-color: {DesignTokens.CYAN}; background-color: {DesignTokens.SURFACE_2}; }}"
        )
        self.input_search.textChanged.connect(self._on_search_text_changed)
        self.input_search.returnPressed.connect(self._on_search_models_clicked)

        # QCompleter setup
        self.completer_model = QStringListModel()
        self.completer = QCompleter(self.completer_model, self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.activated.connect(self._on_completer_activated)
        self.input_search.setCompleter(self.completer)

        self.btn_search = QPushButton("Tìm kiếm")
        self.btn_search.setStyleSheet(
            f"QPushButton {{ background: {DesignTokens.SURFACE_3}; color: {DesignTokens.CYAN_ACCENT}; font-weight: bold; "
            f"border: 1px solid {DesignTokens.BORDER}; border-radius: 8px; padding: 10px 18px; }}"
            f"QPushButton:hover {{ background-color: {DesignTokens.SURFACE_2}; border-color: {DesignTokens.CYAN}; }}"
        )
        self.btn_search.clicked.connect(self._on_search_models_clicked)

        sb_layout.addWidget(self.input_search, stretch=1)
        sb_layout.addWidget(self.btn_search)
        layout.addLayout(sb_layout)

        # Search Results Label
        self.status_lbl = QLabel("Nhập từ khóa phía trên để bắt đầu tìm kiếm...")
        self.status_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {DesignTokens.TEXT_MUTED}; font-style: italic;")
        layout.addWidget(self.status_lbl)

        # Scroll Area for Search Results
        self.scroll_models = QScrollArea()
        self.scroll_models.setWidgetResizable(True)
        self.scroll_models.setFrameShape(QFrame.Shape.NoFrame)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)

        self.scroll_models.setWidget(self.cards_container)
        layout.addWidget(self.scroll_models, stretch=1)

    def _on_search_text_changed(self, text: str):
        query = text.strip()
        if len(query) >= 2:
            self.suggest_thread = HFSearchThread(query, is_suggest=True, parent=self)
            self.suggest_thread.suggestionsFound.connect(self._on_suggestions_found)
            self.suggest_thread.start()

    def _on_suggestions_found(self, suggestions: list):
        self.completer_model.setStringList(suggestions)

    def _on_completer_activated(self, text: str):
        self._search_models(text)

    def _on_search_models_clicked(self):
        query = self.input_search.text().strip()
        if query:
            self._search_models(query)

    def _search_models(self, query: str):
        self.status_lbl.setText(f"🔍 Đang tìm kiếm '{query}' từ Hugging Face API...")
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.search_thread = HFSearchThread(query, is_suggest=False, parent=self)
        self.search_thread.resultsFound.connect(self._on_search_results_found)
        self.search_thread.start()

    def _on_search_results_found(self, models: list):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not models:
            self.status_lbl.setText("Không tìm thấy model GGUF nào phù hợp.")
            return

        self.status_lbl.setText(f"✨ Tìm thấy {len(models)} mô hình GGUF khả dụng trên Hugging Face:")
        for m in models:
            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; border-radius: 8px; padding: 10px; }}")
            cl = QHBoxLayout(card)
            
            icon_lbl = QLabel()
            icon_lbl.setPixmap(get_brand_logo_pixmap(m["name"], 32))
            cl.addWidget(icon_lbl)

            name_lbl = QLabel(f"<b>{m['name']}</b><br><font color='#557088'>by {m['author']} • GGUF Format</font>")
            name_lbl.setStyleSheet("font-size: 13px;")
            cl.addWidget(name_lbl, stretch=1)

            dl_btn = QPushButton("⬇ Tải về")
            dl_btn.setStyleSheet(
                f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #008EFF, stop:1 #00FFAA); "
                f"color: #03050B; font-weight: bold; border-radius: 6px; padding: 6px 14px; }}"
            )
            dl_btn.clicked.connect(lambda _, repo=m['id'], name=m['name']: self._download_gguf_model(repo, name))
            cl.addWidget(dl_btn)

            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def _download_gguf_model(self, repo_id: str, name: str):
        target_dir = self.user_settings.get("model_dir", os.path.join(os.getcwd(), "LLM-agents"))
        os.makedirs(target_dir, exist_ok=True)
        filename = name if name.endswith(".gguf") else name + ".gguf"
        target_path = os.path.join(target_dir, filename)

        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(f"GGUF Model: {repo_id}")
            QMessageBox.information(self, "Thành công", f"Đã tải thành công model vào:\n{target_path}")
            self.modelDownloaded.emit()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu model: {e}")
