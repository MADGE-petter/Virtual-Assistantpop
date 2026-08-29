from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton,
    QFrame, QMessageBox
)
from view.ui.styles import DesignTokens
from view.ui.settings.settings_config import save_user_settings


class GeneralTabWidget(QWidget):
    """Tab 1: Cài đặt chung phong cách hiện đại, tinh tế."""

    def __init__(self, user_settings: dict, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        # Header
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title = QLabel("Cài Đặt Chung")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {DesignTokens.TEXT_MAIN}; letter-spacing: 0.5px;")
        desc = QLabel("Tùy chỉnh hành vi khởi chạy, hiển thị linh vật và giọng nói của POP Assistant")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        layout.addLayout(title_box)

        # Settings Card Container
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: rgba(14, 20, 36, 0.65); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 12px; }}"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(16)

        # Setting 1: Autostart
        s1 = self._create_setting_row(
            "Khởi động cùng hệ thống",
            "Tự động chạy POP AI ngầm dưới khay hệ thống khi bạn bật máy tính",
            self.user_settings.get("autostart", False)
        )
        self.chk_autostart = s1[1]
        card_layout.addLayout(s1[0])

        card_layout.addWidget(self._create_separator())

        # Setting 2: Mini Mascot Top
        s2 = self._create_setting_row(
            "Ghim Linh vật Mini Mascot",
            "Luôn giữ biểu tượng trợ lý ảo Mini Mascot nổi lơ lửng trên mọi cửa sổ",
            self.user_settings.get("mascot_top", True)
        )
        self.chk_mascot = s2[1]
        card_layout.addLayout(s2[0])

        card_layout.addWidget(self._create_separator())

        # Setting 3: Voice Feedback
        s3 = self._create_setting_row(
            "Phản hồi bằng Giọng nói (TTS)",
            "POP AI sẽ tự động đọc câu trả lời bằng giọng nói tiếng Việt tự nhiên",
            self.user_settings.get("tts_enabled", True)
        )
        self.chk_tts = s3[1]
        card_layout.addLayout(s3[0])

        layout.addWidget(card)
        layout.addStretch()

        # Bottom Action Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()

        save_btn = QPushButton("Lưu Thay Đổi")
        save_btn.setFixedHeight(38)
        save_btn.setFixedWidth(140)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(
            f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #008EFF, stop:1 #00FFAA); "
            f"color: #03050B; font-weight: bold; font-size: 13px; border: none; border-radius: 8px; }}"
            f"QPushButton:hover {{ background: #00FFAA; }}"
        )
        save_btn.clicked.connect(self._save_settings)
        bottom_bar.addWidget(save_btn)

        layout.addLayout(bottom_bar)

    def _create_setting_row(self, title: str, subtitle: str, default_val: bool):
        row = QHBoxLayout()
        row.setSpacing(12)

        text_box = QVBoxLayout()
        text_box.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {DesignTokens.TEXT_MAIN};")

        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet(f"font-size: 12px; color: {DesignTokens.TEXT_MUTED};")

        text_box.addWidget(lbl_title)
        text_box.addWidget(lbl_sub)
        row.addLayout(text_box, stretch=1)

        chk = QCheckBox()
        chk.setChecked(default_val)
        chk.setCursor(Qt.CursorShape.PointingHandCursor)
        chk.setStyleSheet(
            f"QCheckBox::indicator {{ width: 20px; height: 20px; border-radius: 5px; border: 1px solid {DesignTokens.BORDER}; background: {DesignTokens.SURFACE_1}; }}"
            f"QCheckBox::indicator:checked {{ background-color: {DesignTokens.CYAN_ACCENT}; border-color: {DesignTokens.CYAN_ACCENT}; image: none; }}"
        )
        row.addWidget(chk)

        return row, chk

    def _create_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); max-height: 1px;")
        return sep

    def _save_settings(self):
        self.user_settings["autostart"] = self.chk_autostart.isChecked()
        self.user_settings["mascot_top"] = self.chk_mascot.isChecked()
        self.user_settings["tts_enabled"] = self.chk_tts.isChecked()
        save_user_settings(self.user_settings)
        QMessageBox.information(self, "Thành công", "Đã lưu cài đặt chung thành công!")
