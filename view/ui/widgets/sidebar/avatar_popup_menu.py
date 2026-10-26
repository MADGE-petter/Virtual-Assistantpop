"""
POP Sidebar - Avatar Popup Menu Component.
"""

from PyQt6.QtCore import (
    Qt, pyqtSignal, QSize, QPoint, QPropertyAnimation, QEasingCurve,
    QParallelAnimationGroup, QEvent
)
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFrame,
    QGraphicsDropShadowEffect
)

from view.ui.styles import DesignTokens
from view.ui.icons import create_vector_icon


class AvatarPopupMenu(QWidget):
    """Menu Popup người dùng màu đen tuyền không viền chữ trắng, tự đóng khi click ra ngoài."""

    profileClicked = pyqtSignal()
    settingsClicked = pyqtSignal()
    modelsClicked = pyqtSignal()
    logoutClicked = pyqtSignal()
    menuClosed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(260, 185)
        self._setup_ui()

    def closeEvent(self, a0):
        self.menuClosed.emit()
        super().closeEvent(a0)

    def changeEvent(self, a0):
        if a0 and a0.type() == QEvent.Type.ActivationChange and not self.isActiveWindow():
            self.close()
        super().changeEvent(a0)

    def _setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(6, 6, 6, 6)

        container = QFrame()
        container.setStyleSheet(
            f"QFrame {{"
            f"  background-color: #000000;"
            f"  border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT};"
            f"  border-radius: 12px;"
            f"}}"
        )
        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)

        def _create_btn(text: str, handler, icon_type: str | None = None, color: str = "#FFFFFF"):
            btn = QPushButton("  " + text)
            if icon_type:
                btn.setIcon(create_vector_icon(icon_type, color, 16))
                btn.setIconSize(QSize(16, 16))
            btn.setFixedHeight(34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                f"QPushButton {{"
                f"  background: transparent;"
                f"  color: {color};"
                f"  font-size: 13px;"
                f"  font-weight: 600;"
                f"  text-align: left;"
                f"  padding-left: 14px;"
                f"  border: none;"
                f"  border-radius: 8px;"
                f"}}"
                f"QPushButton:hover {{"
                f"  background: rgba(255, 255, 255, 0.12);"
                f"}}"
            )
            btn.clicked.connect(lambda: [self.close(), handler()])
            return btn

        btn_prof = _create_btn("Hồ sơ & Bộ nhớ", self.profileClicked.emit, "user")
        btn_set = _create_btn("Cài đặt chung", self.settingsClicked.emit, "settings")
        btn_mod = _create_btn("Quản lý Models", self.modelsClicked.emit, "box")

        btn_sep = QFrame()
        btn_sep.setFrameShape(QFrame.Shape.HLine)
        btn_sep.setStyleSheet("background-color: rgba(255, 255, 255, 0.12); max-height: 1px; margin: 2px 4px; border: none;")

        btn_out = _create_btn("Đăng xuất", self.logoutClicked.emit, "exit", "#FF4B6E")
        btn_out.setStyleSheet(
            f"QPushButton {{"
            f"  background: transparent;"
            f"  color: #FF4B6E;"
            f"  font-size: 13px;"
            f"  font-weight: 600;"
            f"  text-align: left;"
            f"  padding-left: 14px;"
            f"  border: none;"
            f"  border-radius: 8px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: rgba(255, 75, 110, 0.25);"
            f"}}"
        )

        layout.addWidget(btn_prof)
        layout.addWidget(btn_set)
        layout.addWidget(btn_mod)
        layout.addWidget(btn_sep)
        layout.addWidget(btn_out)

        root_layout.addWidget(container)

    def show_animated(self, target_pos: QPoint):
        start_pos = QPoint(target_pos.x(), target_pos.y() + 8)
        self.setWindowOpacity(0.0)
        self.move(start_pos)
        self.show()
        self.raise_()

        self._anim_group = QParallelAnimationGroup(self)

        pos_anim = QPropertyAnimation(self, b"pos")
        pos_anim.setDuration(160)
        pos_anim.setStartValue(start_pos)
        pos_anim.setEndValue(target_pos)
        pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        op_anim = QPropertyAnimation(self, b"windowOpacity")
        op_anim.setDuration(160)
        op_anim.setStartValue(0.0)
        op_anim.setEndValue(1.0)
        op_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._anim_group.addAnimation(pos_anim)
        self._anim_group.addAnimation(op_anim)
        self._anim_group.start()
