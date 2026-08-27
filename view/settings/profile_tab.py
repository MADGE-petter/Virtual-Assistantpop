from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from view.ui.styles import DesignTokens


class ProfileTabWidget(QWidget):
    """Tab 5: Hồ Sơ Người Dùng."""

    def __init__(self, username: str = "Tài khoản", parent=None):
        super().__init__(parent)
        self.username = username
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Hồ Sơ Người Dùng")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT};")
        layout.addWidget(title)

        prof_card = QFrame()
        prof_card.setStyleSheet(f"QFrame {{ background: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; border-radius: 12px; padding: 20px; }}")
        pc_layout = QHBoxLayout(prof_card)
        pc_layout.setSpacing(20)

        avatar_lbl = QLabel(self.username[0].upper() if self.username else "U")
        avatar_lbl.setFixedSize(60, 60)
        avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_lbl.setStyleSheet(f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #008EFF, stop:1 #00FFAA); color: black; font-size: 26px; font-weight: bold; border-radius: 30px;")
        pc_layout.addWidget(avatar_lbl)

        info_box = QVBoxLayout()
        info_box.setSpacing(4)
        u_name = QLabel(f"<b>Tên tài khoản:</b> {self.username}")
        u_name.setStyleSheet("font-size: 14px;")
        u_role = QLabel("Quyền hạn: Administrator • Local Desktop User")
        u_role.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 12px;")
        info_box.addWidget(u_name)
        info_box.addWidget(u_role)

        pc_layout.addLayout(info_box, stretch=1)
        layout.addWidget(prof_card)

        layout.addStretch()
