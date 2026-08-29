import os
import json
import urllib.request
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QProgressBar, QGraphicsDropShadowEffect, QWidget
)
from PyQt6.QtGui import QColor

from view.ui.styles import DesignTokens
from view.ui.icons import get_brand_logo_pixmap


class HFVariantFetchThread(QThread):
    """Luồng tải danh sách các file GGUF và dung lượng thực tế từ Hugging Face tree API."""
    variantsFound = pyqtSignal(list)
    fetchError = pyqtSignal(str)

    def __init__(self, repo_id: str, parent=None):
        super().__init__(parent)
        self.repo_id = repo_id

    def run(self):
        try:
            url = f"https://huggingface.co/api/models/{self.repo_id}/tree/main"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode('utf-8'))

            variants = []
            for item in data:
                if isinstance(item, dict) and item.get('path', '').endswith('.gguf'):
                    filename = item['path']
                    size_bytes = item.get('size', 0)
                    size_mb = size_bytes / (1024 * 1024) if size_bytes > 0 else 0.0

                    # Phân tích độ ưu tiên và nhãn lượng tử hóa
                    lower_f = filename.lower()
                    tag = "Chuẩn GGUF"
                    is_recommended = False
                    priority = 10

                    if "q4_k_m" in lower_f or "q4_k" in lower_f:
                        tag = "Khuyên dùng (Cân bằng RAM & Tốc độ)"
                        is_recommended = True
                        priority = 1
                    elif "q5_k_m" in lower_f or "q5_k" in lower_f:
                        tag = "Chất lượng cao (Độ chính xác tốt)"
                        priority = 2
                    elif "q8_0" in lower_f or "q8_k" in lower_f:
                        tag = "Chất lượng tối đa (Cần nhiều RAM)"
                        priority = 3
                    elif "q6_k" in lower_f:
                        tag = "Chất lượng rất cao"
                        priority = 4
                    elif "q4_0" in lower_f or "iq4" in lower_f:
                        tag = "Gọn nhẹ (4-bit tiêu chuẩn)"
                        priority = 5
                    elif "q3_k" in lower_f or "iq3" in lower_f:
                        tag = "Tiết kiệm RAM (Dành cho máy yếu)"
                        priority = 6
                    elif "q2" in lower_f or "iq2" in lower_f:
                        tag = "Siêu nhẹ (2-bit)"
                        priority = 7

                    variants.append({
                        "filename": filename,
                        "size_mb": size_mb,
                        "tag": tag,
                        "is_recommended": is_recommended,
                        "priority": priority
                    })

            # Sắp xếp danh sách (Ưu tiên Q4_K_M -> Q5 -> Q8 -> Q6 -> Q4 -> Q3 -> Q2)
            variants.sort(key=lambda x: (x["priority"], -x["size_mb"]))
            self.variantsFound.emit(variants)

        except Exception as e:
            self.fetchError.emit(str(e))


class QuantizationDialog(QDialog):
    """Cửa sổ chọn phiên bản Quantization (Q4_K_M, Q5, Q8, Q3...) trước khi tải."""

    fileSelected = pyqtSignal(str)

    def __init__(self, repo_id: str, model_name: str, parent=None):
        super().__init__(parent)
        self.repo_id = repo_id
        self.model_name = model_name

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(720, 520)

        self._setup_ui()
        self._load_variants()

    def _setup_ui(self):
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(12, 12, 12, 12)

        # Glassmorphic Dialog Box
        self.container = QFrame()
        self.container.setStyleSheet(
            f"QFrame {{"
            f"  background-color: rgba(10, 14, 26, 0.96);"
            f"  border: 1px solid rgba(0, 255, 170, 0.3);"
            f"  border-radius: 16px;"
            f"}}"
        )
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setColor(QColor(0, 255, 170, 50))
        shadow.setOffset(0, 6)
        self.container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Bar
        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_brand_logo_pixmap(self.model_name, 32))
        header.addWidget(icon_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel("CHỌN PHIÊN BẢN QUANTIZATION (GGUF)")
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT}; letter-spacing: 0.5px;")
        
        repo_lbl = QLabel(f"Repository: {self.repo_id}")
        repo_lbl.setStyleSheet(f"font-size: 12px; color: {DesignTokens.TEXT_MUTED};")
        
        title_box.addWidget(title_lbl)
        title_box.addWidget(repo_lbl)
        header.addLayout(title_box, stretch=1)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {DesignTokens.TEXT_MUTED}; font-size: 14px; border: none; border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: rgba(255, 75, 110, 0.25); color: #FF4B6E; }}"
        )
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)

        layout.addLayout(header)

        # Instruction Note
        guide_lbl = QLabel("💡 <b>Gợi ý:</b> Bản <b>Q4_K_M</b> là phiên bản tối ưu nhất giữa dung lượng và độ thông minh cho đa số máy tính.")
        guide_lbl.setStyleSheet(
            f"background: rgba(0, 255, 170, 0.08); border: 1px solid rgba(0, 255, 170, 0.2); "
            f"border-radius: 8px; padding: 8px 12px; font-size: 12px; color: {DesignTokens.TEXT_MAIN};"
        )
        layout.addWidget(guide_lbl)

        # Loading / Status Label
        self.status_lbl = QLabel("Đang tải danh sách các phiên bản Quantization từ Hugging Face...")
        self.status_lbl.setStyleSheet(f"font-size: 12px; color: {DesignTokens.CYAN_ACCENT}; font-style: italic;")
        layout.addWidget(self.status_lbl)

        # Scroll Area holding Quantization Options
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)

        self.scroll.setWidget(self.list_widget)
        layout.addWidget(self.scroll, stretch=1)

        base_layout.addWidget(self.container)

    def _load_variants(self):
        self.fetch_thread = HFVariantFetchThread(self.repo_id, parent=self)
        self.fetch_thread.variantsFound.connect(self._on_variants_loaded)
        self.fetch_thread.fetchError.connect(self._on_fetch_error)
        self.fetch_thread.start()

    def _on_variants_loaded(self, variants: list):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not variants:
            self.status_lbl.setText("Không tìm thấy file .gguf nào trong repository này.")
            return

        self.status_lbl.setText(f"Tìm thấy {len(variants)} phiên bản Quantization khả dụng:")

        for v in variants:
            row = QFrame()
            if v["is_recommended"]:
                row.setStyleSheet(
                    f"QFrame {{ background: rgba(0, 255, 170, 0.12); border: 1px solid {DesignTokens.CYAN_ACCENT}; "
                    f"border-radius: 10px; padding: 10px 14px; }}"
                )
            else:
                row.setStyleSheet(
                    f"QFrame {{ background: rgba(14, 20, 36, 0.65); border: 1px solid rgba(255, 255, 255, 0.08); "
                    f"border-radius: 10px; padding: 10px 14px; }}"
                    f"QFrame:hover {{ background: rgba(18, 26, 46, 0.85); border-color: rgba(0, 255, 170, 0.25); }}"
                )

            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(12)

            info_box = QVBoxLayout()
            info_box.setSpacing(3)

            fn_lbl = QLabel(v["filename"])
            fn_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {'#00FFAA' if v['is_recommended'] else DesignTokens.TEXT_MAIN};")

            size_str = f"{v['size_mb'] / 1024:.2f} GB" if v['size_mb'] >= 1024 else f"{v['size_mb']:.1f} MB"
            tag_color = "#00FFAA" if v['is_recommended'] else "#8A9EB5"
            sub_lbl = QLabel(f"<font color='{tag_color}'><b>{v['tag']}</b></font> &nbsp;•&nbsp; <font color='#8A9EB5'>Dung lượng: {size_str}</font>")
            sub_lbl.setStyleSheet("font-size: 11px;")

            info_box.addWidget(fn_lbl)
            info_box.addWidget(sub_lbl)
            rl.addLayout(info_box, stretch=1)

            dl_btn = QPushButton("⬇ Tải bản này")
            dl_btn.setFixedHeight(30)
            dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if v["is_recommended"]:
                dl_btn.setStyleSheet(
                    f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #008EFF, stop:1 #00FFAA); "
                    f"color: #03050B; font-weight: bold; border: none; border-radius: 6px; padding: 0 14px; font-size: 11px; }}"
                    f"QPushButton:hover {{ background: #00FFAA; }}"
                )
            else:
                dl_btn.setStyleSheet(
                    f"QPushButton {{ background: {DesignTokens.SURFACE_3}; color: {DesignTokens.TEXT_MAIN}; "
                    f"border: 1px solid {DesignTokens.BORDER}; border-radius: 6px; padding: 0 14px; font-size: 11px; font-weight: 600; }}"
                    f"QPushButton:hover {{ background: {DesignTokens.SURFACE_2}; border-color: {DesignTokens.CYAN}; color: {DesignTokens.CYAN_ACCENT}; }}"
                )
            dl_btn.clicked.connect(lambda _, f=v["filename"]: self._select_file(f))
            rl.addWidget(dl_btn)

            self.list_layout.addWidget(row)

        self.list_layout.addStretch()

    def _on_fetch_error(self, error_msg: str):
        self.status_lbl.setText(f"Lỗi khi lấy danh sách: {error_msg}")

    def _select_file(self, filename: str):
        self.fileSelected.emit(filename)
        self.accept()
