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
        title = QLabel("Thông Số Hệ Thống & Máy Tính")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {DesignTokens.TEXT_MAIN}; letter-spacing: 0.5px;")
        desc = QLabel("Thông tin cấu hình phần cứng và tình trạng tài nguyên hệ điều hành thời gian thực")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        layout.addLayout(title_box)

        # Grid of Modern Hardware Cards
        grid = QGridLayout()
        grid.setSpacing(14)

        # Card 1: OS
        self.card_os = self._create_card("Hệ Điều Hành", f"{platform.system()} {platform.release()}", f"Kiến trúc: {platform.architecture()[0]}")
        grid.addWidget(self.card_os, 0, 0)

        # Card 2: Screen Resolution
        screen = QApplication.primaryScreen()
        res_str = f"{screen.geometry().width()} × {screen.geometry().height()} px" if screen else "1920 × 1080 px"
        self.card_screen = self._create_card("Màn Hình Chính", res_str, "Tỷ lệ chuẩn 60Hz")
        grid.addWidget(self.card_screen, 0, 1)

        # Card 3: CPU with Progress Bar
        self.card_cpu, self.cpu_val_lbl, self.cpu_bar = self._create_meter_card("Bộ Vi Xử Lý (CPU)", f"{psutil.cpu_count(logical=True)} Luồng xử lý")
        grid.addWidget(self.card_cpu, 1, 0)

        # Card 4: RAM with Progress Bar
        self.card_ram, self.ram_val_lbl, self.ram_bar = self._create_meter_card("Bộ Nhớ RAM", "Đang tải...")
        grid.addWidget(self.card_ram, 1, 1)

        # Card 5: App Version Card (Span 2 columns)
        app_card = QFrame()
        app_card.setStyleSheet(
            f"QFrame {{ background: rgba(14, 20, 36, 0.65); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 12px; padding: 14px 18px; }}"
        )
        ac_layout = QHBoxLayout(app_card)
        ac_layout.setContentsMargins(4, 2, 4, 2)
        
        app_info = QVBoxLayout()
        app_info.setSpacing(3)
        app_title = QLabel("POP AI Assistant Pro")
        app_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {DesignTokens.CYAN_ACCENT};")
        app_sub = QLabel("Phiên bản v2.5 Enterprise • Tối ưu hóa cho Windows x64 • Hỗ trợ GGUF Cục bộ & Cloud")
        app_sub.setStyleSheet(f"font-size: 12px; color: {DesignTokens.TEXT_MUTED};")
        app_info.addWidget(app_title)
        app_info.addWidget(app_sub)
        
        ac_layout.addLayout(app_info, stretch=1)

        grid.addWidget(app_card, 2, 0, 1, 2)

        layout.addLayout(grid)
        layout.addStretch()

        self.update_system_telemetry()

    def _create_card(self, title: str, main_val: str, sub_val: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: rgba(14, 20, 36, 0.65); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 12px; padding: 14px 18px; }}"
        )
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(4)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {DesignTokens.TEXT_MUTED}; text-transform: uppercase; letter-spacing: 0.5px;")

        v_lbl = QLabel(main_val)
        v_lbl.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {DesignTokens.TEXT_MAIN};")

        s_lbl = QLabel(sub_val)
        s_lbl.setStyleSheet(f"font-size: 11px; color: {DesignTokens.TEXT_MUTED};")

        c_layout.addWidget(t_lbl)
        c_layout.addWidget(v_lbl)
        c_layout.addWidget(s_lbl)
        return card

    def _create_meter_card(self, title: str, sub_val: str):
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: rgba(14, 20, 36, 0.65); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 12px; padding: 14px 18px; }}"
        )
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(6)

        header = QHBoxLayout()
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {DesignTokens.TEXT_MUTED}; text-transform: uppercase; letter-spacing: 0.5px;")
        
        val_lbl = QLabel("0%")
        val_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {DesignTokens.CYAN_ACCENT};")
        header.addWidget(t_lbl)
        header.addStretch()
        header.addWidget(val_lbl)

        p_bar = QProgressBar()
        p_bar.setFixedHeight(8)
        p_bar.setStyleSheet(
            f"QProgressBar {{ background: {DesignTokens.SURFACE_2}; border: none; border-radius: 4px; text-align: right; }}"
            f"QProgressBar::chunk {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #008EFF, stop:1 #00FFAA); border-radius: 4px; }}"
        )
        p_bar.setValue(0)
        p_bar.setTextVisible(False)

        s_lbl = QLabel(sub_val)
        s_lbl.setStyleSheet(f"font-size: 11px; color: {DesignTokens.TEXT_MUTED};")

        c_layout.addLayout(header)
        c_layout.addWidget(p_bar)
        c_layout.addWidget(s_lbl)
        return card, val_lbl, p_bar

    def update_system_telemetry(self):
        try:
            cpu_usage = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()

            self.cpu_val_lbl.setText(f"{cpu_usage:.0f}%")
            self.cpu_bar.setValue(int(cpu_usage))

            used_gb = mem.used / (1024**3)
            total_gb = mem.total / (1024**3)
            self.ram_val_lbl.setText(f"{used_gb:.1f} / {total_gb:.1f} GB ({mem.percent:.0f}%)")
            self.ram_bar.setValue(int(mem.percent))
        except Exception:
            pass
