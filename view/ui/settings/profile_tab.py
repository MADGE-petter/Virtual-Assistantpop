import os
import json
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTextEdit, QPushButton
)
from view.ui.styles import DesignTokens
from view.ui.icons import create_vector_icon


class ProfileTabWidget(QWidget):
    """Tab 5: Hồ Sơ Người Dùng & Bộ Nhớ Cốt Lõi (Core Memory) phong cách Glassmorphism Cyberpunk."""

    def __init__(self, username: str = "Tài khoản", parent=None):
        super().__init__(parent)
        self.username = username
        self.memory_file = os.path.join(os.getcwd(), "database", "user_memory.json")
        self._ensure_paths()
        self._setup_ui()
        self._load_core_memory()

    def _ensure_paths(self):
        os.makedirs(os.path.join(os.getcwd(), "database"), exist_ok=True)
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump({"core_memory": ""}, f, ensure_ascii=False)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        # Header Title Bar
        title_box = QVBoxLayout()
        title_box.setSpacing(6)

        title_row = QHBoxLayout()
        title = QLabel("Hồ Sơ & Bộ Nhớ Cá Nhân Hóa")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {DesignTokens.TEXT_MAIN}; letter-spacing: 0.5px;")

        badge = QLabel("CORE MEMORY")
        badge.setStyleSheet(
            f"background: rgba(0, 255, 170, 0.12); color: {DesignTokens.CYAN_ACCENT}; font-size: 11px; "
            f"font-weight: 700; border-radius: 4px; padding: 2px 8px; border: 1px solid rgba(0, 255, 170, 0.25);"
        )
        title_row.addWidget(title)
        title_row.addWidget(badge)
        title_row.addStretch()

        desc = QLabel("Quản lý thông tin định danh và bộ nhớ dài hạn giúp POP AI hiểu rõ bạn hơn qua từng phiên làm việc")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 13px;")

        title_box.addLayout(title_row)
        title_box.addWidget(desc)
        layout.addLayout(title_box)

        # Profile Banner Card
        profile_card = QFrame()
        profile_card.setStyleSheet(
            f"QFrame {{ background: rgba(16, 22, 31, 0.75); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 14px; padding: 18px 22px; }}"
        )
        pc_layout = QHBoxLayout(profile_card)
        pc_layout.setContentsMargins(6, 4, 6, 4)
        pc_layout.setSpacing(20)

        # Avatar circle with glowing border
        first_char = self.username[0].upper() if self.username else "U"
        avatar_lbl = QLabel(first_char)
        avatar_lbl.setFixedSize(64, 64)
        avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_lbl.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #008EFF, stop:1 #00FFAA); "
            f"color: #03050B; font-size: 24px; font-weight: 800; border-radius: 32px; border: 2px solid rgba(0, 255, 255, 0.5);"
        )
        pc_layout.addWidget(avatar_lbl)

        # User info
        info_box = QVBoxLayout()
        info_box.setSpacing(6)

        u_name = QLabel(self.username)
        u_name.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {DesignTokens.TEXT_MAIN};")

        badges_row = QHBoxLayout()
        badges_row.setSpacing(8)

        role_badge = QLabel("ADMINISTRATOR")
        role_badge.setStyleSheet(
            f"background: rgba(0, 255, 170, 0.12); color: {DesignTokens.CYAN_ACCENT}; "
            f"font-size: 11px; font-weight: 700; border-radius: 4px; padding: 3px 10px; border: 1px solid rgba(0, 255, 170, 0.25);"
        )

        status_badge = QLabel("● ONLINE")
        status_badge.setStyleSheet(
            f"background: rgba(0, 142, 255, 0.12); color: {DesignTokens.BLUE_ACCENT}; "
            f"font-size: 11px; font-weight: 700; border-radius: 4px; padding: 3px 10px; border: 1px solid rgba(0, 142, 255, 0.25);"
        )

        badges_row.addWidget(role_badge)
        badges_row.addWidget(status_badge)
        badges_row.addStretch()

        info_box.addWidget(u_name)
        info_box.addLayout(badges_row)
        pc_layout.addLayout(info_box, stretch=1)

        layout.addWidget(profile_card)

        # Core Memory Editor Card
        mem_card = QFrame()
        mem_card.setStyleSheet(
            f"QFrame {{ background: rgba(16, 22, 31, 0.75); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 14px; }}"
        )
        mc_layout = QVBoxLayout(mem_card)
        mc_layout.setContentsMargins(18, 16, 18, 16)
        mc_layout.setSpacing(10)

        mem_header = QHBoxLayout()
        mem_title = QLabel("Bộ Nhớ Cốt Lõi (Core Memory)")
        mem_title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {DesignTokens.TEXT_SECONDARY};")
        
        self.char_count_lbl = QLabel("0 ký tự")
        self.char_count_lbl.setStyleSheet(f"font-size: 11px; color: {DesignTokens.TEXT_MUTED};")

        mem_header.addWidget(mem_title)
        mem_header.addStretch()
        mem_header.addWidget(self.char_count_lbl)
        mc_layout.addLayout(mem_header)

        mem_desc = QLabel(
            "Ghi lại sở thích, nghề nghiệp, phong cách trả lời hoặc các sự thật quan trọng về bạn. "
            "POP sẽ tự động áp dụng thông tin này làm ngữ cảnh ưu tiên cao trong mọi cuộc trò chuyện."
        )
        mem_desc.setStyleSheet(f"font-size: 12px; color: {DesignTokens.TEXT_MUTED}; line-height: 1.4;")
        mem_desc.setWordWrap(True)
        mc_layout.addWidget(mem_desc)

        # Text Area for Core Memory
        self.txt_core_memory = QTextEdit()
        self.txt_core_memory.setPlaceholderText(
            "VD: Tôi là lập trình viên Python và Fullstack, thích câu trả lời ngắn gọn, có ví dụ code trực quan, hay dùng hệ điều hành Windows..."
        )
        self.txt_core_memory.setStyleSheet(
            f"QTextEdit {{ background-color: rgba(10, 15, 24, 0.85); border: 1px solid rgba(0, 255, 255, 0.15); "
            f"border-radius: 10px; padding: 14px; color: {DesignTokens.TEXT_MAIN}; font-size: 13px; line-height: 1.6; }}"
            f"QTextEdit:focus {{ border-color: {DesignTokens.CYAN}; }}"
        )
        self.txt_core_memory.textChanged.connect(self._update_char_count)
        mc_layout.addWidget(self.txt_core_memory, stretch=1)

        layout.addWidget(mem_card, stretch=1)

        # Bottom Bar
        bottom_bar = QHBoxLayout()
        
        self.status_feedback = QLabel("")
        self.status_feedback.setStyleSheet(f"color: {DesignTokens.CYAN_ACCENT}; font-size: 13px; font-weight: 600;")
        self.status_feedback.hide()
        bottom_bar.addWidget(self.status_feedback)

        bottom_bar.addStretch()

        save_btn = QPushButton(" Lưu Hồ Sơ & Bộ Nhớ")
        save_btn.setIcon(create_vector_icon("check", "#03050B", 16))
        save_btn.setFixedHeight(38)
        save_btn.setFixedWidth(180)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(
            f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #008EFF, stop:1 #00FFAA); "
            f"color: #03050B; font-weight: 700; font-size: 13px; border: none; border-radius: 8px; padding: 0 16px; }}"
            f"QPushButton:hover {{ background: #00FFAA; }}"
            f"QPushButton:pressed {{ background: #00CC88; }}"
        )
        save_btn.clicked.connect(self._save_core_memory)
        bottom_bar.addWidget(save_btn)

        layout.addLayout(bottom_bar)

    def _update_char_count(self):
        cnt = len(self.txt_core_memory.toPlainText())
        self.char_count_lbl.setText(f"{cnt} ký tự")

    def _load_core_memory(self):
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.txt_core_memory.setPlainText(data.get("core_memory", ""))
                    self._update_char_count()
        except Exception:
            pass

    def _save_core_memory(self):
        try:
            data = {}
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    try: data = json.load(f)
                    except: data = {}
            data["core_memory"] = self.txt_core_memory.toPlainText().strip()
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.status_feedback.setText("Đã lưu bộ nhớ cốt lõi thành công.")
            self.status_feedback.show()
            QTimer.singleShot(2600, lambda: self.status_feedback.hide())
        except Exception as e:
            self.status_feedback.setText(f"Lỗi: {e}")
            self.status_feedback.show()
