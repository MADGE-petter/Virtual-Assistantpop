import os
from PyQt6.QtCore import Qt, pyqtSignal, QStringListModel
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QMessageBox, QCompleter,
    QProgressBar
)

from view.ui.styles import DesignTokens
from view.ui.icons import get_brand_logo_pixmap
from view.ui.settings.settings_config import HFSearchThread, HFModelDownloadThread
from view.ui.settings.quantization_dialog import QuantizationDialog


class DownloadTabWidget(QWidget):
    """Tab Tải & Tìm kiếm Model chuyên biệt từ Hugging Face với tính năng chọn phiên bản Quantization."""
    
    modelDownloaded = pyqtSignal()

    def __init__(self, user_settings: dict, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self.download_thread = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title = QLabel("Tìm Kiếm & Tải Model từ Hugging Face")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {DesignTokens.TEXT_MAIN}; letter-spacing: 0.5px;")
        desc = QLabel("Khám phá hàng ngàn mô hình AI GGUF trên Hugging Face Hub và tự do lựa chọn phiên bản Quantization (Q4, Q5, Q8...)")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        layout.addLayout(title_box)

        # Search Bar Box
        search_card = QFrame()
        search_card.setStyleSheet(
            f"QFrame {{ background: rgba(14, 20, 36, 0.65); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 12px; padding: 6px 10px; }}"
        )
        sb_layout = QHBoxLayout(search_card)
        sb_layout.setContentsMargins(4, 2, 4, 2)
        sb_layout.setSpacing(10)

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Nhập tên model (VD: Llama-3.2, Qwen2.5, Gemma-2, DeepSeek, Mistral...)...")
        self.input_search.setStyleSheet(
            f"QLineEdit {{ background: transparent; border: none; color: {DesignTokens.TEXT_MAIN}; font-size: 13px; padding: 6px 4px; }}"
        )
        self.input_search.textChanged.connect(self._on_search_text_changed)
        self.input_search.returnPressed.connect(self._on_search_models_clicked)

        # QCompleter setup
        self.completer_model = QStringListModel()
        self.completer = QCompleter(self.completer_model, self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.activated.connect(self._on_completer_activated)
        self.input_search.setCompleter(self.completer)

        self.btn_search = QPushButton("Tìm Kiếm")
        self.btn_search.setFixedHeight(34)
        self.btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_search.setStyleSheet(
            f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #008EFF, stop:1 #00FFAA); "
            f"color: #03050B; font-weight: bold; font-size: 12px; border: none; border-radius: 8px; padding: 0 18px; }}"
            f"QPushButton:hover {{ background: #00FFAA; }}"
        )
        self.btn_search.clicked.connect(self._on_search_models_clicked)

        sb_layout.addWidget(self.input_search, stretch=1)
        sb_layout.addWidget(self.btn_search)
        layout.addWidget(search_card)

        # Download Progress Card (Hidden by default, shown during download)
        self.progress_frame = QFrame()
        self.progress_frame.setStyleSheet(
            f"QFrame {{ background: rgba(0, 255, 170, 0.06); border: 1px solid {DesignTokens.CYAN_ACCENT}; "
            f"border-radius: 12px; padding: 14px 18px; }}"
        )
        self.progress_frame.hide()
        pf_layout = QVBoxLayout(self.progress_frame)
        pf_layout.setContentsMargins(0, 0, 0, 0)
        pf_layout.setSpacing(8)

        self.dl_title_lbl = QLabel("Đang chuẩn bị tải...")
        self.dl_title_lbl.setStyleSheet(f"font-weight: 700; font-size: 13px; color: {DesignTokens.CYAN_ACCENT};")

        self.dl_progress_bar = QProgressBar()
        self.dl_progress_bar.setFixedHeight(10)
        self.dl_progress_bar.setStyleSheet(
            f"QProgressBar {{ background: {DesignTokens.SURFACE_2}; border: none; border-radius: 5px; text-align: center; }}"
            f"QProgressBar::chunk {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #008EFF, stop:1 #00FFAA); border-radius: 5px; }}"
        )
        self.dl_progress_bar.setValue(0)
        self.dl_progress_bar.setTextVisible(False)

        pf_bottom = QHBoxLayout()
        self.dl_info_lbl = QLabel("Đang kết nối đến Hugging Face Resolve...")
        self.dl_info_lbl.setStyleSheet(f"font-size: 12px; color: {DesignTokens.TEXT_MUTED};")

        self.dl_cancel_btn = QPushButton("Hủy Tải")
        self.dl_cancel_btn.setFixedHeight(26)
        self.dl_cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dl_cancel_btn.setStyleSheet(
            f"QPushButton {{ background: rgba(255, 75, 110, 0.15); color: #FF4B6E; border: 1px solid rgba(255, 75, 110, 0.4); "
            f"border-radius: 6px; padding: 0 12px; font-size: 11px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: rgba(255, 75, 110, 0.3); border-color: #FF4B6E; }}"
        )
        self.dl_cancel_btn.clicked.connect(self._cancel_download)

        pf_bottom.addWidget(self.dl_info_lbl, stretch=1)
        pf_bottom.addWidget(self.dl_cancel_btn)

        pf_layout.addWidget(self.dl_title_lbl)
        pf_layout.addWidget(self.dl_progress_bar)
        pf_layout.addLayout(pf_bottom)

        layout.addWidget(self.progress_frame)

        # Search Results Status Label
        self.status_lbl = QLabel("Nhập từ khóa phía trên để bắt đầu tìm kiếm mô hình...")
        self.status_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {DesignTokens.TEXT_MUTED}; margin-top: 4px;")
        layout.addWidget(self.status_lbl)

        # Scroll Area for Search Results
        self.scroll_models = QScrollArea()
        self.scroll_models.setWidgetResizable(True)
        self.scroll_models.setFrameShape(QFrame.Shape.NoFrame)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)

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
        self.status_lbl.setText(f"🔍 Đang tìm kiếm '{query}' trên Hugging Face Hub...")
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.search_thread = HFSearchThread(query, is_suggest=False, parent=self)
        self.search_thread.resultsFound.connect(self._on_search_results_found)
        self.search_thread.searchError.connect(lambda err: self.status_lbl.setText(f"Lỗi tìm kiếm: {err}"))
        self.search_thread.start()

    def _on_search_results_found(self, models: list):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not models:
            self.status_lbl.setText("Không tìm thấy model GGUF nào phù hợp.")
            return

        self.status_lbl.setText(f"Tìm thấy {len(models)} mô hình GGUF khả dụng trên Hugging Face:")
        for m in models:
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
            icon_lbl.setPixmap(get_brand_logo_pixmap(m["name"], 34))
            cl.addWidget(icon_lbl)

            info_box = QVBoxLayout()
            info_box.setSpacing(3)

            name_lbl = QLabel(m["name"])
            name_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {DesignTokens.TEXT_MAIN};")

            sub_lbl = QLabel(f"<font color='#00FFAA'>● Tác giả: {m['author']}</font> &nbsp;•&nbsp; <font color='#8A9EB5'>Định dạng GGUF Đa Quantization</font>")
            sub_lbl.setStyleSheet("font-size: 11px;")

            info_box.addWidget(name_lbl)
            info_box.addWidget(sub_lbl)
            cl.addLayout(info_box, stretch=1)

            dl_btn = QPushButton("⬇ Chọn Quant & Tải")
            dl_btn.setFixedHeight(30)
            dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            dl_btn.setStyleSheet(
                f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #008EFF, stop:1 #00FFAA); "
                f"color: #03050B; font-weight: bold; border: none; border-radius: 6px; padding: 0 14px; font-size: 11px; }}"
                f"QPushButton:hover {{ background: #00FFAA; }}"
            )
            dl_btn.clicked.connect(lambda _, repo=m['id'], name=m['name']: self._open_quantization_selector(repo, name))
            cl.addWidget(dl_btn)

            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def _open_quantization_selector(self, repo_id: str, model_name: str):
        dialog = QuantizationDialog(repo_id, model_name, parent=self)
        dialog.fileSelected.connect(lambda chosen_file: self._start_real_download(repo_id, model_name, chosen_file))
        dialog.exec()

    def _start_real_download(self, repo_id: str, model_name: str, chosen_file: str = None):
        if self.download_thread and self.download_thread.isRunning():
            QMessageBox.warning(self, "Đang tải", "Một mô hình khác đang được tải về. Vui lòng chờ hoàn tất hoặc bấm Hủy tải.")
            return

        target_dir = self.user_settings.get("model_dir", os.path.join(os.getcwd(), "LLM-agents"))
        self.progress_frame.show()
        display_name = chosen_file if chosen_file else model_name
        self.dl_title_lbl.setText(f"Đang tải: {display_name}...")
        self.dl_progress_bar.setValue(0)
        self.dl_info_lbl.setText("Đang kết nối đến Hugging Face Resolve CDN...")
        self.btn_search.setEnabled(False)

        self.download_thread = HFModelDownloadThread(repo_id, target_dir, preferred_file=chosen_file, parent=self)
        self.download_thread.statusUpdated.connect(lambda status: self.dl_info_lbl.setText(status))
        self.download_thread.progressChanged.connect(self._on_download_progress)
        self.download_thread.downloadFinished.connect(self._on_download_finished)
        self.download_thread.downloadError.connect(self._on_download_error)
        self.download_thread.start()

    def _on_download_progress(self, percent: int, downloaded_mb: float, total_mb: float, speed_mb_s: float):
        self.dl_progress_bar.setValue(percent)
        if total_mb > 0:
            self.dl_info_lbl.setText(
                f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB ({percent}%) • Tốc độ: {speed_mb_s:.2f} MB/s"
            )
        else:
            self.dl_info_lbl.setText(f"Đã tải {downloaded_mb:.1f} MB • Tốc độ: {speed_mb_s:.2f} MB/s")

    def _on_download_finished(self, saved_path: str):
        self.btn_search.setEnabled(True)
        self.progress_frame.hide()
        QMessageBox.information(
            self,
            "Tải Thành Công",
            f"Đã tải thành công phiên bản mô hình GGUF về máy:\n{saved_path}\n\nBạn có thể vào tab 'Quản lý Models' để kiểm tra dung lượng và sử dụng ngay!"
        )
        self.modelDownloaded.emit()

    def _on_download_error(self, err_msg: str):
        self.btn_search.setEnabled(True)
        self.progress_frame.hide()
        QMessageBox.warning(self, "Thông Báo", err_msg)

    def _cancel_download(self):
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.cancel()
            self.dl_info_lbl.setText("Đang dừng tải...")
