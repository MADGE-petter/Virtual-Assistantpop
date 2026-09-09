from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton,
    QFrame
)
from view.ui.styles import DesignTokens
from view.ui.icons import create_vector_icon
from view.ui.settings.settings_config import save_user_settings


class RulesTabWidget(QWidget):
    """Tab 4: Lệnh Ngữ Cảnh & System Rules phong cách Cyberpunk Glassmorphic chuyên nghiệp."""

    settingsChanged = pyqtSignal()

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
        title = QLabel("Quy Tắc Ngữ Cảnh Hệ Thống")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {DesignTokens.TEXT_MAIN}; letter-spacing: 0.5px;")

        badge = QLabel("SYSTEM PROMPT")
        badge.setStyleSheet(
            f"background: rgba(0, 255, 170, 0.12); color: {DesignTokens.CYAN_ACCENT}; font-size: 11px; "
            f"font-weight: 700; border-radius: 4px; padding: 2px 8px; border: 1px solid rgba(0, 255, 170, 0.25);"
        )
        title_row.addWidget(title)
        title_row.addWidget(badge)
        title_row.addStretch()

        desc = QLabel("Định hình phong cách trả lời, vai trò chuyên môn và chỉ thị hệ thống mặc định trước mọi câu hỏi")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 13px;")

        title_box.addLayout(title_row)
        title_box.addWidget(desc)
        layout.addLayout(title_box)

        # Quick Presets Card
        presets_card = QFrame()
        presets_card.setStyleSheet(
            f"QFrame {{ background: rgba(16, 22, 31, 0.75); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 12px; padding: 6px 12px; }}"
        )
        pb_layout = QHBoxLayout(presets_card)
        pb_layout.setContentsMargins(8, 6, 8, 6)
        pb_layout.setSpacing(10)

        pb_lbl = QLabel("Mẫu có sẵn:")
        pb_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {DesignTokens.TEXT_SECONDARY};")
        pb_layout.addWidget(pb_lbl)

        presets = [
            ("Trợ lý Tiếng Việt", "Bạn là POP AI Assistant, trợ lý thông minh thân thiện bằng tiếng Việt, luôn giải thích rõ ràng và hữu ích."),
            ("Chuyên gia Lập trình", "Bạn là chuyên gia lập trình phần mềm cấp cao. Hãy trả lời trọng tâm, tối ưu code sạch sẽ, chuẩn PEP8/TypeScript, giải thích thuật toán ngắn gọn."),
            ("Ngắn gọn & Súc tích", "Hãy trả lời cực kỳ ngắn gọn, đi thẳng vào trọng tâm vấn đề, không giải thích dài dòng trừ khi được yêu cầu."),
            ("Phân tích Dữ liệu", "Bạn là nhà khoa học dữ liệu. Hãy phân tích các khía cạnh logic, trình bày dưới dạng bảng hoặc danh sách bullet points rõ ràng.")
        ]

        for p_title, p_content in presets:
            p_btn = QPushButton(p_title)
            p_btn.setFixedHeight(30)
            p_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            p_btn.setStyleSheet(
                f"QPushButton {{ background: {DesignTokens.SURFACE_2}; color: {DesignTokens.TEXT_MAIN}; border: 1px solid {DesignTokens.BORDER}; "
                f"border-radius: 6px; padding: 0 12px; font-size: 12px; font-weight: 500; }}"
                f"QPushButton:hover {{ background: {DesignTokens.SURFACE_3}; border-color: {DesignTokens.CYAN}; color: {DesignTokens.CYAN_ACCENT}; }}"
            )
            p_btn.clicked.connect(lambda _, txt=p_content: self.txt_rule.setPlainText(txt))
            pb_layout.addWidget(p_btn)

        pb_layout.addStretch()
        layout.addWidget(presets_card)

        # Editor Area Card
        editor_card = QFrame()
        editor_card.setStyleSheet(
            f"QFrame {{ background: rgba(16, 22, 31, 0.75); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 14px; }}"
        )
        ec_layout = QVBoxLayout(editor_card)
        ec_layout.setContentsMargins(16, 14, 16, 14)
        ec_layout.setSpacing(10)

        editor_header = QHBoxLayout()
        eh_title = QLabel("Nội Dung Chỉ Thị Hệ Thống:")
        eh_title.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {DesignTokens.TEXT_SECONDARY};")
        
        self.char_count_lbl = QLabel("0 ký tự")
        self.char_count_lbl.setStyleSheet(f"font-size: 11px; color: {DesignTokens.TEXT_MUTED};")
        
        editor_header.addWidget(eh_title)
        editor_header.addStretch()
        editor_header.addWidget(self.char_count_lbl)
        ec_layout.addLayout(editor_header)

        self.txt_rule = QTextEdit()
        self.txt_rule.setPlaceholderText("Nhập câu lệnh hệ thống (System Prompt) của bạn ở đây...")
        initial_rule = self.user_settings.get("system_rule", "Bạn là POP AI Assistant, trợ lý thông minh thân thiện bằng tiếng Việt.")
        self.txt_rule.setPlainText(initial_rule)
        self.txt_rule.setStyleSheet(
            f"QTextEdit {{ background-color: rgba(10, 15, 24, 0.85); border: 1px solid rgba(0, 255, 255, 0.15); "
            f"border-radius: 10px; padding: 14px; color: {DesignTokens.TEXT_MAIN}; font-size: 13px; line-height: 1.6; "
            f"selection-background-color: rgba(0, 255, 170, 0.25); }}"
            f"QTextEdit:focus {{ border-color: {DesignTokens.CYAN}; }}"
        )
        self.txt_rule.textChanged.connect(self._update_char_count)
        ec_layout.addWidget(self.txt_rule, stretch=1)

        layout.addWidget(editor_card, stretch=1)
        self._update_char_count()

        # Bottom Bar
        bottom_bar = QHBoxLayout()
        
        self.status_feedback = QLabel("")
        self.status_feedback.setStyleSheet(f"color: {DesignTokens.CYAN_ACCENT}; font-size: 13px; font-weight: 600;")
        self.status_feedback.hide()
        bottom_bar.addWidget(self.status_feedback)

        bottom_bar.addStretch()

        reset_btn = QPushButton("Khôi Phục Mặc Định")
        reset_btn.setFixedHeight(38)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setStyleSheet(
            f"QPushButton {{ background: {DesignTokens.SURFACE_2}; color: {DesignTokens.TEXT_MUTED}; "
            f"border: 1px solid {DesignTokens.BORDER}; border-radius: 8px; font-size: 12px; font-weight: 500; padding: 0 16px; }}"
            f"QPushButton:hover {{ background: {DesignTokens.SURFACE_3}; border-color: {DesignTokens.BORDER_GLOW}; color: {DesignTokens.TEXT_MAIN}; }}"
        )
        reset_btn.clicked.connect(lambda: self.txt_rule.setPlainText("Bạn là POP AI Assistant, trợ lý thông minh thân thiện bằng tiếng Việt."))
        bottom_bar.addWidget(reset_btn)

        save_rule_btn = QPushButton(" Lưu Quy Tắc")
        save_rule_btn.setIcon(create_vector_icon("check", "#03050B", 16))
        save_rule_btn.setFixedHeight(38)
        save_rule_btn.setFixedWidth(150)
        save_rule_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_rule_btn.setStyleSheet(
            f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #008EFF, stop:1 #00FFAA); "
            f"color: #03050B; font-weight: 700; font-size: 13px; border: none; border-radius: 8px; padding: 0 16px; }}"
            f"QPushButton:hover {{ background: #00FFAA; }}"
            f"QPushButton:pressed {{ background: #00CC88; }}"
        )
        save_rule_btn.clicked.connect(self._save_system_rule)
        bottom_bar.addWidget(save_rule_btn)

        layout.addLayout(bottom_bar)

    def _update_char_count(self):
        cnt = len(self.txt_rule.toPlainText())
        self.char_count_lbl.setText(f"{cnt} ký tự")

    def _save_system_rule(self):
        new_rule = self.txt_rule.toPlainText().strip()
        self.user_settings["system_rule"] = new_rule
        save_user_settings(self.user_settings)
        self.settingsChanged.emit()

        self.status_feedback.setText("Đã lưu quy tắc ngữ cảnh thành công.")
        self.status_feedback.show()
        QTimer.singleShot(2600, lambda: self.status_feedback.hide())
