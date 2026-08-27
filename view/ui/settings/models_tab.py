import os
from PyQt6.QtCore import Qt, pyqtSignal, QStringListModel
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QMessageBox, QFileDialog, QCompleter
)

from view.ui.styles import DesignTokens
from view.ui.icons import get_brand_logo_pixmap
from view.ui.settings.settings_config import save_user_settings, HFSearchThread


class ModelsTabWidget(QWidget):
    """Tab 2: Quản lý LLM Models & Hugging Face Hub."""
    
    modelDownloaded = pyqtSignal()

    def __init__(self, user_settings: dict, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("Quản Lý LLM Models & Hugging Face Hub")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT};")
        layout.addWidget(title)

        # Custom Directory Settings Section
        dir_frame = QFrame()
        dir_frame.setStyleSheet(f"QFrame {{ background: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; border-radius: 10px; padding: 10px; }}")
        df_layout = QHBoxLayout(dir_frame)
        df_layout.setContentsMargins(10, 6, 10, 6)

        dir_lbl = QLabel("Thư mục lưu Models:")
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

        # Search Bar with Auto-Complete Dropdown
        search_box = QVBoxLayout()
        search_box.setSpacing(4)
        
        sb_label = QLabel("Tìm kiếm & Tải Model GGUF từ Hugging Face (Có gợi ý tự động):")
        sb_label.setStyleSheet(f"font-size: 12px; color: {DesignTokens.TEXT_MUTED};")
        search_box.addWidget(sb_label)

        sb_layout = QHBoxLayout()
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Gõ từ khóa (VD: LF, Llama, Qwen, Gemma, Mistral)...")
        self.input_search.setStyleSheet(
            f"QLineEdit {{ background-color: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; "
            f"border-radius: 8px; padding: 8px 12px; color: {DesignTokens.TEXT_MAIN}; font-size: 13px; }}"
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
        self.btn_search.setStyleSheet(f"QPushButton {{ background: {DesignTokens.SURFACE_3}; color: {DesignTokens.CYAN_ACCENT}; font-weight: bold; border-radius: 8px; padding: 8px 16px; }}")
        self.btn_search.clicked.connect(self._on_search_models_clicked)

        sb_layout.addWidget(self.input_search, stretch=1)
        sb_layout.addWidget(self.btn_search)
        search_box.addLayout(sb_layout)

        layout.addLayout(search_box)

        # Local Installed Models / Search Results Label
        self.models_list_lbl = QLabel("Danh sách Model đã cài đặt & Kết quả tìm kiếm:")
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

    def _change_model_directory(self):
        new_dir = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu trữ Models", self.txt_model_dir.text())
        if new_dir:
            self.txt_model_dir.setText(new_dir)
            self.user_settings["model_dir"] = new_dir
            save_user_settings(self.user_settings)
            self.reload_local_models()
            QMessageBox.information(self, "Thành công", f"Đã đổi thư mục lưu model thành:\n{new_dir}")

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
        else:
            self.reload_local_models()

    def _search_models(self, query: str):
        self.models_list_lbl.setText(f"🔍 Kết quả tìm kiếm '{query}' từ Hugging Face:")
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
            self.models_list_lbl.setText("Không tìm thấy model GGUF nào phù hợp.")
            return

        for m in models:
            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; border-radius: 8px; padding: 8px; }}")
            cl = QHBoxLayout(card)
            
            icon_lbl = QLabel()
            icon_lbl.setPixmap(get_brand_logo_pixmap(m["name"], 28))
            cl.addWidget(icon_lbl)

            name_lbl = QLabel(f"<b>{m['name']}</b><br><font color='#557088'>by {m['author']}</font>")
            name_lbl.setStyleSheet("font-size: 12px;")
            cl.addWidget(name_lbl, stretch=1)

            dl_btn = QPushButton("⬇ Tải về")
            dl_btn.setStyleSheet(f"QPushButton {{ background: {DesignTokens.CYAN}; color: black; font-weight: bold; border-radius: 6px; padding: 6px 12px; }}")
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
            self.reload_local_models()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu model: {e}")

    def reload_local_models(self):
        self.models_list_lbl.setText("📦 Các Model đã cài đặt cục bộ:")
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        target_dir = self.user_settings.get("model_dir", os.path.join(os.getcwd(), "LLM-agents"))
        if not os.path.exists(target_dir) or not os.listdir(target_dir):
            no_lbl = QLabel("Chưa có model nào trong thư mục. Hãy gõ từ khóa ở trên để tìm & tải model!")
            no_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-style: italic;")
            self.cards_layout.addWidget(no_lbl)
            self.cards_layout.addStretch()
            return

        for item in os.listdir(target_dir):
            if item.startswith('.'): continue
            full_p = os.path.join(target_dir, item)
            size_mb = os.path.getsize(full_p) / (1024 * 1024) if os.path.isfile(full_p) else 0

            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; border-radius: 8px; padding: 8px; }}")
            cl = QHBoxLayout(card)

            icon_lbl = QLabel()
            icon_lbl.setPixmap(get_brand_logo_pixmap(item, 28))
            cl.addWidget(icon_lbl)

            info_lbl = QLabel(f"<b>{item}</b><br><font color='#557088'>Dung lượng: {size_mb:.1f} MB • Local GGUF</font>")
            info_lbl.setStyleSheet("font-size: 12px;")
            cl.addWidget(info_lbl, stretch=1)

            del_btn = QPushButton("🗑️ Xóa")
            del_btn.setStyleSheet(f"QPushButton {{ background: rgba(255, 75, 110, 0.2); color: #FF4B6E; border: 1px solid #FF4B6E; border-radius: 6px; padding: 4px 10px; }}")
            del_btn.clicked.connect(lambda _, path=full_p: self._delete_local_model(path))
            cl.addWidget(del_btn)

            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def _delete_local_model(self, path: str):
        if QMessageBox.question(self, "Xác nhận", f"Bạn có chắc muốn xóa model này?\n{os.path.basename(path)}") == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isfile(path): os.remove(path)
                elif os.path.isdir(path): import shutil; shutil.rmtree(path)
                self.reload_local_models()
                self.modelDownloaded.emit()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể xóa model: {e}")
