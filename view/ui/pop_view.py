import sys
from pathlib import Path

# Ensure workspace root is in sys.path
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame,
    QGraphicsDropShadowEffect, QStackedWidget, QApplication
)

from view.ui.styles import STYLE_SHEET, DesignTokens, init_fonts
from view.ui.widgets import (
    StarfieldWidget, SidebarWidget, ChatAreaWidget,
    RightPanelWidget, MiniMascotWidget
)
from view.ui.settings import SettingsWidget
from view.ui.icons import get_pop_logo_icon
from view.ui.pop_dispatcher import PopDispatcher
from view.ui.pop_window_manager import PopWindowManager
from view.ui.pop_navigation import PopNavigation
from model.pop_chat_model import PopChatModel
from model.voice_state_model import VoiceState


class ResilientStackedWidget(QStackedWidget):
    """StackedWidget with a compact minimum size hint so child pages never force parent layout overflow."""
    def minimumSizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(280, 200)

    def sizeHint(self):
        cur = self.currentWidget()
        if cur:
            return cur.sizeHint()
        from PyQt6.QtCore import QSize
        return QSize(280, 200)


class PopView(QMainWindow):
    """Main Application Window for POP AI Assistant adhering strictly to MVC architecture."""

    # Public Controller Signals
    sendMessage = pyqtSignal(str)
    voiceToggled = pyqtSignal()
    stopGeneration = pyqtSignal()
    newConversation = pyqtSignal()
    switchModel = pyqtSignal(str)
    openSettings = pyqtSignal()
    loadConversation = pyqtSignal(str)
    deleteConversation = pyqtSignal(str)
    viewClosed = pyqtSignal()
    logoutRequested = pyqtSignal()

    def __init__(self, user_name: str = "Tài khoản"):
        super().__init__()
        init_fonts()
        self.controller = None
        self.user_name = user_name

        self.setWindowTitle("POP - AI Assistant")
        self.setWindowIcon(get_pop_logo_icon(32))
        self.resize(1280, 800)
        self.setMinimumSize(960, 600)

        # Frameless dark window style
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Chat Data Model (loaded with user history from SQLite)
        self.chat_model = PopChatModel(self.user_name)

        # Build UI Components
        self._setup_ui()
        self.setStyleSheet(STYLE_SHEET)

        # Subsystem Coordinators (MVC Modularization)
        self.dispatcher = PopDispatcher(self)
        self.window_mgr = PopWindowManager(self, self.mini_mascot, self.starfield)
        self.navigation = PopNavigation(
            self.sidebar, self.center_stack, self.settings_page,
            self.right_panel, self.right_panel_line, self
        )
        self.nav_mgr = self.navigation

        self._bind_dispatcher_signals()
        self._bind_component_events()

        # Load initial session if exists
        active_session = self.chat_model.get_active_session()
        if active_session:
            self.chat_area.load_session(active_session)

    # ============================================================
    # LAYOUT ASSEMBLY
    # ============================================================

    def _setup_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        root_layout = QVBoxLayout(self.central_widget)
        root_layout.setContentsMargins(10, 10, 10, 10)

        self.container_box = QFrame()
        self.container_box.setObjectName("mainContainer")
        self.container_box.setStyleSheet(
            f"QFrame#mainContainer {{ background-color: {DesignTokens.BG_BASE}; border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; border-radius: 16px; }}"
        )
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setColor(Qt.GlobalColor.black)
        shadow.setOffset(0, 4)
        self.container_box.setGraphicsEffect(shadow)

        box_layout = QHBoxLayout(self.container_box)
        box_layout.setContentsMargins(0, 0, 0, 0)
        box_layout.setSpacing(0)

        # 1. Cosmic Canvas
        self.starfield = StarfieldWidget(self.container_box)
        self.starfield.setGeometry(0, 0, 1280, 800)
        self.starfield.lower()

        # 2. Left Sidebar
        self.sidebar = SidebarWidget(self.chat_model, self.user_name, self.container_box)

        # 3. Central Stack (Chat View <-> Settings View)
        self.center_stack = ResilientStackedWidget(self.container_box)
        self.center_stack.setMinimumWidth(0)
        self.center_stack.setStyleSheet("QStackedWidget { background: transparent; }")

        self.chat_area = ChatAreaWidget(self.center_stack, user_name=self.user_name)
        self.settings_page = SettingsWidget(self.user_name, initial_tab=0, parent=self.center_stack)

        self.center_stack.addWidget(self.chat_area)
        self.center_stack.addWidget(self.settings_page)

        # 4. Right Telemetry Panel
        self.right_panel = RightPanelWidget(self.container_box)

        # Subtle Dividers
        self.sidebar_line = QFrame()
        self.sidebar_line.setFixedWidth(1)
        self.sidebar_line.setStyleSheet("background-color: rgba(255, 255, 255, 0.06);")

        self.right_panel_line = QFrame()
        self.right_panel_line.setFixedWidth(1)
        self.right_panel_line.setStyleSheet("background-color: rgba(255, 255, 255, 0.06);")

        box_layout.addWidget(self.sidebar)
        box_layout.addWidget(self.sidebar_line)
        box_layout.addWidget(self.center_stack, stretch=1)
        box_layout.addWidget(self.right_panel_line)
        box_layout.addWidget(self.right_panel)

        root_layout.addWidget(self.container_box)

        # Desktop Floating Mini Mascot
        self.mini_mascot = MiniMascotWidget()
        self.mini_mascot.move(100, 100)
        self.mini_mascot.show()

    # ============================================================
    # EVENT BINDINGS
    # ============================================================

    def _bind_dispatcher_signals(self):
        """Connect cross-thread dispatch signals to main-thread slots."""
        self.dispatcher.botTextSignal.connect(lambda t: self.update_chat(t, sender="bot"))
        self.dispatcher.userTextSignal.connect(self._handle_user_speech_status)
        self.dispatcher.voiceStateSignal.connect(self._handle_voice_state)
        self.dispatcher.toastSignal.connect(self._handle_toast)
        self.dispatcher.alertSignal.connect(lambda d: self._handle_toast(d.get("message", "Cảnh báo"), "warning"))
        self.dispatcher.showWindowSignal.connect(self._handle_show_window)
        self.dispatcher.hideWindowSignal.connect(self.window_mgr.switch_to_mini_mascot)
        self.dispatcher.confirmationCardSignal.connect(self._handle_show_confirmation)
        self.dispatcher.filePreviewSignal.connect(self._handle_show_file_preview)

    def _bind_component_events(self):
        """Wire UI events across sub-widgets and navigation."""
        # Sidebar Events
        self.sidebar.newChatRequested.connect(self._on_new_chat)
        self.sidebar.backToChatRequested.connect(self.navigation.show_chat_view)
        self.sidebar.conversationSelected.connect(self._on_conversation_selected)
        self.sidebar.deleteConversationRequested.connect(lambda sid: self.deleteConversation.emit(sid))
        self.sidebar.settingsClicked.connect(lambda: self.navigation.open_settings_page(0))
        self.sidebar.modelsClicked.connect(lambda: self.navigation.open_settings_page(1))
        self.sidebar.settingsTabSelected.connect(self.navigation.open_settings_page)
        self.sidebar.memoryClicked.connect(lambda: self.navigation.open_settings_page(5))
        self.sidebar.logoutRequested.connect(self._handle_logout_requested)

        # Chat Area Events
        self.chat_area.sendMessage.connect(self._on_user_send_message)
        self.chat_area.stopGeneration.connect(lambda: self.stopGeneration.emit())
        self.chat_area.switchModel.connect(lambda m: self.switchModel.emit(m))
        self.chat_area.openSettings.connect(lambda: self.navigation.open_settings_page(0))
        self.chat_area.toggleRightPanel.connect(self.navigation.toggle_right_panel)
        self.chat_area.windowMinimize.connect(self.showMinimized)
        self.chat_area.windowHideToMascot.connect(self.window_mgr.switch_to_mini_mascot)
        self.chat_area.windowMaximize.connect(self.window_mgr.toggle_maximize)
        self.chat_area.windowClose.connect(self.close)
        self.chat_area.executeToolRequested.connect(self._on_execute_tool)

        # Settings Events
        if hasattr(self.settings_page, 'backToChatRequested'):
            self.settings_page.backToChatRequested.connect(self.navigation.show_chat_view)
        if hasattr(self.settings_page, 'requestOpenDownloadTab'):
            self.settings_page.requestOpenDownloadTab.connect(lambda: self.navigation.open_settings_page(2))
        self.settings_page.modelDownloaded.connect(lambda: self.chat_area.input_bar._load_local_models())

    # ============================================================
    # PUBLIC MVC INTERFACE (Called by Controller & Services)
    # ============================================================

    def set_controller(self, controller):
        self.controller = controller

    def show_window(self):
        self.dispatcher.showWindowSignal.emit()

    def hide_window(self):
        self.dispatcher.hideWindowSignal.emit()

    def show_welcome(self):
        self.show_toast("Chào mừng bạn quay trở lại với POP AI!", "info")

    def show_toast(self, message: str, toast_type: str = "info"):
        self.dispatcher.toastSignal.emit(message, toast_type)

    def show_alert_notification(self, alert_data: dict):
        self.dispatcher.alertSignal.emit(alert_data)

    def set_voice_state(self, state: VoiceState):
        self.dispatcher.voiceStateSignal.emit(state)

    def update_bot_text(self, text: str):
        self.dispatcher.botTextSignal.emit(text)

    def update_user_text(self, text: str):
        self.dispatcher.userTextSignal.emit(text)

    def set_bot_status(self, status: str):
        self.show_toast(status, "info")

    def set_listening(self, is_listening: bool):
        self.set_voice_state(VoiceState.LISTENING if is_listening else VoiceState.READY)

    def show_confirmation_card(self, title: str, summary: str, tool_name: str, tool_args: dict):
        self.dispatcher.confirmationCardSignal.emit(title, summary, tool_name, tool_args)

    def show_file_preview(self, files: list):
        self.dispatcher.filePreviewSignal.emit(files)

    def update_chat(self, text: str, sender: str = "bot"):
        if not text:
            return
        if sender == "bot":
            self.chat_area.set_thinking(False)
            msg = self.chat_model.add_bot_message(text)
            self.right_panel.add_activity_log("AI Response", "chat")
        else:
            msg = self.chat_model.add_user_message(text)
            self.sidebar.reload_conversations()
            self.right_panel.add_activity_log("User Message", "chat")
        self.chat_area.append_message(msg)

    # ============================================================
    # INTERNAL SLOTS
    # ============================================================

    def _handle_user_speech_status(self, text: str):
        if not text:
            return
        if text == "Đang lắng nghe...":
            self._handle_voice_state(VoiceState.LISTENING)
            return
        if text == "Pop không nghe rõ...":
            self._handle_voice_state(VoiceState.READY)
            return
        self.update_chat(text, sender="user")

    def _handle_voice_state(self, state: VoiceState):
        self.right_panel.set_voice_state(state)
        self.mini_mascot.set_voice_state(state)
        self.chat_area.input_bar.set_listening(state == VoiceState.LISTENING)

    def _handle_toast(self, message: str, toast_type: str = "info"):
        print(f"[POP UI Toast] {toast_type.upper()}: {message}")
        self.right_panel.add_activity_log(message, category=toast_type)

    def _handle_show_window(self):
        if hasattr(self, 'mini_mascot') and self.mini_mascot:
            self.mini_mascot.hide()
        self.show()
        self.raise_()
        self.activateWindow()

    def _handle_show_confirmation(self, title: str, summary: str, tool_name: str, tool_args: dict):
        self.chat_area.set_thinking(False)
        self.chat_area.append_confirmation_card(title, summary, tool_name, tool_args)

    def _handle_show_file_preview(self, files: list):
        self.chat_area.set_thinking(False)
        self.chat_area.append_file_preview_card(files)

    def _on_user_send_message(self, text: str):
        msg = self.chat_model.add_user_message(text)
        self.sidebar.reload_conversations()
        self.chat_area.append_message(msg)
        self.right_panel.add_activity_log("User Message", "chat")
        self.chat_area.set_thinking(True)
        self.sendMessage.emit(text)

    def _on_execute_tool(self, tool_name: str, tool_args: dict):
        if self.controller and hasattr(self.controller, 'execute_tool'):
            self.controller.execute_tool(tool_name, tool_args)

    def _on_new_chat(self):
        self.navigation.show_chat_view()
        new_session = self.chat_model.create_new_session("Cuộc trò chuyện mới")
        self.sidebar.reload_conversations()
        self.chat_area.load_session(new_session)
        self.right_panel.add_activity_log("Cuộc trò chuyện mới", "chat")
        self.newConversation.emit()

    def _on_conversation_selected(self, session_id: str):
        self.navigation.show_chat_view()
        self.chat_model.set_active_session(session_id)
        session = self.chat_model.get_active_session()
        if session:
            self.chat_area.load_session(session)
            self.loadConversation.emit(session_id)

    def _handle_logout_requested(self):
        if hasattr(self, 'mini_mascot') and self.mini_mascot:
            self.mini_mascot.hide()
            self.mini_mascot.close()
        self.hide()
        self.close()
        self.logoutRequested.emit()

    # ============================================================
    # WINDOW EVENTS (Delegated to PopWindowManager)
    # ============================================================

    def mousePressEvent(self, a0):
        self.window_mgr.handle_mouse_press(a0)

    def mouseMoveEvent(self, a0):
        self.window_mgr.handle_mouse_move(a0)

    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        self.window_mgr.handle_resize(self.width(), self.height())

    def showEvent(self, a0):
        super().showEvent(a0)
        self.window_mgr.handle_show()

    def hideEvent(self, a0):
        super().hideEvent(a0)
        self.window_mgr.handle_hide()

    def closeEvent(self, a0):
        self.hide()
        if hasattr(self, 'mini_mascot') and self.mini_mascot:
            self.mini_mascot.hide()
            self.mini_mascot.close()
        if self.controller and hasattr(self.controller, 'shutdown'):
            try:
                self.controller.shutdown.stop()
            except Exception:
                pass
        self.viewClosed.emit()
        super().closeEvent(a0)
        app = QApplication.instance()
        if app:
            app.quit()
