from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QProgressBar, QMessageBox
)
import os

from view.ui.styles import DesignTokens

class ModelDownloaderDialog(QDialog):
    """Dialog to download GGUF models from Hugging Face."""
    
    modelDownloaded = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tải thêm Model GGUF")
        self.setFixedSize(450, 220)
        self.setStyleSheet(f"QDialog {{ background-color: {DesignTokens.BG_BASE}; color: {DesignTokens.TEXT_MAIN}; }}")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Tải Model GGUF từ Hugging Face")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT};")
        layout.addWidget(title)

        desc = QLabel("Nhập Repo ID hoặc Tên Model (VD: unsloth/Llama-3.2-3B-Instruct-GGUF):")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(desc)

        self.input_url = QLineEdit()
        self.input_url.setPlaceholderText("Hugging Face Repo ID...")
        self.input_url.setStyleSheet(
            f"QLineEdit {{ background-color: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; "
            f"border-radius: 8px; padding: 8px; color: {DesignTokens.TEXT_MAIN}; }}"
        )
        layout.addWidget(self.input_url)

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

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Hủy")
        self.cancel_btn.setStyleSheet(f"QPushButton {{ background: transparent; color: {DesignTokens.TEXT_MUTED}; border: none; padding: 6px 12px; }}")
        self.cancel_btn.clicked.connect(self.reject)

        self.download_btn = QPushButton("Tải về")
        self.download_btn.setStyleSheet(
            f"QPushButton {{ background-color: {DesignTokens.CYAN}; color: black; font-weight: bold; "
            f"border-radius: 8px; padding: 6px 16px; }}"
        )
        self.download_btn.clicked.connect(self._start_download)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.download_btn)
        
        layout.addLayout(btn_layout)

    def _start_download(self):
        repo_id = self.input_url.text().strip()
        if not repo_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Repo ID.")
            return

        self.input_url.setEnabled(False)
        self.download_btn.setEnabled(False)
        self.progress.show()

        # Giả lập quá trình tải model
        self._progress_val = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_progress)
        self._timer.start(50)
        
        # Save dummy file name based on input
        safe_name = repo_id.split("/")[-1] if "/" in repo_id else repo_id
        if not safe_name.endswith(".gguf"):
            safe_name += ".gguf"
        self._dummy_filename = safe_name

    def _update_progress(self):
        self._progress_val += 2
        self.progress.setValue(self._progress_val)
        if self._progress_val >= 100:
            self._timer.stop()
            self._finish_download()

    def _finish_download(self):
        # Tạo file ảo để test UI
        target_dir = os.path.join(os.getcwd(), "LLM-agents")
        os.makedirs(target_dir, exist_ok=True)
        with open(os.path.join(target_dir, self._dummy_filename), "w") as f:
            f.write("dummy model content")
            
        QMessageBox.information(self, "Thành công", f"Đã tải xong model: {self._dummy_filename}")
        self.modelDownloaded.emit()
        self.accept()
