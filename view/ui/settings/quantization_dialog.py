import os
import json
import urllib.request
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGraphicsDropShadowEffect, QWidget
)
from PyQt6.QtGui import QColor

from view.ui.styles import DesignTokens
from view.ui.icons import get_brand_logo_pixmap


def get_system_hardware_info() -> dict:
    """Đọc thông tin cấu hình phần cứng: RAM và Card đồ họa (Card rời NVIDIA hoặc Card Onboard)."""
    import psutil
    mem = psutil.virtual_memory()
    total_ram_gb = mem.total / (1024 ** 3)
    avail_ram_gb = mem.available / (1024 ** 3)
    
    gpu_info = {
        "has_discrete_gpu": False,
        "gpu_name": "Card Onboard (Intel / AMD)",
        "vram_gb": 0.0
    }
    
    # 1. Kiểm tra card NVIDIA qua pynvml
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        gpu_name = pynvml.nvmlDeviceGetName(handle)
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        gpu_info["has_discrete_gpu"] = True
        gpu_info["gpu_name"] = str(gpu_name)
        gpu_info["vram_gb"] = mem_info.total / (1024 ** 3)
    except Exception:
        # 2. Fallback WMI để lấy tên Card đồ họa Onboard
        try:
            import wmi
            w = wmi.WMI()
            controllers = [g.Name for g in w.Win32_VideoController() if g.Name]
            if controllers:
                gpu_info["gpu_name"] = controllers[0]
        except Exception:
            pass

    return {
        "total_ram_gb": total_ram_gb,
        "avail_ram_gb": avail_ram_gb,
        "gpu": gpu_info
    }


def evaluate_compatibility(size_mb: float, hw: dict) -> dict:
    """Đánh giá mức độ mượt mà hoặc nguy cơ quá tải RAM của từng gói Quantization."""
    req_ram_gb = (size_mb / 1024.0) + 1.2
    avail_ram = hw["avail_ram_gb"]
    has_gpu = hw["gpu"]["has_discrete_gpu"]
    vram_gb = hw["gpu"]["vram_gb"]

    if has_gpu and (size_mb / 1024.0) <= (vram_gb * 0.85):
        return {
            "status": "smooth_gpu",
            "badge": "✓ CỰC MƯỢT (GPU VRAM)",
            "desc": f"Tối ưu hoàn hảo cho card rời {hw['gpu']['gpu_name']} • Tốc độ phản hồi tức thì",
            "color": "#00FFAA",
            "bg": "rgba(0, 255, 170, 0.12)",
            "border": "#00FFAA",
            "is_recommended": True,
            "priority": 1
        }
    elif req_ram_gb <= (avail_ram * 0.6):
        return {
            "status": "smooth_ram",
            "badge": "✓ RẤT MƯỢT (Khuyên Dùng)",
            "desc": f"RAM trống dư dả ({avail_ram:.1f} GB trống) • Chạy ổn định & phản hồi nhanh",
            "color": "#00FFAA",
            "bg": "rgba(0, 255, 170, 0.10)",
            "border": "#00FFAA",
            "is_recommended": True,
            "priority": 2
        }
    elif req_ram_gb <= (avail_ram * 0.85):
        return {
            "status": "fit",
            "badge": "⚠️ VỪA ĐỦ (Cân Nhắc RAM)",
            "desc": f"Vừa vặn dung lượng RAM trống ({avail_ram:.1f} GB) • Nên đóng bớt các ứng dụng nặng",
            "color": "#FFCC00",
            "bg": "rgba(255, 204, 0, 0.10)",
            "border": "#FFCC00",
            "is_recommended": False,
            "priority": 3
        }
    else:
        return {
            "status": "heavy",
            "badge": "✕ QUÁ TẢI (Dễ Tràn RAM / OOM)",
            "desc": f"Cần ~{req_ram_gb:.1f} GB RAM (Máy chỉ còn {avail_ram:.1f} GB trống) • Dễ giật lag hoặc tràn bộ nhớ",
            "color": "#FF4B6E",
            "bg": "rgba(255, 75, 110, 0.12)",
            "border": "#FF4B6E",
            "is_recommended": False,
            "priority": 4
        }


class HFVariantFetchThread(QThread):
    """Luồng tải danh sách các file GGUF và dung lượng thực tế từ Hugging Face tree API."""
    variantsFound = pyqtSignal(list)
    fetchError = pyqtSignal(str)

    def __init__(self, repo_id: str, hw_specs: dict, parent=None):
        super().__init__(parent)
        self.repo_id = repo_id
        self.hw_specs = hw_specs

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

                    eval_res = evaluate_compatibility(size_mb, self.hw_specs)

                    variants.append({
                        "filename": filename,
                        "size_mb": size_mb,
                        "eval": eval_res
                    })

            # Sắp xếp danh sách: Ưu tiên các gói Mượt mà/Vừa đủ lên đầu
            variants.sort(key=lambda x: (x["eval"]["priority"], -x["size_mb"]))
            self.variantsFound.emit(variants)

        except Exception as e:
            self.fetchError.emit(str(e))


class QuantizationDialog(QDialog):
    """Cửa sổ chọn phiên bản Quantization thông minh kèm đánh giá cấu hình phần cứng."""

    fileSelected = pyqtSignal(str)

    def __init__(self, repo_id: str, model_name: str, parent=None):
        super().__init__(parent)
        self.repo_id = repo_id
        self.model_name = model_name
        self.hw_specs = get_system_hardware_info()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(760, 560)

        self._setup_ui()
        self._load_variants()

    def _setup_ui(self):
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(12, 12, 12, 12)

        # Glassmorphic Dialog Container
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

        # 1. Header Bar
        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_brand_logo_pixmap(self.model_name, 34))
        header.addWidget(icon_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel("TÙY CHỌN QUANTIZATION & ĐÁNH GIÁ PHẦN CỨNG")
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {DesignTokens.CYAN_ACCENT}; letter-spacing: 0.5px;")
        
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

        # 2. Hardware Specs Card Banner
        hw_card = QFrame()
        hw_card.setStyleSheet(
            f"QFrame {{ background: rgba(14, 20, 36, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 10px; padding: 10px 14px; }}"
        )
        hw_layout = QHBoxLayout(hw_card)
        hw_layout.setContentsMargins(4, 2, 4, 2)
        hw_layout.setSpacing(16)

        ram_txt = f"🧠 <b>RAM:</b> {self.hw_specs['total_ram_gb']:.1f} GB (<font color='#00FFAA'>Còn trống: {self.hw_specs['avail_ram_gb']:.1f} GB</font>)"
        gpu_name = self.hw_specs['gpu']['gpu_name']
        if self.hw_specs['gpu']['has_discrete_gpu']:
            gpu_txt = f"🎮 <b>GPU:</b> {gpu_name} (<font color='#00FFAA'>{self.hw_specs['gpu']['vram_gb']:.1f} GB VRAM</font>)"
        else:
            gpu_txt = f"🖥️ <b>Đồ họa:</b> {gpu_name} <font color='#8A9EB5'>(Chạy trên RAM máy)</font>"

        lbl_ram = QLabel(ram_txt)
        lbl_ram.setStyleSheet("font-size: 12px; color: #FFFFFF;")
        
        lbl_gpu = QLabel(gpu_txt)
        lbl_gpu.setStyleSheet("font-size: 12px; color: #FFFFFF;")

        hw_layout.addWidget(lbl_ram)
        hw_layout.addWidget(lbl_gpu)
        hw_layout.addStretch()

        layout.addWidget(hw_card)

        # 3. Status / Loading Label
        self.status_lbl = QLabel("Đang phân tích và đối chiếu các phiên bản Quantization với phần cứng của bạn...")
        self.status_lbl.setStyleSheet(f"font-size: 12px; color: {DesignTokens.CYAN_ACCENT}; font-style: italic;")
        layout.addWidget(self.status_lbl)

        # 4. Scroll Area holding Quantization Options
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
        self.fetch_thread = HFVariantFetchThread(self.repo_id, self.hw_specs, parent=self)
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

        self.status_lbl.setText(f"Danh sách {len(variants)} phiên bản Quantization trên Hugging Face kèm đánh giá tương thích:")

        for v in variants:
            eval_info = v["eval"]
            row = QFrame()
            row.setStyleSheet(
                f"QFrame {{ background: {eval_info['bg']}; border: 1px solid {eval_info['border']}; "
                f"border-radius: 10px; padding: 10px 14px; }}"
            )

            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(12)

            info_box = QVBoxLayout()
            info_box.setSpacing(3)

            top_line = QHBoxLayout()
            top_line.setSpacing(8)

            fn_lbl = QLabel(v["filename"])
            fn_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {eval_info['color']};")

            badge_lbl = QLabel(eval_info["badge"])
            badge_lbl.setStyleSheet(
                f"background: rgba(0,0,0,0.35); color: {eval_info['color']}; font-size: 10px; font-weight: 700; "
                f"border-radius: 4px; padding: 2px 6px;"
            )

            top_line.addWidget(fn_lbl)
            top_line.addWidget(badge_lbl)
            top_line.addStretch()

            size_str = f"{v['size_mb'] / 1024:.2f} GB" if v['size_mb'] >= 1024 else f"{v['size_mb']:.1f} MB"
            sub_lbl = QLabel(f"<font color='#FFFFFF'>Dung lượng: <b>{size_str}</b></font> &nbsp;•&nbsp; <font color='#8A9EB5'>{eval_info['desc']}</font>")
            sub_lbl.setStyleSheet("font-size: 11px;")

            info_box.addLayout(top_line)
            info_box.addWidget(sub_lbl)
            rl.addLayout(info_box, stretch=1)

            dl_btn = QPushButton("⬇ Tải Bản Này")
            dl_btn.setFixedHeight(30)
            dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            if eval_info["is_recommended"]:
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
