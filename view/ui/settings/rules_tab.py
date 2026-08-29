from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton,
    QFrame, QMessageBox
)
from view.ui.styles import DesignTokens
from view.ui.settings.settings_config import save_user_settings


class RulesTabWidget(QWidget):
    """Tab 4: Lệnh Ngữ Cảnh & System Rules phong cách hiện đại."""

    settingsChanged = pyqtSignal()

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
        title = QLabel("Quy Tắc Ngữ Cảnh Hệ Thống")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {DesignTokens.TEXT_MAIN}; letter-spacing: 0.5px;")
        desc = QLabel("Định hình phong cách trả lời và chỉ thị hệ thống mặc định trước mọi câu hỏi khi trò chuyện")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        layout.addLayout(title_box)

        # Quick Presets Bar
        presets_card = QFrame()
        presets_card.setStyleSheet(
            f"QFrame {{ background: rgba(14, 20, 36, 0.65); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 10px; }}"
        )
        pb_layout = QHBoxLayout(presets_card)
        pb_layout.setContentsMargins(14, 10, 14, 10)
        pb_layout.setSpacing(8)

        pb_lbl = QLabel("Mẫu có sẵn:")
        pb_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {DesignTokens.TEXT_MUTED};")
        pb_layout.addWidget(pb_lbl)

        presets = [
            ("Trợ lý Tiếng Việt", "Bạn là POP AI Assistant, trợ lý thông minh thân thiện bằng tiếng Việt, luôn giải thích rõ ràng và hữu ích."),
            ("Chuyên gia Lập trình", "Bạn là chuyên gia lập trình phần mềm cấp cao. Hãy trả lời trọng tâm, tối ưu code sạch sẽ, giải thích thuật toán ngắn gọn."),
            ("Ngắn gọn & Súc tích", "Hãy trả lời cực kỳ ngắn gọn, đi thẳng vào trọng tâm vấn đề, không dài dòng."),
        ]

        for p_title, p_content in presets:
            p_btn = QPushButton(p_title)
            p_btn.setFixedHeight(28)
            p_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            p_btn.setStyleSheet(
                f"QPushButton {{ background: {DesignTokens.SURFACE_2}; color: {DesignTokens.TEXT_MAIN}; border: 1px solid {DesignTokens.BORDER}; "
                f"border-radius: 6px; padding: 0 10px; font-size: 11px; font-weight: 500; }}"
                f"QPushButton:hover {{ background: {DesignTokens.SURFACE_3}; border-color: {DesignTokens.CYAN}; color: {DesignTokens.CYAN_ACCENT}; }}"
            )
            p_btn.clicked.connect(lambda _, txt=p_content: self.txt_rule.setPlainText(txt))
            pb_layout.addWidget(p_btn)

        pb_layout.addStretch()
        layout.addWidget(presets_card)

        # Editor Area
        self.txt_rule = QTextEdit()
        self.txt_rule.setPlaceholderText("Nhập câu lệnh hệ thống (System Prompt) của bạn ở đây...")
        self.txt_rule.setPlainText(self.user_settings.get("system_rule", "Bạn là POP AI Assistant, trợ lý thông minh thân thiện bằng tiếng Việt."))
        self.txt_rule.setStyleSheet(
            f"QTextEdit {{ background-color: rgba(14, 20, 36, 0.65); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 10px; padding: 14px; color: {DesignTokens.TEXT_MAIN}; font-size: 13px; line-height: 1.5; }}"
            f"QTextEdit:focus {{ border-color: {DesignTokens.CYAN}; }}"
        )
        layout.addWidget(self.txt_rule, stretch=1)

        # Bottom Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()

        save_rule_btn = QPushButton("Lưu Quy Tắc")
        save_rule_btn.setFixedHeight(38)
        save_rule_btn.setFixedWidth(140)
        save_rule_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_rule_btn.setStyleSheet(
            f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #008EFF, stop:1 #00FFAA); "
            f"color: #03050B; font-weight: bold; font-size: 13px; border: none; border-radius: 8px; }}"
            f"QPushButton:hover {{ background: #00FFAA; }}"
        )
        save_rule_btn.clicked.connect(self._save_system_rule)
        bottom_bar.addWidget(save_rule_btn)

        layout.addLayout(bottom_bar)

    def _save_system_rule(self):
        self.user_settings["system_rule"] = self.txt_rule.toPlainText().strip()
        save_user_settings(self.user_settings)
        self.settingsChanged.emit()
        QMessageBox.information(self, "Thành công", "Đã cập nhật quy tắc ngữ cảnh hệ thống thành công!")
