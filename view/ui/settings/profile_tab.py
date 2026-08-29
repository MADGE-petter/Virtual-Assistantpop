import os
import json
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTextEdit, QPushButton, QMessageBox
)
from view.ui.styles import DesignTokens


class ProfileTabWidget(QWidget):
    """Tab 5: Hồ Sơ Người Dùng & Bộ Nhớ Cốt Lõi (Core Memory)."""

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
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        # Header
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title = QLabel("Hồ Sơ & Bộ Nhớ Cá Nhân")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {DesignTokens.TEXT_MAIN}; letter-spacing: 0.5px;")
        desc = QLabel("Thông tin người dùng và bộ nhớ cốt lõi (Core Memory) để POP Assistant cá nhân hóa câu trả lời")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        layout.addLayout(title_box)

        # 1. User Card
        prof_card = QFrame()
        prof_card.setStyleSheet(
            f"QFrame {{ background: rgba(14, 20, 36, 0.65); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 12px; padding: 18px; }}"
        )
        pc_layout = QHBoxLayout(prof_card)
        pc_layout.setSpacing(18)

        # Avatar
        avatar_lbl = QLabel(self.username[0].upper() if self.username else "U")
        avatar_lbl.setFixedSize(56, 56)
        avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_lbl.setStyleSheet(
            f"background-color: rgba(255, 255, 255, 0.05); color: {DesignTokens.TEXT_MAIN}; "
            f"font-size: 22px; font-weight: 600; border-radius: 28px; border: 1px solid rgba(255, 255, 255, 0.15);"
        )
        pc_layout.addWidget(avatar_lbl)

        info_box = QVBoxLayout()
        info_box.setSpacing(4)
        
        name_row = QHBoxLayout()
        u_name = QLabel(self.username)
        u_name.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {DesignTokens.TEXT_MAIN};")
        
        role_badge = QLabel("ADMINISTRATOR")
        role_badge.setStyleSheet(
            f"background: rgba(255, 255, 255, 0.08); color: {DesignTokens.TEXT_MUTED}; "
            f"font-size: 10px; font-weight: 600; border-radius: 4px; padding: 2px 8px; letter-spacing: 0.5px;"
        )
        name_row.addWidget(u_name)
        name_row.addWidget(role_badge)
        name_row.addStretch()
        
        u_role = QLabel("Tài khoản cục bộ • Toàn quyền quản trị hệ thống & AI models")
        u_role.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 12px;")

        info_box.addLayout(name_row)
        info_box.addWidget(u_role)

        pc_layout.addLayout(info_box, stretch=1)
        layout.addWidget(prof_card)

        # 2. Core Memory Section
        mem_box = QVBoxLayout()
        mem_box.setSpacing(6)
        
        mem_title = QLabel("Bộ Nhớ Cốt Lõi (Core Memory):")
        mem_title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {DesignTokens.TEXT_MAIN};")
        
        mem_desc = QLabel("Ghi lại thông tin về nghề nghiệp, thói quen, phong cách làm việc của bạn. POP sẽ luôn ghi nhớ các thông tin này trong mọi cuộc trò chuyện:")
        mem_desc.setStyleSheet(f"font-size: 12px; color: {DesignTokens.TEXT_MUTED};")
        mem_desc.setWordWrap(True)

        mem_box.addWidget(mem_title)
        mem_box.addWidget(mem_desc)
        layout.addLayout(mem_box)

        # Text Area for Core Memory
        self.txt_core_memory = QTextEdit()
        self.txt_core_memory.setPlaceholderText("VD: Tôi là lập trình viên Python, thích câu trả lời ngắn gọn, hay làm việc về backend và AI...")
        self.txt_core_memory.setStyleSheet(
            f"QTextEdit {{ background-color: rgba(14, 20, 36, 0.65); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 10px; padding: 14px; color: {DesignTokens.TEXT_MAIN}; font-size: 13px; line-height: 1.5; }}"
            f"QTextEdit:focus {{ border-color: rgba(255, 255, 255, 0.25); }}"
        )
        layout.addWidget(self.txt_core_memory, stretch=1)

        # Bottom Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()

        save_btn = QPushButton("Lưu Bộ Nhớ Cốt Lõi")
        save_btn.setFixedHeight(38)
        save_btn.setFixedWidth(170)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(
            f"QPushButton {{ background-color: rgba(255, 255, 255, 0.05); color: {DesignTokens.TEXT_MAIN}; "
            f"font-weight: 500; font-size: 13px; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; }}"
            f"QPushButton:hover {{ background-color: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); }}"
            f"QPushButton:pressed {{ background-color: rgba(255, 255, 255, 0.02); }}"
        )
        save_btn.clicked.connect(self._save_core_memory)
        bottom_bar.addWidget(save_btn)

        layout.addLayout(bottom_bar)

    def _load_core_memory(self):
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.txt_core_memory.setPlainText(data.get("core_memory", ""))
        except Exception:
            pass

    def _save_core_memory(self):
        try:
            data = {"core_memory": self.txt_core_memory.toPlainText().strip()}
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Thành công", "Đã lưu bộ nhớ cốt lõi (Core Memory) thành công!")
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể lưu bộ nhớ: {e}")
