import platform
import psutil
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QLinearGradient, QPen, QBrush, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QApplication, QScrollArea, QSizePolicy, QGraphicsDropShadowEffect
)
from view.ui.styles import DesignTokens


class GradientLabel(QLabel):
    """Render label text with a radiant horizontal linear gradient (Cyan -> Sky Blue -> Violet)."""

    def __init__(self, text: str = "", font_size: int = 11, font_weight: int = 700, letter_spacing: float = 0.8, parent=None):
        super().__init__(text, parent)
        self.letter_spacing = letter_spacing
        f = self.font()
        f.setPointSize(font_size)
        f.setBold(font_weight >= 600)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, letter_spacing)
        self.setFont(f)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("border: none; background: transparent; padding: 0px; margin: 0px;")

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        grad = QLinearGradient(0, 0, max(self.width(), 120), 0)
        grad.setColorAt(0.0, QColor("#008EFF"))   # Xanh dương (Electric Blue)
        grad.setColorAt(1.0, QColor("#00FFAA"))   # Xanh lá (Emerald Green)

        painter.setPen(QPen(QBrush(grad), 1))
        painter.setFont(self.font())
        painter.drawText(self.rect(), self.alignment() | Qt.TextFlag.TextWordWrap, self.text())
        painter.end()


class AboutTabWidget(QWidget):
    """Tab 6: Thông Số Máy & Hệ Thống (About Me) thiết kế dạng Hardware Diagnostic Dashboard bán trong suốt cao cấp."""

    def __init__(self, user_settings: dict, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self._setup_ui()

    def _setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(22)

        # --------------------------------------------------------
        # 1. Header Title Bar
        # --------------------------------------------------------
        title_box = QVBoxLayout()
        title_box.setSpacing(6)

        title_row = QHBoxLayout()
        title = QLabel("Thông Số Máy Tính & Chẩn Đoán")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {DesignTokens.TEXT_MAIN}; letter-spacing: 0.5px; border: none; background: transparent;")

        badge = QLabel("DIAGNOSTICS")
        badge.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #008EFF, stop:1 #00FFAA); "
            "color: #040812; font-size: 11px; font-weight: 800; letter-spacing: 0.8px; "
            "border-radius: 6px; padding: 4px 10px; border: none;"
        )
        title_row.addWidget(title)
        title_row.addWidget(badge)
        title_row.addStretch()

        desc = QLabel("Thông số cấu hình phần cứng, card đồ họa và môi trường thực thi của máy tính")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 13px; border: none; background: transparent;")
        desc.setWordWrap(True)

        title_box.addLayout(title_row)
        title_box.addWidget(desc)
        layout.addLayout(title_box)

        # --------------------------------------------------------
        # 2. Retrieve Hardware Info Safely
        # --------------------------------------------------------
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
            vram_gb = round(float(int(mem.total)) / (1024**3), 1)
            gpu_info = f"{gpu_name} ({vram_gb} GB VRAM)"
        except Exception:
            pass

        screen = QApplication.primaryScreen()
        res_str = f"{screen.geometry().width()} × {screen.geometry().height()} px ({screen.depth()} bit)" if screen else "1920 × 1080 px"

        # --------------------------------------------------------
        # 3. Hardware Grid (2 columns, pure black floating cards with gradient border & icons)
        # --------------------------------------------------------
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(18)
        grid_layout.setVerticalSpacing(18)
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)

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

        scroll.setWidget(content_widget)
        root_layout.addWidget(scroll)

    def _create_spec_card(self, icon_type: str, label: str, value: str, sub: str) -> QFrame:
        from view.ui.icons import get_vector_pixmap
        card = QFrame()
        card.setObjectName("specCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        # Nền hoàn toàn trong suốt + viền trắng pha gradient phối trên-dưới
        card.setStyleSheet(
            "#specCard {"
            "  background: transparent;"
            "  border: 1px solid;"
            "  border-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 255, 255, 0.32), stop:0.35 rgba(255, 255, 255, 0.12), stop:0.8 rgba(255, 255, 255, 0.04), stop:1 rgba(255, 255, 255, 0.01));"
            "  border-radius: 14px;"
            "}"
            "#specCard:hover {"
            "  background: rgba(255, 255, 255, 0.04);"
            "  border-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 255, 255, 0.55), stop:0.4 rgba(255, 255, 255, 0.22), stop:1 rgba(255, 255, 255, 0.06));"
            "}"
            "#specCard QLabel {"
            "  border: none;"
            "  background: transparent;"
            "  padding: 0px;"
            "  margin: 0px;"
            "}"
        )

        # Hiệu ứng nổi bóng mờ 3D bán trong suốt
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 6)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(10)

        # Header Row: Icon Badge (vẽ gradient) + Category Label (chữ gradient)
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        icon_box = QFrame()
        icon_box.setFixedSize(34, 34)
        icon_box.setStyleSheet(
            "QFrame {"
            "  background: transparent;"
            "  border: 1px solid rgba(255, 255, 255, 0.12);"
            "  border-radius: 9px;"
            "}"
            "QFrame QLabel { border: none; background: transparent; padding: 0px; }"
        )
        ib_layout = QHBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        ib_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Icon vẽ bằng vector gradient đa sắc siêu nét
        icon_lbl.setPixmap(get_vector_pixmap(icon_type, "gradient", 18))
        ib_layout.addWidget(icon_lbl)

        # Tiêu đề danh mục dạng chữ gradient
        lbl = GradientLabel(label, font_size=11, font_weight=700, letter_spacing=0.8)

        header_row.addWidget(icon_box)
        header_row.addWidget(lbl)
        header_row.addStretch()

        # Primary Hardware Value
        val = QLabel(value)
        val.setWordWrap(True)
        val.setStyleSheet("font-size: 15px; font-weight: 600; color: #FFFFFF;")

        # Subtitle / Detail
        sub_lbl = QLabel(sub)
        sub_lbl.setWordWrap(True)
        sub_lbl.setStyleSheet(f"font-size: 12px; color: {DesignTokens.TEXT_SECONDARY};")

        card_layout.addLayout(header_row)
        card_layout.addWidget(val)
        card_layout.addWidget(sub_lbl)
        return card

    def update_system_telemetry(self):
        pass
