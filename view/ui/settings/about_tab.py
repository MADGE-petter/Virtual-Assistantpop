import platform
import psutil
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QApplication
)
from view.ui.styles import DesignTokens


class AboutTabWidget(QWidget):
    """Tab 6: Thông Số Máy & Hệ Thống (About Me) thiết kế dạng Hardware Diagnostic Dashboard cao cấp."""

    def __init__(self, user_settings: dict, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        # Header Title Bar
        title_box = QVBoxLayout()
        title_box.setSpacing(6)

        title_row = QHBoxLayout()
        title = QLabel("Thông Số Máy Tính & Chẩn Đoán")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {DesignTokens.TEXT_MAIN}; letter-spacing: 0.5px;")

        badge = QLabel("DIAGNOSTICS")
        badge.setStyleSheet(
            f"background: rgba(0, 255, 170, 0.12); color: {DesignTokens.CYAN_ACCENT}; font-size: 11px; "
            f"font-weight: 700; border-radius: 4px; padding: 2px 8px; border: 1px solid rgba(0, 255, 170, 0.25);"
        )
        title_row.addWidget(title)
        title_row.addWidget(badge)
        title_row.addStretch()

        desc = QLabel("Thông số cấu hình phần cứng, card đồ họa và môi trường thực thi của máy tính")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 13px;")

        title_box.addLayout(title_row)
        title_box.addWidget(desc)
        layout.addLayout(title_box)

        # Retrieve Hardware Info Safely
        os_info = f"{platform.system()} {platform.release()} ({platform.architecture()[0]})"
        cpu_info = f"{platform.processor() or 'Intel / AMD Processor'} ({psutil.cpu_count(logical=True)} Threads)"
        
        ram_bytes = psutil.virtual_memory().total
        ram_gb = round(ram_bytes / (1024**3))
        ram_avail = round(psutil.virtual_memory().available / (1024**3), 1)
        ram_info = f"{ram_gb} GB RAM (Khả dụng: {ram_avail} GB)"

        try:
            disk = psutil.disk_usage('C:\\') if platform.system() == "Windows" else psutil.disk_usage('/')
            disk_total = round(disk.total / (1024**3))
            disk_free = round(disk.free / (1024**3))
            disk_info = f"{disk_free} GB trống / {disk_total} GB (Ổ đĩa C:)"
        except Exception:
            disk_info = "Không thể đọc dữ liệu ổ đĩa"

        gpu_info = "Intel / AMD Graphics"
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            gpu_name = pynvml.nvmlDeviceGetName(handle)
            if isinstance(gpu_name, bytes):
                gpu_name = gpu_name.decode('utf-8')
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            vram_gb = round(mem.total / (1024**3), 1)
            gpu_info = f"{gpu_name} ({vram_gb} GB VRAM)"
        except Exception:
            pass

        screen = QApplication.primaryScreen()
        res_str = f"{screen.geometry().width()} × {screen.geometry().height()} px ({screen.depth()} bit)" if screen else "1920 × 1080 px"

        # Hardware Grid (2 columns x 3 rows of rich cards with monochrome vector icons)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(14)

        specs = [
            ("monitor", "HỆ ĐIỀU HÀNH (OS)", os_info, "Kiến trúc x64 Windows Subsystem"),
            ("cpu", "BỘ VI XỬ LÝ (CPU)", cpu_info, "Hỗ trợ AVX2 & SIMD Acceleration"),
            ("ram", "BỘ NHỚ RAM", ram_info, "Băng thông kênh đôi High Speed"),
            ("gpu", "CARD ĐỒ HỌA (GPU)", gpu_info, "Gia tốc mô hình AI Offline"),
            ("disk", "Ổ ĐĨA HỆ THỐNG", disk_info, "Lưu trữ dữ liệu & tệp mô hình"),
            ("monitor", "MÀN HÌNH CHÍNH", res_str, "Mật độ điểm ảnh DPI chuẩn")
        ]

        for idx, (icon_type, label, value, sub) in enumerate(specs):
            card = self._create_spec_card(icon_type, label, value, sub)
            row = idx // 2
            col = idx % 2
            grid_layout.addWidget(card, row, col)

        layout.addLayout(grid_layout)

        layout.addStretch()

        # Enterprise App Info Card
        app_card = QFrame()
        app_card.setStyleSheet(
            f"QFrame {{ background: rgba(16, 22, 31, 0.6); border: 1px solid rgba(0, 255, 170, 0.2); "
            f"border-radius: 12px; padding: 14px 18px; }}"
        )
        ac_layout = QHBoxLayout(app_card)
        ac_layout.setContentsMargins(8, 2, 8, 2)
        ac_layout.setSpacing(16)

        logo_badge = QLabel("POP")
        logo_badge.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #008EFF, stop:1 #00FFAA); "
            f"color: #03050B; font-weight: 800; font-size: 14px; border-radius: 8px; padding: 6px 12px;"
        )
        ac_layout.addWidget(logo_badge)

        app_info = QVBoxLayout()
        app_info.setSpacing(2)
        app_title = QLabel("POP AI Assistant Pro — Enterprise Platform Edition")
        app_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {DesignTokens.TEXT_MAIN};")
        app_sub = QLabel("Phiên bản v2.5 • Động cơ GGUF LlamaCPP & WebRTC Engine • Tối ưu hóa cho Windows x64")
        app_sub.setStyleSheet(f"font-size: 12px; color: {DesignTokens.TEXT_MUTED};")
        app_info.addWidget(app_title)
        app_info.addWidget(app_sub)

        ac_layout.addLayout(app_info, stretch=1)
        layout.addWidget(app_card)

    def _create_spec_card(self, icon_type: str, label: str, value: str, sub: str) -> QFrame:
        from view.ui.icons import get_vector_pixmap
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: rgba(16, 22, 31, 0.75); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 12px; padding: 14px 16px; }}"
            f"QFrame:hover {{ border-color: rgba(0, 255, 255, 0.35); background: rgba(21, 28, 39, 0.85); }}"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(6, 4, 6, 4)
        card_layout.setSpacing(6)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_vector_pixmap(icon_type, "#E6F4FF", 18))

        lbl = QLabel(label)
        lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {DesignTokens.TEXT_MUTED}; letter-spacing: 0.5px;")

        header_row.addWidget(icon_lbl)
        header_row.addWidget(lbl)
        header_row.addStretch()

        val = QLabel(value)
        val.setWordWrap(True)
        val.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {DesignTokens.TEXT_MAIN};")

        sub_lbl = QLabel(sub)
        sub_lbl.setStyleSheet(f"font-size: 11px; color: {DesignTokens.TEXT_SECONDARY};")

        card_layout.addLayout(header_row)
        card_layout.addWidget(val)
        card_layout.addWidget(sub_lbl)
        return card

    def update_system_telemetry(self):
        pass
