from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QFrame, QStackedWidget
)

from view.ui.styles import DesignTokens
from view.ui.settings.settings_config import load_user_settings
from view.ui.settings.general_tab import GeneralTabWidget
from view.ui.settings.models_tab import ModelsTabWidget
from view.ui.settings.database_tab import DatabaseTabWidget
from view.ui.settings.rules_tab import RulesTabWidget
from view.ui.settings.profile_tab import ProfileTabWidget
from view.ui.settings.about_tab import AboutTabWidget


class SettingsDialog(QDialog):
    """Trang Quản lý Settings Hợp nhất (Assembled from Modular Tabs)."""
    
    settingsChanged = pyqtSignal()
    modelDownloaded = pyqtSignal()

    def __init__(self, username: str = "Tài khoản", initial_tab: int = 0, parent=None):
        super().__init__(parent)
        self.username = username
        self.user_settings = load_user_settings()
        
        self.setWindowTitle("POP AI - Cài Đặt & Quản Lý Hệ Thống")
        self.setFixedSize(860, 580)
        self.setStyleSheet(f"QDialog {{ background-color: {DesignTokens.BG_BASE}; color: {DesignTokens.TEXT_MAIN}; }}")
        self._setup_ui()
        
        if initial_tab < self.nav_list.count():
            self.nav_list.setCurrentRow(initial_tab)

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # -----------------------------------------------------------
        # LEFT NAVIGATION SIDEBAR (Tabs)
        # -----------------------------------------------------------
        self.nav_sidebar = QFrame()
        self.nav_sidebar.setFixedWidth(210)
        self.nav_sidebar.setStyleSheet(
            f"QFrame {{ background-color: {DesignTokens.SURFACE_1}; border-right: 1px solid {DesignTokens.BORDER}; }}"
        )
        nav_layout = QVBoxLayout(self.nav_sidebar)
        nav_layout.setContentsMargins(12, 20, 12, 20)
        nav_layout.setSpacing(10)

        title_lbl = QLabel("CÀI ĐẶT POP")
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT}; margin-bottom: 10px;")
        nav_layout.addWidget(title_lbl)

        self.nav_list = QListWidget()
        self.nav_list.setStyleSheet(
            f"QListWidget {{ background: transparent; border: none; font-size: 13px; }}"
            f"QListWidget::item {{ padding: 10px 12px; border-radius: 8px; margin-bottom: 4px; color: {DesignTokens.TEXT_MAIN}; }}"
            f"QListWidget::item:hover {{ background: {DesignTokens.SURFACE_2}; color: {DesignTokens.CYAN}; }}"
            f"QListWidget::item:selected {{ background: {DesignTokens.SURFACE_3}; color: {DesignTokens.CYAN_ACCENT}; font-weight: bold; }}"
        )

        nav_items = [
            "⚙️  Cài đặt chung",
            "🧠  Quản lý Models",
            "🗄️  Dữ liệu & File",
            "📜  Quy tắc Ngữ cảnh",
            "👤  Hồ sơ Người dùng",
            "🖥️  Thông số Máy"
        ]
        for item in nav_items:
            self.nav_list.addItem(QListWidgetItem(item))

        self.nav_list.currentRowChanged.connect(self._on_tab_changed)
        nav_layout.addWidget(self.nav_list, stretch=1)

        main_layout.addWidget(self.nav_sidebar)

        # -----------------------------------------------------------
        # RIGHT STACKED WIDGET (Modular Tab Pages)
        # -----------------------------------------------------------
        self.stacked_widget = QStackedWidget()
        
        self.general_tab = GeneralTabWidget(self.user_settings)
        self.models_tab = ModelsTabWidget(self.user_settings)
        self.models_tab.modelDownloaded.connect(lambda: self.modelDownloaded.emit())
        self.database_tab = DatabaseTabWidget()
        self.rules_tab = RulesTabWidget(self.user_settings)
        self.rules_tab.settingsChanged.connect(lambda: self.settingsChanged.emit())
        self.profile_tab = ProfileTabWidget(self.username)
        self.about_tab = AboutTabWidget(self.user_settings)

        self.stacked_widget.addWidget(self.general_tab)
        self.stacked_widget.addWidget(self.models_tab)
        self.stacked_widget.addWidget(self.database_tab)
        self.stacked_widget.addWidget(self.rules_tab)
        self.stacked_widget.addWidget(self.profile_tab)
        self.stacked_widget.addWidget(self.about_tab)

        main_layout.addWidget(self.stacked_widget, stretch=1)

    def _on_tab_changed(self, index: int):
        self.stacked_widget.setCurrentIndex(index)
        if index == 1:
            self.models_tab.reload_local_models()
        elif index == 5:
            self.about_tab.update_system_telemetry()
