"""
Chat Header Bar Widget - Header bar of the Chat Area with navigation, settings, and window controls.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QPushButton

from view.ui.styles import DesignTokens
from view.ui.icons import create_vector_icon


class ChatHeaderBarWidget(QFrame):
    """Header bar of the Chat Area with navigation, settings, and window controls."""

    toggleRightPanel = pyqtSignal()
    openSettings = pyqtSignal()
    windowHideToMascot = pyqtSignal()
    windowMinimize = pyqtSignal()
    windowMaximize = pyqtSignal()
    windowClose = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self.setStyleSheet("QFrame { background-color: transparent; border: none; }")
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(10)

        self.panel_btn = QPushButton()
        self.panel_btn.setIcon(create_vector_icon("panel_toggle", DesignTokens.TEXT_SECONDARY, 18))
        self.panel_btn.setFixedSize(32, 32)
        self.panel_btn.setToolTip("Bật/tắt bảng giám sát hệ thống")
        self.panel_btn.setStyleSheet(
            f"QPushButton {{ border: none; background: transparent; padding: 0px; }} "
            f"QPushButton:hover {{ background: rgba(0, 229, 255, 0.1); border-radius: 8px; }}"
        )
        self.panel_btn.clicked.connect(self.toggleRightPanel.emit)

        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(create_vector_icon("settings", DesignTokens.TEXT_SECONDARY, 18))
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.setToolTip("Cài đặt")
        self.settings_btn.setStyleSheet(
            "QPushButton { border: none; background: transparent; padding: 0px; } "
            "QPushButton:hover { background: rgba(255, 255, 255, 0.08); border-radius: 8px; }"
        )
        self.settings_btn.clicked.connect(self.openSettings.emit)

        win_controls = QHBoxLayout()
        win_controls.setSpacing(4)

        btn_style = (
            "QPushButton { border: none; background: transparent; padding: 0px; border-radius: 6px; } "
            "QPushButton:hover { background: rgba(255, 255, 255, 0.08); }"
        )

        # 1. Nút Ẩn xuống Mini Mascot (Hiện linh vật nổi mini)
        self.mascot_btn = QPushButton()
        self.mascot_btn.setIcon(create_vector_icon("mini_mascot", DesignTokens.CYAN_ACCENT, 14))
        self.mascot_btn.setFixedSize(28, 28)
        self.mascot_btn.setToolTip("Ẩn xuống Linh vật Mini Mascot (Chuột phải vào Mascot để mở Gacha & Bộ Sưu Tập)")
        self.mascot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mascot_btn.setStyleSheet(
            "QPushButton { border: none; background: transparent; padding: 0px; border-radius: 6px; } "
            f"QPushButton:hover {{ background: rgba(0, 255, 170, 0.15); }}"
        )
        self.mascot_btn.clicked.connect(self.windowHideToMascot.emit)

        # 2. Nút Thu nhỏ cửa sổ xuống Taskbar
        self.min_btn = QPushButton()
        self.min_btn.setIcon(create_vector_icon("minimize", DesignTokens.TEXT_SECONDARY, 12))
        self.min_btn.setFixedSize(28, 28)
        self.min_btn.setToolTip("Thu nhỏ cửa sổ")
        self.min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.min_btn.setStyleSheet(btn_style)
        self.min_btn.clicked.connect(self.windowMinimize.emit)

        # 3. Nút Phóng to / Thu nhỏ kích thước
        self.max_btn = QPushButton()
        self.max_btn.setIcon(create_vector_icon("maximize", DesignTokens.TEXT_SECONDARY, 12))
        self.max_btn.setFixedSize(28, 28)
        self.max_btn.setToolTip("Phóng to / Khôi phục kích thước")
        self.max_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.max_btn.setStyleSheet(btn_style)
        self.max_btn.clicked.connect(self.windowMaximize.emit)

        # 4. Nút Đóng
        self.close_btn = QPushButton()
        self.close_btn.setIcon(create_vector_icon("close", DesignTokens.CORAL_ACCENT, 12))
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setToolTip("Đóng")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet(
            "QPushButton { border: none; background: transparent; padding: 0px; border-radius: 6px; } "
            "QPushButton:hover { background: rgba(244, 63, 94, 0.22); }"
        )
        self.close_btn.clicked.connect(self.windowClose.emit)

        win_controls.addWidget(self.mascot_btn)
        win_controls.addWidget(self.min_btn)
        win_controls.addWidget(self.max_btn)
        win_controls.addWidget(self.close_btn)

        layout.addStretch()
        layout.addWidget(self.panel_btn)
        layout.addWidget(self.settings_btn)
        layout.addLayout(win_controls)
