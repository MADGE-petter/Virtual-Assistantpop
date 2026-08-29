from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from view.ui.styles import DesignTokens


class ProfileTabWidget(QWidget):
    """Tab 5: Hồ Sơ Người Dùng thiết kế hiện đại, cao cấp."""

    def __init__(self, username: str = "Tài khoản", parent=None):
        super().__init__(parent)
        self.username = username
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        # Header
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title = QLabel("Hồ Sơ Người Dùng")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {DesignTokens.TEXT_MAIN}; letter-spacing: 0.5px;")
        desc = QLabel("Thông tin tài khoản cá nhân và phân quyền bảo mật trên thiết bị này")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        layout.addLayout(title_box)

        # User Card
        prof_card = QFrame()
        prof_card.setStyleSheet(
            f"QFrame {{ background: rgba(14, 20, 36, 0.65); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 14px; padding: 24px; }}"
        )
        pc_layout = QHBoxLayout(prof_card)
        pc_layout.setSpacing(22)

        # Avatar
        avatar_lbl = QLabel(self.username[0].upper() if self.username else "U")
        avatar_lbl.setFixedSize(68, 68)
        avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_lbl.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00FFAA, stop:1 #008EFF); "
            f"color: #03050B; font-size: 28px; font-weight: 800; border-radius: 34px; border: 2px solid rgba(0, 255, 170, 0.4);"
        )
        pc_layout.addWidget(avatar_lbl)

        info_box = QVBoxLayout()
        info_box.setSpacing(5)
        
        name_row = QHBoxLayout()
        u_name = QLabel(self.username)
        u_name.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {DesignTokens.TEXT_MAIN};")
        
        role_badge = QLabel("ADMINISTRATOR")
        role_badge.setStyleSheet(
            f"background: rgba(0, 255, 170, 0.15); color: {DesignTokens.CYAN_ACCENT}; "
            f"font-size: 10px; font-weight: 700; border-radius: 4px; padding: 3px 8px; letter-spacing: 0.5px;"
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

        layout.addStretch()
