import psutil
import platform
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QApplication
from view.ui.styles import DesignTokens


class AboutTabWidget(QWidget):
    """Tab 6: Thông Số Máy & Hệ Thống (About Me)."""

    def __init__(self, user_settings: dict, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("Thông Số Hệ Thống & Cấu Hình Máy (About Me)")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT};")
        layout.addWidget(title)

        self.telemetry_box = QTextEdit()
        self.telemetry_box.setReadOnly(True)
        self.telemetry_box.setStyleSheet(
            f"QTextEdit {{ background-color: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; "
            f"border-radius: 10px; padding: 14px; color: {DesignTokens.TEXT_MAIN}; font-family: Consolas, monospace; font-size: 12px; }}"
        )
        layout.addWidget(self.telemetry_box, stretch=1)

        self.update_system_telemetry()

    def update_system_telemetry(self):
        cpu_usage = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        screen = QApplication.primaryScreen()
        res = screen.geometry() if screen else None

        info = f"""==================================================
  POP AI ASSISTANT - HỆ THỐNG GIÁM SÁT PHẦN CỨNG
==================================================

💻 Hệ điều hành   : {platform.system()} {platform.release()} ({platform.architecture()[0]})
🖥️ Màn hình      : {res.width()}x{res.height()} px
⚙️ Bộ vi xử lý    : {platform.processor()} ({psutil.cpu_count(logical=True)} Threads)
📊 Mức sử dụng CPU : {cpu_usage}%

🧠 Bộ nhớ RAM     : {mem.used / (1024**3):.2f} GB / {mem.total / (1024**3):.2f} GB ({mem.percent}%)
💾 Thư mục Model  : {self.user_settings.get('model_dir')}

🚀 Phiên bản App  : POP AI v2.5 (Windows Enterprise Edition)
"""
        self.telemetry_box.setPlainText(info)
