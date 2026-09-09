from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QTimer
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame
)
from view.ui.styles import DesignTokens
from view.ui.icons import create_vector_icon
from view.ui.settings.settings_config import save_user_settings


class ToggleSwitch(QWidget):
    """Modern iOS/Windows 11 style animated toggle switch widget."""
    toggled = pyqtSignal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self.setFixedSize(46, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        if self._checked != checked:
            self._checked = checked
            self.toggled.emit(self._checked)
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        r = h / 2.0

        # Background Track
        if self._checked:
            track_color = QColor(0, 255, 170)  # Cyan / Emerald accent
            border_color = QColor(0, 255, 170)
        else:
            track_color = QColor(25, 34, 48)
            border_color = QColor(45, 58, 78)

        painter.setBrush(QBrush(track_color))
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), r, r)

        # Thumb (circle slider)
        thumb_radius = r - 3.5
        thumb_y = r
        thumb_x = (w - r) if self._checked else r
        thumb_color = QColor(3, 5, 11) if self._checked else QColor(180, 200, 220)

        painter.setBrush(QBrush(thumb_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(thumb_x - thumb_radius, thumb_y - thumb_radius, thumb_radius * 2, thumb_radius * 2))


class GeneralTabWidget(QWidget):
    """Tab 1: Cài đặt chung phong cách Glassmorphism Cyberpunk thanh lịch, màu sắc hài hòa."""

    def __init__(self, user_settings: dict, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # Header Title Bar
        title_box = QVBoxLayout()
        title_box.setSpacing(6)

        title_row = QHBoxLayout()
        title = QLabel("Cài Đặt Chung")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {DesignTokens.TEXT_MAIN}; letter-spacing: 0.5px;")
        
        badge = QLabel("HỆ THỐNG")
        badge.setStyleSheet(
            f"background: rgba(0, 255, 170, 0.12); color: {DesignTokens.CYAN_ACCENT}; font-size: 11px; "
            f"font-weight: 700; border-radius: 4px; padding: 2px 8px; border: 1px solid rgba(0, 255, 170, 0.25);"
        )
        title_row.addWidget(title)
        title_row.addWidget(badge)
        title_row.addStretch()

        desc = QLabel("Tùy chỉnh hành vi khởi động, giao diện linh vật và phản hồi giọng nói của trợ lý POP")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 13px;")

        title_box.addLayout(title_row)
        title_box.addWidget(desc)
        layout.addLayout(title_box)

        # Settings Card Container (Glassmorphism card)
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: rgba(16, 22, 31, 0.75); border: 1px solid rgba(255, 255, 255, 0.08); "
            f"border-radius: 14px; }}"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 18, 22, 18)
        card_layout.setSpacing(16)

        # Setting 1: Autostart
        s1 = self._create_setting_row(
            "Khởi động cùng hệ thống",
            "Tự động chạy POP AI ngầm dưới khay hệ thống khi bạn bật máy tính",
            self.user_settings.get("autostart", False)
        )
        self.sw_autostart = s1[1]
        card_layout.addLayout(s1[0])

        card_layout.addWidget(self._create_separator())

        # Setting 2: Mini Mascot Top
        s2 = self._create_setting_row(
            "Ghim Linh vật Mini Mascot",
            "Luôn giữ biểu tượng trợ lý ảo Mini Mascot nổi lơ lửng trên mọi cửa sổ máy tính",
            self.user_settings.get("mascot_top", True)
        )
        self.sw_mascot = s2[1]
        card_layout.addLayout(s2[0])

        card_layout.addWidget(self._create_separator())

        # Setting 3: Voice Feedback
        s3 = self._create_setting_row(
            "Phản hồi bằng Giọng nói (TTS)",
            "POP AI sẽ tự động đọc câu trả lời bằng giọng nói tiếng Việt tự nhiên",
            self.user_settings.get("tts_enabled", True)
        )
        self.sw_tts = s3[1]
        card_layout.addLayout(s3[0])

        layout.addWidget(card)
        layout.addStretch()

        # Bottom Action Bar with In-App Status Notification
        bottom_bar = QHBoxLayout()
        
        self.status_feedback = QLabel("")
        self.status_feedback.setStyleSheet(f"color: {DesignTokens.CYAN_ACCENT}; font-size: 13px; font-weight: 600;")
        self.status_feedback.hide()
        bottom_bar.addWidget(self.status_feedback)

        bottom_bar.addStretch()

        save_btn = QPushButton(" Lưu Thay Đổi")
        save_btn.setIcon(create_vector_icon("check", "#03050B", 16))
        save_btn.setFixedHeight(38)
        save_btn.setFixedWidth(150)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(
            f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #008EFF, stop:1 #00FFAA); "
            f"color: #03050B; font-weight: 700; font-size: 13px; border: none; border-radius: 8px; padding: 0 16px; }}"
            f"QPushButton:hover {{ background: #00FFAA; }}"
            f"QPushButton:pressed {{ background: #00CC88; }}"
        )
        save_btn.clicked.connect(self._save_settings)
        bottom_bar.addWidget(save_btn)

        layout.addLayout(bottom_bar)

    def _create_setting_row(self, title: str, subtitle: str, default_val: bool):
        row = QHBoxLayout()
        row.setSpacing(14)

        text_box = QVBoxLayout()
        text_box.setSpacing(3)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {DesignTokens.TEXT_MAIN};")

        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet(f"font-size: 12px; color: {DesignTokens.TEXT_MUTED};")

        text_box.addWidget(lbl_title)
        text_box.addWidget(lbl_sub)
        row.addLayout(text_box, stretch=1)

        switch = ToggleSwitch(checked=default_val)
        row.addWidget(switch, alignment=Qt.AlignmentFlag.AlignVCenter)

        return row, switch

    def _create_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: rgba(255, 255, 255, 0.06); max-height: 1px;")
        return sep

    def _save_settings(self):
        self.user_settings["autostart"] = self.sw_autostart.isChecked()
        self.user_settings["mascot_top"] = self.sw_mascot.isChecked()
        self.user_settings["tts_enabled"] = self.sw_tts.isChecked()
        save_user_settings(self.user_settings)

        # Elegant in-app feedback pill instead of jarring native QMessageBox
        self.status_feedback.setText("Đã lưu cài đặt chung thành công.")
        self.status_feedback.show()
        QTimer.singleShot(2600, lambda: self.status_feedback.hide())
