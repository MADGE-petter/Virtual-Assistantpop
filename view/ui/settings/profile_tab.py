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
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Center container
        center_container = QFrame()
        center_container.setFixedWidth(560)
        
        layout = QVBoxLayout(center_container)
        layout.setContentsMargins(20, 40, 20, 40)
        layout.setSpacing(16)

        # Avatar - Centered
        avatar_box = QHBoxLayout()
        avatar_lbl = QLabel(self.username[0].upper() if self.username else "U")
        avatar_lbl.setFixedSize(72, 72)
        avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_lbl.setStyleSheet(
            f"background-color: rgba(0, 142, 255, 0.08); color: {DesignTokens.TEXT_PRIMARY}; "
            f"font-size: 28px; font-weight: 600; border-radius: 36px; border: 1px solid {DesignTokens.BORDER_GLOW};"
        )
        avatar_box.addStretch()
        avatar_box.addWidget(avatar_lbl)
        avatar_box.addStretch()
        layout.addLayout(avatar_box)

        # User Info - Centered
        info_box = QVBoxLayout()
        info_box.setSpacing(6)
        
        u_name = QLabel(self.username)
        u_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        u_name.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {DesignTokens.TEXT_MAIN};")
        
        role_row = QHBoxLayout()
        role_badge = QLabel("ADMINISTRATOR")
        role_badge.setStyleSheet(
            f"background: rgba(0, 255, 170, 0.12); color: {DesignTokens.CYAN_ACCENT}; "
            f"font-size: 11px; font-weight: 600; border-radius: 4px; padding: 3px 10px; letter-spacing: 0.5px; border: 1px solid rgba(0, 255, 170, 0.2);"
        )
        role_row.addStretch()
        role_row.addWidget(role_badge)
        role_row.addStretch()

        info_box.addWidget(u_name)
        info_box.addLayout(role_row)
        
        layout.addLayout(info_box)
        layout.addSpacing(16)

        # Core Memory Section
        mem_title = QLabel("Bộ Nhớ Cốt Lõi (Core Memory)")
        mem_title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {DesignTokens.TEXT_SECONDARY};")
        
        mem_desc = QLabel("Ghi lại thông tin về nghề nghiệp, thói quen, phong cách làm việc của bạn. POP sẽ luôn ghi nhớ các thông tin này trong mọi cuộc trò chuyện.")
        mem_desc.setStyleSheet(f"font-size: 12px; color: {DesignTokens.TEXT_MUTED};")
        mem_desc.setWordWrap(True)

        layout.addWidget(mem_title)
        layout.addWidget(mem_desc)

        # Text Area for Core Memory
        self.txt_core_memory = QTextEdit()
        self.txt_core_memory.setPlaceholderText("VD: Tôi là lập trình viên Python, thích câu trả lời ngắn gọn, hay làm việc về backend và AI...")
        self.txt_core_memory.setStyleSheet(
            f"QTextEdit {{ background-color: rgba(14, 20, 36, 0.65); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 10px; padding: 14px; color: {DesignTokens.TEXT_MAIN}; font-size: 13px; line-height: 1.5; }}"
            f"QTextEdit:focus {{ border-color: {DesignTokens.CYAN}; }}"
        )
        layout.addWidget(self.txt_core_memory, stretch=1)

        # Bottom Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()

        save_btn = QPushButton("Lưu Thay Đổi")
        save_btn.setFixedHeight(40)
        save_btn.setFixedWidth(140)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(
            f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #008EFF, stop:1 #00FFAA); "
            f"color: #03050B; font-weight: 700; font-size: 13px; border: none; border-radius: 8px; }}"
            f"QPushButton:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00A6FF, stop:1 #33FFBC); }}"
            f"QPushButton:pressed {{ background: #008EFF; }}"
        )
        save_btn.clicked.connect(self._save_core_memory)
        bottom_bar.addWidget(save_btn)

        layout.addLayout(bottom_bar)
        
        main_layout.addStretch()
        main_layout.addWidget(center_container)
        main_layout.addStretch()

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
