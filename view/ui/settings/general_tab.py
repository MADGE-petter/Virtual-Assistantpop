from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QTimer, QSettings
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QScrollArea
)
from view.ui.styles import DesignTokens
from view.ui.icons import create_vector_icon
from view.ui.settings.settings_config import save_user_settings


class ToggleSwitch(QWidget):
    """Modern iOS/Windows 11 style animated toggle switch widget."""
    toggled = pyqtSignal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self.setFixedSize(46, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        if self._checked != checked:
            self._checked = checked
            self.toggled.emit(self._checked)
            self.update()

    def mousePressEvent(self, a0):
        if a0.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
            a0.accept()

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        r = h / 2.0

        # Background Track
        if self._checked:
            track_color = QColor(0, 255, 170)  # Cyan / Emerald accent
            border_color = QColor(0, 255, 170)
        else:
            track_color = QColor(25, 34, 48)
            border_color = QColor(45, 58, 78)

        painter.setBrush(QBrush(track_color))
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), r, r)

        # Thumb (circle slider)
        thumb_radius = r - 3.5
        thumb_y = r
        thumb_x = (w - r) if self._checked else r
        thumb_color = QColor(3, 5, 11) if self._checked else QColor(180, 200, 220)

        painter.setBrush(QBrush(thumb_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(thumb_x - thumb_radius, thumb_y - thumb_radius, thumb_radius * 2, thumb_radius * 2))


class GeneralTabWidget(QWidget):
    """Tab 1: Cài đặt chung & Phân bổ phần cứng (RAM/CPU/eGPU) phong cách Glassmorphism Cyberpunk thanh lịch."""

    settingsChanged = pyqtSignal()

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
        layout.setSpacing(20)

        # Header Title Bar
        title_box = QVBoxLayout()
        title_box.setSpacing(6)

        title_row = QHBoxLayout()
        title = QLabel("Cài Đặt Chung & Phần Cứng")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {DesignTokens.TEXT_MAIN}; letter-spacing: 0.5px;")
        
        badge = QLabel("HỆ THỐNG & eGPU")
        badge.setStyleSheet(
            f"background: transparent; color: {DesignTokens.CYAN_ACCENT}; font-size: 11px; "
            f"font-weight: 700; border-radius: 4px; padding: 2px 8px; border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT};"
        )
        title_row.addWidget(title)
        title_row.addWidget(badge)
        title_row.addStretch()

        desc = QLabel("Tùy chỉnh hành vi hệ thống và thiết lập phân bổ tài nguyên phần cứng (RAM / eGPU) cho các mô hình AI")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 13px;")

        title_box.addLayout(title_row)
        title_box.addWidget(desc)
        layout.addLayout(title_box)

        # Section 1: System & Mascot Settings
        card = QFrame()
        card.setObjectName("generalCard")
        card.setStyleSheet(
            f"#generalCard {{ background: transparent; border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; "
            f"border-radius: 14px; }}"
            f"#generalCard:hover {{ background: rgba(255, 255, 255, 0.03); border-color: {DesignTokens.BORDER_GRADIENT_HOVER}; }}"
            f"#generalCard QLabel {{ border: none; background: transparent; }}"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 18, 22, 18)
        card_layout.setSpacing(16)

        # Setting 1: Autostart
        s1 = self._create_setting_row(
            "Khởi động cùng hệ thống",
            "Tự động chạy POP AI ngầm dưới khay hệ thống khi bạn bật máy tính",
            self.user_settings.get("autostart", False)
        )
        self.sw_autostart = s1[1]
        card_layout.addLayout(s1[0])

        card_layout.addWidget(self._create_separator())

        # Setting 2: Mini Mascot Top
        s2 = self._create_setting_row(
            "Ghim Linh vật Mini Mascot",
            "Luôn giữ biểu tượng trợ lý ảo Mini Mascot nổi lơ lửng trên mọi cửa sổ máy tính",
            self.user_settings.get("mascot_top", True)
        )
        self.sw_mascot = s2[1]
        card_layout.addLayout(s2[0])

        card_layout.addWidget(self._create_separator())

        # Setting 3: Voice Feedback
        s3 = self._create_setting_row(
            "Phản hồi bằng Giọng nói (TTS)",
            "POP AI sẽ tự động đọc câu trả lời bằng giọng nói tiếng Việt tự nhiên",
            self.user_settings.get("tts_enabled", True)
        )
        self.sw_tts = s3[1]
        card_layout.addLayout(s3[0])

        card_layout.addWidget(self._create_separator())

        # Setting 4: Mascot Sleep Timeout
        s4 = self._create_combo_setting_row(
            "Thời gian chờ tự động ngủ (Mascot Sleep)",
            "Chuyển linh vật sang trạng thái ngủ tiết kiệm tài nguyên khi không tương tác chuột",
            current_minutes=self.user_settings.get("mascot_sleep_timeout_minutes", 3)
        )
        self.combo_sleep = s4[1]
        card_layout.addLayout(s4[0])

        layout.addWidget(card)

        # Section 2: Hardware Acceleration & Offload (RAM vs eGPU)
        hw_title = QLabel("Phân Bổ Phần Cứng (Hardware Acceleration / eGPU)")
        hw_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {DesignTokens.CYAN_ACCENT}; letter-spacing: 0.5px; margin-top: 6px;")
        layout.addWidget(hw_title)

        hw_card = QFrame()
        hw_card.setObjectName("hwCard")
        hw_card.setStyleSheet(
            f"#hwCard {{ background: transparent; border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; "
            f"border-radius: 14px; }}"
            f"#hwCard:hover {{ background: rgba(255, 255, 255, 0.03); border-color: {DesignTokens.BORDER_GRADIENT_HOVER}; }}"
            f"#hwCard QLabel {{ border: none; background: transparent; }}"
        )
        hw_layout = QVBoxLayout(hw_card)
        hw_layout.setContentsMargins(22, 18, 22, 18)
        hw_layout.setSpacing(16)

        # Hardware Setting 1: Voice models compute device
        voice_opts = [
            ("RAM / CPU (Mặc định - Tiết kiệm VRAM)", "cpu"),
            ("GPU / eGPU (CUDA)", "cuda")
        ]
        h1 = self._create_custom_combo_row(
            "Thiết bị chạy 2 Model Giọng nói (ASR & TTS)",
            "Chạy model Nhận diện (Zipformer) và Phát âm (MeloTTS) bằng RAM để dành 100% VRAM cho LLM",
            options=voice_opts,
            current_val=self.user_settings.get("voice_device", "cpu")
        )
        self.combo_voice_dev = h1[1]
        hw_layout.addLayout(h1[0])

        hw_layout.addWidget(self._create_separator())

        # Hardware Setting 2: LLM compute device
        llm_opts = [
            ("eGPU / GPU Rời (Toàn bộ layers: -1)", "gpu"),
            ("RAM / CPU (CPU Only: 0 layers)", "cpu")
        ]
        h2 = self._create_custom_combo_row(
            "Thiết bị chạy Mô hình Đàm thoại (LLM)",
            "Đẩy tối đa trọng số mô hình LLM lên card đồ họa eGPU để đạt tốc độ phản hồi nhanh nhất",
            options=llm_opts,
            current_val=self.user_settings.get("llm_device", "gpu")
        )
        self.combo_llm_dev = h2[1]
        hw_layout.addLayout(h2[0])

        hw_layout.addWidget(self._create_separator())

        # Hardware Setting 3: Main GPU Index (for multi-GPU / eGPU setups)
        gpu_idx_opts = [
            ("GPU 0 (Mặc định eGPU / Card đồ họa chính)", 0),
            ("GPU 1 (Card đồ họa phụ)", 1),
            ("GPU 2", 2)
        ]
        h3 = self._create_custom_combo_row(
            "Chỉ định GPU chính (eGPU Device Index)",
            "Chỉ định GPU index cho eGPU khi máy có nhiều card (ví dụ: iGPU tích hợp + eGPU rời)",
            options=gpu_idx_opts,
            current_val=int(self.user_settings.get("llm_main_gpu", 0))
        )
        self.combo_main_gpu = h3[1]
        hw_layout.addLayout(h3[0])

        layout.addWidget(hw_card)
        layout.addStretch()

        # Bottom Action Bar with In-App Status Notification
        bottom_bar = QHBoxLayout()
        
        self.status_feedback = QLabel("")
        self.status_feedback.setStyleSheet(f"color: {DesignTokens.CYAN_ACCENT}; font-size: 13px; font-weight: 600;")
        self.status_feedback.hide()
        bottom_bar.addWidget(self.status_feedback)

        bottom_bar.addStretch()

        save_btn = QPushButton(" Lưu Thay Đổi")
        save_btn.setIcon(create_vector_icon("check", "#03050B", 16))
        save_btn.setFixedHeight(38)
        save_btn.setFixedWidth(150)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(
            f"QPushButton {{ background: {DesignTokens.GRADIENT_BLUE_GREEN}; "
            f"color: #03050B; font-weight: 700; font-size: 13px; border: none; border-radius: 8px; padding: 0 16px; }}"
            f"QPushButton:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0077D6, stop:1 #00E699); }}"
            f"QPushButton:pressed {{ background: #00CC88; }}"
        )
        save_btn.clicked.connect(self._save_settings)
        bottom_bar.addWidget(save_btn)

        layout.addLayout(bottom_bar)

        scroll.setWidget(content_widget)
        root_layout.addWidget(scroll)

    def _create_setting_row(self, title: str, subtitle: str, default_val: bool):
        row = QHBoxLayout()
        row.setSpacing(14)

        text_box = QVBoxLayout()
        text_box.setSpacing(3)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {DesignTokens.TEXT_MAIN};")

        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet(f"font-size: 12px; color: {DesignTokens.TEXT_MUTED};")

        text_box.addWidget(lbl_title)
        text_box.addWidget(lbl_sub)
        row.addLayout(text_box, stretch=1)

        switch = ToggleSwitch(checked=default_val)
        row.addWidget(switch, alignment=Qt.AlignmentFlag.AlignVCenter)

        return row, switch

    def _create_combo_setting_row(self, title: str, subtitle: str, current_minutes: int = 3):
        options = [
            ("1 phút", 1),
            ("2 phút", 2),
            ("3 phút (Mặc định)", 3),
            ("5 phút", 5),
            ("10 phút", 10),
            ("15 phút", 15)
        ]
        return self._create_custom_combo_row(title, subtitle, options, current_minutes)

    def _create_custom_combo_row(self, title: str, subtitle: str, options: list, current_val):
        row = QHBoxLayout()
        row.setSpacing(14)

        text_box = QVBoxLayout()
        text_box.setSpacing(3)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {DesignTokens.TEXT_MAIN};")

        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet(f"font-size: 12px; color: {DesignTokens.TEXT_MUTED};")

        text_box.addWidget(lbl_title)
        text_box.addWidget(lbl_sub)
        row.addLayout(text_box, stretch=1)

        combo = QComboBox()
        combo.setFixedHeight(34)
        combo.setCursor(Qt.CursorShape.PointingHandCursor)
        combo.setStyleSheet(
            f"QComboBox {{ background: rgba(20, 28, 44, 0.85); border: 1px solid rgba(0, 255, 170, 0.3); "
            f"border-radius: 8px; padding: 4px 12px; color: {DesignTokens.TEXT_MAIN}; font-size: 13px; font-weight: 600; min-width: 180px; }}"
            f"QComboBox:hover {{ border-color: {DesignTokens.CYAN_ACCENT}; background: rgba(28, 40, 62, 0.95); }}"
            f"QComboBox::drop-down {{ border: none; width: 22px; }}"
            f"QComboBox QAbstractItemView {{ background: #0B111E; border: 1px solid #1E293B; "
            f"border-radius: 8px; color: {DesignTokens.TEXT_MAIN}; selection-background-color: rgba(0, 255, 170, 0.2); selection-color: #00FFAA; padding: 4px; }}"
        )
        selected_index = 0
        for i, (text, val) in enumerate(options):
            combo.addItem(text, val)
            if val == current_val or str(val) == str(current_val):
                selected_index = i
        combo.setCurrentIndex(selected_index)

        row.addWidget(combo, alignment=Qt.AlignmentFlag.AlignVCenter)
        return row, combo

    def _create_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: rgba(255, 255, 255, 0.06); max-height: 1px;")
        return sep

    def _save_settings(self):
        self.user_settings["autostart"] = self.sw_autostart.isChecked()
        self.user_settings["mascot_top"] = self.sw_mascot.isChecked()
        self.user_settings["tts_enabled"] = self.sw_tts.isChecked()
        sleep_minutes = int(self.combo_sleep.currentData())
        self.user_settings["mascot_sleep_timeout_minutes"] = sleep_minutes

        # Hardware settings
        voice_dev = str(self.combo_voice_dev.currentData())
        llm_dev = str(self.combo_llm_dev.currentData())
        main_gpu = int(self.combo_main_gpu.currentData())

        self.user_settings["voice_device"] = voice_dev
        self.user_settings["llm_device"] = llm_dev
        self.user_settings["llm_gpu_layers"] = -1 if llm_dev == "gpu" else 0
        self.user_settings["llm_main_gpu"] = main_gpu

        save_user_settings(self.user_settings)

        # Sync to persistent QSettings & emit update
        QSettings("PopAI", "MiniMascot").setValue("sleep_timeout_minutes", sleep_minutes)
        self.settingsChanged.emit()

        # Reload LLM config so hardware offloading applies dynamically
        try:
            from service.llm_service import LLMService
            LLMService().reload_config()
        except Exception:
            pass

        # In-app feedback
        self.status_feedback.setText(f"Đã lưu: Giọng nói={voice_dev.upper()}, LLM={llm_dev.upper()} (GPU {main_gpu}).")
        self.status_feedback.show()
        QTimer.singleShot(2600, lambda: self.status_feedback.hide())

