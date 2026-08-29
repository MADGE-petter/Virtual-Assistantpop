import psutil
import platform
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QApplication, QProgressBar
)
from view.ui.styles import DesignTokens


class AboutTabWidget(QWidget):
    """Tab 6: Thông Số Máy & Hệ Thống (About Me) thiết kế dạng Dashboard trực quan cao cấp."""

    def __init__(self, user_settings: dict, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title = QLabel("Thông Số Máy Tính (DxDiag Style)")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {DesignTokens.TEXT_MAIN}; letter-spacing: 0.5px;")
        desc = QLabel("Thông tin chi tiết về cấu hình phần cứng và hệ điều hành của máy")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        layout.addLayout(title_box)

        # List Container
        list_container = QFrame()
        list_container.setStyleSheet(
            f"QFrame {{ background: rgba(14, 20, 36, 0.65); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 12px; padding: 4px; }}"
        )
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(20, 20, 20, 20)
        list_layout.setSpacing(14)

        # Retrieve Hardware Info
        import psutil
        import platform
        
        # OS
        os_info = f"{platform.system()} {platform.release()} ({platform.architecture()[0]})"
        
        # CPU
        cpu_info = f"{platform.processor() or 'Unknown CPU'} ({psutil.cpu_count(logical=True)} CPUs)"
        
        # RAM
        ram_bytes = psutil.virtual_memory().total
        ram_gb = round(ram_bytes / (1024**3))
        ram_info = f"{ram_gb} GB RAM"
        
        # Disk (C: Drive)
        try:
            disk = psutil.disk_usage('C:\\') if platform.system() == "Windows" else psutil.disk_usage('/')
            disk_total = round(disk.total / (1024**3))
            disk_free = round(disk.free / (1024**3))
            disk_info = f"{disk_free} GB trống / Tổng {disk_total} GB (Ổ đĩa chính)"
        except Exception:
            disk_info = "Không thể đọc dữ liệu ổ đĩa"
            
        # GPU
        gpu_info = "Intel / AMD Integrated Graphics"
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
            
        # Display
        screen = QApplication.primaryScreen()
        res_str = f"{screen.geometry().width()} x {screen.geometry().height()} px (32 bit) (60Hz)" if screen else "1920 x 1080 px"

        # Create rows
        self._add_list_row(list_layout, "Hệ Điều Hành (OS):", os_info)
        self._add_list_row(list_layout, "Bộ Vi Xử Lý (CPU):", cpu_info)
        self._add_list_row(list_layout, "Bộ Nhớ Trong (RAM):", ram_info)
        self._add_list_row(list_layout, "Ổ Cứng (Disk):", disk_info)
        self._add_list_row(list_layout, "Card Đồ Họa (GPU):", gpu_info)
        self._add_list_row(list_layout, "Màn Hình (Display):", res_str, is_last=True)

        layout.addWidget(list_container)
        
        # App Version Card
        app_card = QFrame()
        app_card.setStyleSheet(
            f"QFrame {{ background: rgba(14, 20, 36, 0.4); border: 1px dashed rgba(255, 255, 255, 0.1); "
            f"border-radius: 8px; padding: 12px; margin-top: 12px; }}"
        )
        ac_layout = QHBoxLayout(app_card)
        ac_layout.setContentsMargins(8, 0, 8, 0)
        
        app_info = QVBoxLayout()
        app_title = QLabel("POP AI Assistant Pro - System Diagnostics")
        app_title.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {DesignTokens.TEXT_MAIN};")
        app_sub = QLabel("Phiên bản v2.5 Enterprise • Tối ưu hóa cho Windows x64")
        app_sub.setStyleSheet(f"font-size: 12px; color: {DesignTokens.TEXT_MUTED};")
        app_info.addWidget(app_title)
        app_info.addWidget(app_sub)
        
        ac_layout.addLayout(app_info, stretch=1)
        layout.addWidget(app_card)
        
        layout.addStretch()

    def _add_list_row(self, parent_layout, label_text: str, value_text: str, is_last: bool = False):
        row = QHBoxLayout()
        row.setSpacing(16)
        
        lbl = QLabel(label_text)
        lbl.setFixedWidth(140)
        lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {DesignTokens.TEXT_MUTED};")
        
        val = QLabel(value_text)
        val.setWordWrap(True)
        val.setStyleSheet(f"font-size: 14px; font-weight: 500; color: {DesignTokens.TEXT_MAIN};")
        
        row.addWidget(lbl)
        row.addWidget(val, stretch=1)
        parent_layout.addLayout(row)
        
        if not is_last:
            line = QFrame()
            line.setFixedHeight(1)
            line.setStyleSheet("background-color: rgba(255, 255, 255, 0.05);")
            parent_layout.addWidget(line)

    def update_system_telemetry(self):
        # Không cần telemetry real-time cho DxDiag style list view
        pass
