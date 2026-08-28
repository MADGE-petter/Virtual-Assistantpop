from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QFrame, QStackedWidget, QPushButton
)

from view.ui.styles import DesignTokens
from view.ui.icons import get_pop_logo_pixmap
from view.ui.settings.settings_config import load_user_settings
from view.ui.settings.general_tab import GeneralTabWidget
from view.ui.settings.models_tab import ModelsTabWidget
from view.ui.settings.download_tab import DownloadTabWidget
from view.ui.settings.database_tab import DatabaseTabWidget
from view.ui.settings.rules_tab import RulesTabWidget
from view.ui.settings.profile_tab import ProfileTabWidget
from view.ui.settings.about_tab import AboutTabWidget


class SettingsWidget(QWidget):
    """Trang Cài đặt & Quản lý nhúng trực tiếp trong cửa sổ PopView (In-Window View Switch)."""
    
    backToChatRequested = pyqtSignal()
    settingsChanged = pyqtSignal()
    modelDownloaded = pyqtSignal()

    def __init__(self, username: str = "Tài khoản", initial_tab: int = 0, parent=None):
        super().__init__(parent)
        self.username = username
        self.user_settings = load_user_settings()
        self._setup_ui()
        self.open_tab(initial_tab)

    def open_tab(self, index: int):
        if 0 <= index < self.nav_list.count():
            self.nav_list.setCurrentRow(index)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # -----------------------------------------------------------
        # TOP HEADER BAR WITH BACK TO CHAT BUTTON
        # -----------------------------------------------------------
        header_bar = QFrame()
        header_bar.setFixedHeight(54)
        header_bar.setStyleSheet(
            f"QFrame {{ background: rgba(15, 22, 38, 0.7); border-bottom: 1px solid {DesignTokens.BORDER}; }}"
        )
        hb_layout = QHBoxLayout(header_bar)
        hb_layout.setContentsMargins(16, 0, 16, 0)
        hb_layout.setSpacing(12)

        # Back Button to return to Chat View
        self.back_btn = QPushButton("←  Quay lại Chat")
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setStyleSheet(
            f"QPushButton {{ background: {DesignTokens.SURFACE_2}; color: {DesignTokens.CYAN_ACCENT}; font-size: 13px; "
            f"font-weight: bold; border: 1px solid {DesignTokens.BORDER}; border-radius: 8px; padding: 6px 14px; }}"
            f"QPushButton:hover {{ background: {DesignTokens.SURFACE_3}; border-color: {DesignTokens.CYAN}; }}"
        )
        self.back_btn.clicked.connect(lambda: self.backToChatRequested.emit())
        hb_layout.addWidget(self.back_btn)

        logo_lbl = QLabel()
        logo_lbl.setPixmap(get_pop_logo_pixmap(22))
        hb_layout.addWidget(logo_lbl)

        win_title = QLabel("CÀI ĐẶT & QUẢN LÝ HỆ THỐNG")
        win_title.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {DesignTokens.TEXT_MAIN}; letter-spacing: 1px;")
        hb_layout.addWidget(win_title, stretch=1)

        main_layout.addWidget(header_bar)

        # -----------------------------------------------------------
        # BODY LAYOUT (Left Tab List + Right Stacked Pages)
        # -----------------------------------------------------------
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Left Nav Sidebar
        self.nav_sidebar = QFrame()
        self.nav_sidebar.setFixedWidth(210)
        self.nav_sidebar.setStyleSheet(
            f"QFrame {{ background-color: rgba(8, 12, 22, 0.6); border-right: 1px solid {DesignTokens.BORDER}; }}"
        )
        nav_layout = QVBoxLayout(self.nav_sidebar)
        nav_layout.setContentsMargins(12, 16, 12, 16)
        nav_layout.setSpacing(8)

        self.nav_list = QListWidget()
        self.nav_list.setStyleSheet(
            f"QListWidget {{ background: transparent; border: none; font-size: 13px; outline: none; }}"
            f"QListWidget::item {{ padding: 11px 14px; border-radius: 10px; margin-bottom: 4px; color: {DesignTokens.TEXT_MAIN}; }}"
            f"QListWidget::item:hover {{ background: rgba(0, 255, 170, 0.08); color: {DesignTokens.CYAN}; }}"
            f"QListWidget::item:selected {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 255, 170, 0.2), stop:1 rgba(0, 142, 255, 0.2)); "
            f"color: {DesignTokens.CYAN_ACCENT}; font-weight: bold; border-left: 3px solid {DesignTokens.CYAN_ACCENT}; }}"
        )

        nav_items = [
            "Cài đặt chung",
            "Quản lý Models",
            "Tải & Tìm kiếm Model",
            "Dữ liệu & Files",
            "Quy tắc Ngữ cảnh",
            "Hồ sơ người dùng",
            "Thông số máy"
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
        main_layout.addLayout(body_layout, stretch=1)

    def _on_tab_changed(self, index: int):
        self.stacked_widget.setCurrentIndex(index)
        if index == 1:
            self.models_tab.reload_local_models()
        elif index == 6:
            self.about_tab.update_system_telemetry()
