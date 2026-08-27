from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QPushButton, QMessageBox
from view.ui.styles import DesignTokens
from view.settings.settings_config import save_user_settings


class GeneralTabWidget(QWidget):
    """Tab 1: Cài đặt chung."""

    def __init__(self, user_settings: dict, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Cài Đặt Chung")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT};")
        layout.addWidget(title)

        self.chk_autostart = QCheckBox("Khởi động POP AI cùng hệ thống Windows")
        self.chk_autostart.setChecked(self.user_settings.get("autostart", False))
        self.chk_autostart.setStyleSheet(f"font-size: 13px; color: {DesignTokens.TEXT_MAIN};")

        self.chk_mascot = QCheckBox("Luôn giữ linh vật Mini Mascot lơ lửng trên màn hình")
        self.chk_mascot.setChecked(self.user_settings.get("mascot_top", True))
        self.chk_mascot.setStyleSheet(f"font-size: 13px; color: {DesignTokens.TEXT_MAIN};")

        self.chk_tts = QCheckBox("Bật phản hồi âm thanh (Giọng nói POP)")
        self.chk_tts.setChecked(self.user_settings.get("tts_enabled", True))
        self.chk_tts.setStyleSheet(f"font-size: 13px; color: {DesignTokens.TEXT_MAIN};")

        layout.addWidget(self.chk_autostart)
        layout.addWidget(self.chk_mascot)
        layout.addWidget(self.chk_tts)

        layout.addStretch()

        save_btn = QPushButton("Lưu Cài Đặt")
        save_btn.setFixedSize(140, 36)
        save_btn.setStyleSheet(f"QPushButton {{ background-color: {DesignTokens.CYAN}; color: black; font-weight: bold; border-radius: 8px; }}")
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)

    def _save_settings(self):
        self.user_settings["autostart"] = self.chk_autostart.isChecked()
        self.user_settings["mascot_top"] = self.chk_mascot.isChecked()
        self.user_settings["tts_enabled"] = self.chk_tts.isChecked()
        save_user_settings(self.user_settings)
        QMessageBox.information(self, "Thành công", "Đã lưu cài đặt chung!")
