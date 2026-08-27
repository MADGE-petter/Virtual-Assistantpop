from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox
from view.ui.styles import DesignTokens
from view.ui.settings.settings_config import save_user_settings


class RulesTabWidget(QWidget):
    """Tab 4: Lệnh Ngữ Cảnh & System Rules."""

    settingsChanged = pyqtSignal()

    def __init__(self, user_settings: dict, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Lệnh Ngữ Cảnh & System Rules")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT};")
        layout.addWidget(title)

        desc = QLabel("Thiết lập quy tắc ngữ cảnh mặc định. Lệnh này sẽ tự động được áp dụng trước mỗi câu hỏi của bạn khi chat:")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.txt_rule = QTextEdit()
        self.txt_rule.setPlainText(self.user_settings.get("system_rule", ""))
        self.txt_rule.setStyleSheet(
            f"QTextEdit {{ background-color: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; "
            f"border-radius: 10px; padding: 12px; color: {DesignTokens.TEXT_MAIN}; font-size: 13px; }}"
        )
        layout.addWidget(self.txt_rule, stretch=1)

        save_rule_btn = QPushButton("Lưu Quy Tắc Ngữ Cảnh")
        save_rule_btn.setFixedSize(180, 36)
        save_rule_btn.setStyleSheet(f"QPushButton {{ background-color: {DesignTokens.CYAN}; color: black; font-weight: bold; border-radius: 8px; }}")
        save_rule_btn.clicked.connect(self._save_system_rule)
        layout.addWidget(save_rule_btn)

    def _save_system_rule(self):
        self.user_settings["system_rule"] = self.txt_rule.toPlainText().strip()
        save_user_settings(self.user_settings)
        self.settingsChanged.emit()
        QMessageBox.information(self, "Thành công", "Đã cập nhật quy tắc ngữ cảnh hệ thống!")
