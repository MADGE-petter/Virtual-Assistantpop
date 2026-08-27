from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QMouseEvent, QColor
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QFrame, QStackedWidget, QPushButton, QGraphicsDropShadowEffect, QWidget
)

from view.ui.styles import DesignTokens
from view.ui.icons import get_pop_logo_pixmap
from view.ui.widgets.starfield_widget import StarfieldWidget
from view.ui.settings.settings_config import load_user_settings
from view.ui.settings.general_tab import GeneralTabWidget
from view.ui.settings.models_tab import ModelsTabWidget
from view.ui.settings.download_tab import DownloadTabWidget
from view.ui.settings.database_tab import DatabaseTabWidget
from view.ui.settings.rules_tab import RulesTabWidget
from view.ui.settings.profile_tab import ProfileTabWidget
from view.ui.settings.about_tab import AboutTabWidget


class SettingsDialog(QDialog):
    """Trang Quản lý Settings Hợp nhất kế thừa 100% phong cách POP UI (Starfield, Glassmorphism, Frameless Window)."""
    
    settingsChanged = pyqtSignal()
    modelDownloaded = pyqtSignal()

    def __init__(self, username: str = "Tài khoản", initial_tab: int = 0, parent=None):
        super().__init__(parent)
        self.username = username
        self.user_settings = load_user_settings()
        self._drag_pos = QPoint()

        # Frameless & Translucent window setup matching POP UI
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(920, 630)

        self._setup_ui()
        
        if initial_tab < self.nav_list.count():
            self.nav_list.setCurrentRow(initial_tab)

    def _setup_ui(self):
        # Base Layout holding Starfield Background & Glass Container
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(12, 12, 12, 12)

        # 1. Starfield Background Widget
        self.starfield = StarfieldWidget(self)
        self.starfield.setGeometry(0, 0, 920, 630)
        self.starfield.lower()

        # 2. Glassmorphic Central Container
        self.container_box = QFrame()
        self.container_box.setStyleSheet(
            f"QFrame#container_box {{"
            f"  background-color: rgba(10, 14, 26, 0.90);"
            f"  border: 1px solid rgba(0, 255, 170, 0.25);"
            f"  border-radius: 16px;"
            f"}}"
        )
        self.container_box.setObjectName("container_box")

        # Glowing Cyan Shadow Effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setColor(QColor(0, 255, 170, 45))
        shadow.setOffset(0, 6)
        self.container_box.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(self.container_box)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # -----------------------------------------------------------
        # TOP DRAGGABLE HEADER BAR
        # -----------------------------------------------------------
        header_bar = QFrame()
        header_bar.setFixedHeight(48)
        header_bar.setStyleSheet(
            f"QFrame {{ background: rgba(15, 22, 38, 0.6); border-top-left-radius: 16px; border-top-right-radius: 16px; "
            f"border-bottom: 1px solid {DesignTokens.BORDER}; }}"
        )
        hb_layout = QHBoxLayout(header_bar)
        hb_layout.setContentsMargins(16, 0, 16, 0)

        logo_lbl = QLabel()
        logo_lbl.setPixmap(get_pop_logo_pixmap(24))
        hb_layout.addWidget(logo_lbl)

        win_title = QLabel("POP AI — CÀI ĐẶT & QUẢN LÝ HỆ THỐNG")
        win_title.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT}; letter-spacing: 1px;")
        hb_layout.addWidget(win_title, stretch=1)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {DesignTokens.TEXT_MUTED}; font-size: 14px; border: none; border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: rgba(255, 75, 110, 0.25); color: #FF4B6E; }}"
        )
        close_btn.clicked.connect(self.close)
        hb_layout.addWidget(close_btn)

        container_layout.addWidget(header_bar)

        # -----------------------------------------------------------
        # BODY LAYOUT (Left Nav + Right Pages)
        # -----------------------------------------------------------
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Left Nav Sidebar
        self.nav_sidebar = QFrame()
        self.nav_sidebar.setFixedWidth(220)
        self.nav_sidebar.setStyleSheet(
            f"QFrame {{ background-color: rgba(8, 12, 22, 0.7); border-right: 1px solid {DesignTokens.BORDER}; border-bottom-left-radius: 16px; }}"
        )
        nav_layout = QVBoxLayout(self.nav_sidebar)
        nav_layout.setContentsMargins(12, 16, 12, 16)
        nav_layout.setSpacing(8)

        self.nav_list = QListWidget()
        self.nav_list.setStyleSheet(
            f"QListWidget {{ background: transparent; border: none; font-size: 13px; outline: none; }}"
            f"QListWidget::item {{ padding: 11px 14px; border-radius: 10px; margin-bottom: 5px; color: {DesignTokens.TEXT_MAIN}; }}"
            f"QListWidget::item:hover {{ background: rgba(0, 255, 170, 0.08); color: {DesignTokens.CYAN}; }}"
            f"QListWidget::item:selected {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 255, 170, 0.2), stop:1 rgba(0, 142, 255, 0.2)); "
            f"color: {DesignTokens.CYAN_ACCENT}; font-weight: bold; border-left: 3px solid {DesignTokens.CYAN_ACCENT}; }}"
        )

        nav_items = [
            "⚙️  Cài đặt chung",
            "🧠  Quản lý Models",
            "📥  Tải & Tìm kiếm Model",
            "🗄️  Dữ liệu & File",
            "📜  Quy tắc Ngữ cảnh",
            "👤  Hồ sơ Người dùng",
            "🖥️  Thông số Máy"
        ]
        for item in nav_items:
            self.nav_list.addItem(QListWidgetItem(item))

        self.nav_list.currentRowChanged.connect(self._on_tab_changed)
        nav_layout.addWidget(self.nav_list, stretch=1)

        body_layout.addWidget(self.nav_sidebar)

        # Right Stacked Pages
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("QStackedWidget { background: transparent; }")
        
        self.general_tab = GeneralTabWidget(self.user_settings)
        self.models_tab = ModelsTabWidget(self.user_settings)
        self.models_tab.modelDownloaded.connect(lambda: self.modelDownloaded.emit())
        self.models_tab.requestOpenDownloadTab.connect(lambda: self.nav_list.setCurrentRow(2))

        self.download_tab = DownloadTabWidget(self.user_settings)
        self.download_tab.modelDownloaded.connect(lambda: (self.modelDownloaded.emit(), self.models_tab.reload_local_models()))

        self.database_tab = DatabaseTabWidget()
        self.rules_tab = RulesTabWidget(self.user_settings)
        self.rules_tab.settingsChanged.connect(lambda: self.settingsChanged.emit())
        self.profile_tab = ProfileTabWidget(self.username)
        self.about_tab = AboutTabWidget(self.user_settings)

        self.stacked_widget.addWidget(self.general_tab)
        self.stacked_widget.addWidget(self.models_tab)
        self.stacked_widget.addWidget(self.download_tab)
        self.stacked_widget.addWidget(self.database_tab)
        self.stacked_widget.addWidget(self.rules_tab)
        self.stacked_widget.addWidget(self.profile_tab)
        self.stacked_widget.addWidget(self.about_tab)

        body_layout.addWidget(self.stacked_widget, stretch=1)
        container_layout.addLayout(body_layout, stretch=1)

        base_layout.addWidget(self.container_box)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.starfield.setGeometry(0, 0, self.width(), self.height())

    def _on_tab_changed(self, index: int):
        self.stacked_widget.setCurrentIndex(index)
        if index == 1:
            self.models_tab.reload_local_models()
        elif index == 6:
            self.about_tab.update_system_telemetry()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
