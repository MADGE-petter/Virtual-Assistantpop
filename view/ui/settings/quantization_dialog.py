import os
import json
import re
import urllib.request
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QWidget
)

from view.ui.styles import DesignTokens
from view.ui.icons import get_brand_logo_pixmap, create_vector_icon, get_vector_pixmap


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
        import warnings
        warnings.filterwarnings('ignore', message=r'.*pynvml.*')
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
            "badge": "[GPU VRAM] CỰC MƯỢT",
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
            "badge": "[KHUYÊN DÙNG] RẤT MƯỢT",
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
            "badge": "[CÂN NHẮC] VỪA ĐỦ",
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
            "badge": "[CẢNH BÁO] QUÁ TẢI",
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

        self.setWindowTitle("Chọn phiên bản model")
        self.setFixedSize(760, 560)

        self._setup_ui()
        self._load_variants()

    def _setup_ui(self):
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)

        self.container = QFrame()
        self.container.setObjectName("variantDialog")
        self.container.setStyleSheet(
            f"QFrame#variantDialog {{ background: {DesignTokens.BG_BASE}; "
            f"border: 1px solid {DesignTokens.BORDER}; border-radius: 3px; }}"
        )

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        # 1. Header Bar
        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_brand_logo_pixmap(self.model_name, 34))
        header.addWidget(icon_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel("Chọn phiên bản model")
        title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 650; color: {DesignTokens.TEXT_MAIN};")
        
        repo_lbl = QLabel(self.repo_id)
        repo_lbl.setStyleSheet(f"font-size: 11px; color: {DesignTokens.TEXT_MUTED};")
        
        title_box.addWidget(title_lbl)
        title_box.addWidget(repo_lbl)
        header.addLayout(title_box, stretch=1)

        close_btn = QPushButton()
        close_btn.setIcon(create_vector_icon("close", "#8A9EB5", 14))
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: 1px solid transparent; border-radius: 3px; }}"
            f"QPushButton:hover {{ background-color: {DesignTokens.SURFACE_2}; border-color: {DesignTokens.BORDER}; }}"
        )
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)

        layout.addLayout(header)

        # 2. Hardware Specs Card Banner
        hw_card = QFrame()
        hw_card.setStyleSheet(
            f"QFrame {{ background: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; "
            f"border-radius: 3px; padding: 8px 12px; }}"
        )
        hw_layout = QHBoxLayout(hw_card)
        hw_layout.setContentsMargins(4, 2, 4, 2)
        hw_layout.setSpacing(16)

        ram_txt = f"<b>RAM:</b> {self.hw_specs['total_ram_gb']:.1f} GB (<font color='#00FFAA'>Còn trống: {self.hw_specs['avail_ram_gb']:.1f} GB</font>)"
        gpu_name = self.hw_specs['gpu']['gpu_name']
        if self.hw_specs['gpu']['has_discrete_gpu']:
            gpu_txt = f"<b>GPU:</b> {gpu_name} (<font color='#00FFAA'>{self.hw_specs['gpu']['vram_gb']:.1f} GB VRAM</font>)"
        else:
            gpu_txt = f"<b>Đồ họa:</b> {gpu_name} <font color='#8A9EB5'>(Chạy trên RAM máy)</font>"

        ram_box = QHBoxLayout()
        ram_box.setSpacing(6)
        ram_ico = QLabel()
        ram_ico.setPixmap(get_vector_pixmap("ram", "#00FFAA", 16))
        lbl_ram = QLabel(ram_txt)
        lbl_ram.setStyleSheet("font-size: 12px; color: #FFFFFF;")
        ram_box.addWidget(ram_ico)
        ram_box.addWidget(lbl_ram)

        gpu_box = QHBoxLayout()
        gpu_box.setSpacing(6)
        gpu_ico = QLabel()
        gpu_ico.setPixmap(get_vector_pixmap("gpu", "#00FFAA", 16))
        lbl_gpu = QLabel(gpu_txt)
        lbl_gpu.setStyleSheet("font-size: 12px; color: #FFFFFF;")
        gpu_box.addWidget(gpu_ico)
        gpu_box.addWidget(lbl_gpu)

        hw_layout.addLayout(ram_box)
        hw_layout.addLayout(gpu_box)
        hw_layout.addStretch()

        layout.addWidget(hw_card)

        # 3. Status / Loading Label
        self.status_lbl = QLabel("Đang phân tích và đối chiếu các phiên bản Quantization với phần cứng của bạn...")
        self.status_lbl.setStyleSheet(f"font-size: 11px; color: {DesignTokens.TEXT_SECONDARY};")
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
            filename = os.path.basename(v["filename"])
            parameter_match = re.search(r"(?<![A-Za-z0-9])(\d+(?:\.\d+)?B)(?![A-Za-z0-9])", filename, re.IGNORECASE)
            quant_match = re.search(r"(?<![A-Za-z0-9])Q\d(?:_[A-Z0-9]+)*", filename, re.IGNORECASE)
            variant_title = " · ".join(
                value.upper() for value in (
                    parameter_match.group(1) if parameter_match else None,
                    quant_match.group(0) if quant_match else None,
                ) if value
            ) or filename

            row = QFrame()
            row.setStyleSheet(
                f"QFrame {{ background: {DesignTokens.SURFACE_1}; "
                f"border: 1px solid {DesignTokens.BORDER}; border-left: 3px solid {eval_info['color']}; "
                f"border-radius: 8px; padding: 10px 12px; }}"
            )

            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(12)

            info_box = QVBoxLayout()
            info_box.setSpacing(3)

            top_line = QHBoxLayout()
            top_line.setSpacing(8)

            fn_lbl = QLabel(variant_title)
            fn_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {DesignTokens.TEXT_MAIN};")

            status_labels = {
                "smooth_gpu": "GPU TỐI ƯU",
                "smooth_ram": "ĐỀ XUẤT",
                "fit": "VỪA ĐỦ",
                "heavy": "QUÁ TẢI",
            }
            badge_lbl = QLabel(status_labels.get(eval_info["status"], "TƯƠNG THÍCH"))
            badge_lbl.setStyleSheet(
                f"background: {DesignTokens.SURFACE_2}; color: {eval_info['color']}; font-size: 9px; font-weight: 700; "
                f"border: 1px solid {DesignTokens.BORDER}; border-radius: 4px; padding: 4px 7px;"
            )

            size_str = f"{v['size_mb'] / 1024:.2f} GB" if v['size_mb'] >= 1024 else f"{v['size_mb']:.1f} MB"
            size_lbl = QLabel(size_str)
            size_lbl.setStyleSheet(f"font-size: 11px; font-weight: 650; color: {DesignTokens.TEXT_SECONDARY};")

            top_line.addWidget(fn_lbl)
            top_line.addWidget(badge_lbl)
            top_line.addStretch()
            top_line.addWidget(size_lbl)

            file_lbl = QLabel(v["filename"])
            file_lbl.setStyleSheet(f"font-size: 10px; color: {DesignTokens.TEXT_MUTED};")
            file_lbl.setWordWrap(True)
            compatibility_lbl = QLabel(eval_info["desc"])
            compatibility_lbl.setStyleSheet(f"font-size: 10px; color: {DesignTokens.TEXT_SECONDARY};")
            compatibility_lbl.setWordWrap(True)

            info_box.addLayout(top_line)
            info_box.addWidget(file_lbl)
            info_box.addWidget(compatibility_lbl)
            rl.addLayout(info_box, stretch=1)

            dl_btn = QPushButton("Tải bản này")
            dl_btn.setIcon(create_vector_icon("download", DesignTokens.TEXT_MAIN, 14))
            dl_btn.setFixedHeight(34)
            dl_btn.setMinimumWidth(112)
            dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            dl_btn.setStyleSheet(
                f"QPushButton {{ background: {DesignTokens.SURFACE_2}; color: {DesignTokens.TEXT_MAIN}; font-weight: 650; "
                f"border: 1px solid #405366; border-radius: 5px; padding: 0 10px; font-size: 10px; }}"
                f"QPushButton:hover {{ background: #202D3A; border-color: {eval_info['color']}; }}"
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
