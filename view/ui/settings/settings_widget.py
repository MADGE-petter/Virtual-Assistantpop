from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget
)

from view.ui.settings.settings_config import load_user_settings
from view.ui.settings.general_tab import GeneralTabWidget
from view.ui.settings.models_tab import ModelsTabWidget
from view.ui.settings.download_tab import DownloadTabWidget
from view.ui.settings.database_tab import DatabaseTabWidget
from view.ui.settings.rules_tab import RulesTabWidget
from view.ui.settings.profile_tab import ProfileTabWidget
from view.ui.settings.about_tab import AboutTabWidget


class SettingsWidget(QWidget):
    """Nội dung Trang Cài đặt & Quản lý nhúng trực tiếp ở khung trung tâm PopView (Không chứa Sidebar kép)."""
    
    settingsChanged = pyqtSignal()
    modelDownloaded = pyqtSignal()
    requestOpenDownloadTab = pyqtSignal()

    def __init__(self, username: str = "Tài khoản", initial_tab: int = 0, parent=None):
        super().__init__(parent)
        self.username = username
        self.user_settings = load_user_settings()
        self._setup_ui()
        self.open_tab(initial_tab)

    def open_tab(self, index: int):
        if 0 <= index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index)
            if index == 1:
                self.models_tab.reload_local_models()
            elif index == 6:
                self.about_tab.update_system_telemetry()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main Stacked Widget holding all 7 Settings Tab Pages
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("QStackedWidget { background: transparent; }")
        
        self.general_tab = GeneralTabWidget(self.user_settings)
        self.models_tab = ModelsTabWidget(self.user_settings)
        self.models_tab.modelDownloaded.connect(lambda: self.modelDownloaded.emit())
        self.models_tab.requestOpenDownloadTab.connect(lambda: self.requestOpenDownloadTab.emit())

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

        main_layout.addWidget(self.stacked_widget, stretch=1)
