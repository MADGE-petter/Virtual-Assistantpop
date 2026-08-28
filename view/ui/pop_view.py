"""
PopView - Main Window View implementing MVC interface for POP AI Assistant with Mini Mascot integration.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame,
    QGraphicsDropShadowEffect, QStackedWidget
)

from view.ui.styles import STYLE_SHEET, DesignTokens
from view.ui.widgets import (
    StarfieldWidget, SidebarWidget, ChatAreaWidget,
    RightPanelWidget, MiniMascotWidget, MemoryDialog
)
from view.ui.settings import SettingsDialog
from view.ui.icons import get_pop_logo_icon
from model.pop_chat_model import PopChatModel
from model.voice_state_model import VoiceState
from service.agent import OpenClawAgentEngine


class PopView(QMainWindow):
    """Main Application Window for POP AI Assistant adhering strictly to MVC architecture."""

    sendMessage = pyqtSignal(str)
    voiceToggled = pyqtSignal()
    stopGeneration = pyqtSignal()
    newConversation = pyqtSignal()
    switchModel = pyqtSignal(str)
    openSettings = pyqtSignal()
    loadConversation = pyqtSignal(str)
    deleteConversation = pyqtSignal(str)
    viewClosed = pyqtSignal()

    # Thread-safe cross-thread UI dispatch signals
    _botTextSignal = pyqtSignal(str)
    _userTextSignal = pyqtSignal(str)
    _voiceStateSignal = pyqtSignal(object)
    _toastSignal = pyqtSignal(str, str)
    _alertSignal = pyqtSignal(dict)
    _showWindowSignal = pyqtSignal()
    _hideWindowSignal = pyqtSignal()

    def __init__(self, user_name: str = "Tài khoản"):
        super().__init__()
        self.controller = None
        self.user_name = user_name

        self.setWindowTitle("POP - AI Assistant")
        self.setWindowIcon(get_pop_logo_icon(32))
        self.resize(1280, 800)
        self.setMinimumSize(960, 600)

        # Frameless dark window style
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Chat Data Model & Agent Engine
        self.chat_model = PopChatModel()
        self.agent_engine = OpenClawAgentEngine()

        self._drag_pos = QPoint()

        self._setup_ui()
        self.setStyleSheet(STYLE_SHEET)

        # Connect thread-safe internal signals to main-thread handlers
        self._botTextSignal.connect(self._handle_update_bot_text)
        self._userTextSignal.connect(self._handle_update_user_text)
        self._voiceStateSignal.connect(self._handle_set_voice_state)
        self._toastSignal.connect(self._handle_show_toast)
        self._alertSignal.connect(self._handle_show_alert_notification)
        self._showWindowSignal.connect(self._handle_show_window)
        self._hideWindowSignal.connect(self._handle_hide_window)

        # Desktop Mini Mascot Floating Avatar Widget
        self.mini_mascot = MiniMascotWidget()
        self.mini_mascot.move(100, 100)
        self.mini_mascot.show()
        self.mini_mascot.toggleMainWindowRequested.connect(self._toggle_main_window_visibility)

    def _setup_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        root_layout = QVBoxLayout(self.central_widget)
        root_layout.setContentsMargins(10, 10, 10, 10)

        self.container_box = QFrame()
        self.container_box.setObjectName("mainContainer")
        self.container_box.setStyleSheet(
            f"QFrame#mainContainer {{ background-color: {DesignTokens.BG_BASE}; border: none; border-radius: 16px; }}"
        )
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(Qt.GlobalColor.black)
        shadow.setOffset(0, 8)
        self.container_box.setGraphicsEffect(shadow)

        box_layout = QHBoxLayout(self.container_box)
        box_layout.setContentsMargins(0, 0, 0, 0)
        box_layout.setSpacing(0)

        # 1. Starfield Canvas
        self.starfield = StarfieldWidget(self.container_box)
        self.starfield.setGeometry(0, 0, 1280, 800)
        self.starfield.lower()

        # 2. Left Sidebar
        self.sidebar = SidebarWidget(self.chat_model, self.user_name, self.container_box)
        self.sidebar.newChatRequested.connect(self._on_new_chat)
        self.sidebar.conversationSelected.connect(self._on_conversation_selected)
        self.sidebar.deleteConversationRequested.connect(lambda sid: self.deleteConversation.emit(sid))
        self.sidebar.settingsClicked.connect(lambda: self._open_settings_page(0))
        self.sidebar.modelsClicked.connect(lambda: self._open_settings_page(1))
        self.sidebar.settingsTabSelected.connect(lambda tab_idx: self._open_settings_page(tab_idx))
        self.sidebar.memoryClicked.connect(self._open_memory_dialog)
        # 3. Central Stack (Switching between Chat View and Settings Page)
        self.center_stack = QStackedWidget(self.container_box)
        self.center_stack.setStyleSheet("QStackedWidget { background: transparent; }")

        self.chat_area = ChatAreaWidget(self.container_box)
        self.chat_area.sendMessage.connect(self._on_user_send_message)
        self.chat_area.stopGeneration.connect(lambda: self.stopGeneration.emit())
        self.chat_area.switchModel.connect(lambda m: self.switchModel.emit(m))
        self.chat_area.openSettings.connect(lambda: self._open_settings_page(0))
        self.chat_area.toggleRightPanel.connect(self._toggle_right_panel)
        self.chat_area.windowMinimize.connect(self._switch_to_mini_mascot)
        self.chat_area.windowMaximize.connect(self._toggle_maximize)
        self.chat_area.windowClose.connect(self.close)
        self.chat_area.executeToolRequested.connect(self._on_execute_tool)

        from view.ui.settings import SettingsWidget
        self.settings_page = SettingsWidget(self.user_name, initial_tab=0, parent=self.container_box)
        self.settings_page.backToChatRequested.connect(self._show_chat_view)
        self.settings_page.modelDownloaded.connect(lambda: self.chat_area.input_bar._load_local_models())

        self.center_stack.addWidget(self.chat_area)
        self.center_stack.addWidget(self.settings_page)

        # 4. Right Telemetry Panel
        self.right_panel = RightPanelWidget(self.container_box)

        # Vertical Separator Line between Sidebar & Center Area
        self.sidebar_line = QFrame()
        self.sidebar_line.setFixedWidth(1)
        self.sidebar_line.setStyleSheet("background-color: rgba(255, 255, 255, 0.25);")

        box_layout.addWidget(self.sidebar)
        box_layout.addWidget(self.sidebar_line)
        box_layout.addWidget(self.center_stack, stretch=1)
        box_layout.addWidget(self.right_panel)

        root_layout.addWidget(self.container_box)

        active_session = self.chat_model.get_active_session()
        if active_session:
            self.chat_area.load_session(active_session)

    def _open_memory_dialog(self):
        from view.ui.widgets import MemoryDialog
        dialog = MemoryDialog(self.user_name, self)
        dialog.exec()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.starfield.setGeometry(0, 0, self.width(), self.height())

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.isMaximized():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def _switch_to_mini_mascot(self):
        """Hide main chat window and re-show Mini Mascot floating avatar."""
        self.hide()
        if hasattr(self, 'mini_mascot'):
            self.mini_mascot.show()

    def _toggle_main_window_visibility(self):
        """Toggle Show / Hide main POP window when double clicking Mini Mascot."""
        if self.isVisible():
            self._switch_to_mini_mascot()
        else:
            if hasattr(self, 'mini_mascot'):
                self.mini_mascot.hide()
            self.show()
            self.raise_()
            self.activateWindow()
            self.setFocus()

    # ============================================================
    # CONTROLLER COMPATIBILITY API (Thread-Safe Public Methods)
    # ============================================================

    def set_controller(self, controller):
        self.controller = controller

    def show_window(self):
        self._showWindowSignal.emit()

    def hide_window(self):
        self._hideWindowSignal.emit()

    def show_welcome(self):
        self.show_toast("Chào mừng bạn quay trở lại với POP AI!", "info")

    def show_toast(self, message: str, toast_type: str = "info"):
        self._toastSignal.emit(message, toast_type)

    def show_alert_notification(self, alert_data: dict):
        self._alertSignal.emit(alert_data)

    def set_voice_state(self, state: VoiceState):
        self._voiceStateSignal.emit(state)

    def update_bot_text(self, text: str):
        """Update bot speech/message on UI (thread-safe)."""
        self._botTextSignal.emit(text)

    def update_user_text(self, text: str):
        """Update user speech/status on UI (thread-safe)."""
        self._userTextSignal.emit(text)

    def set_bot_status(self, status: str):
        """Update status pill/badge."""
        self.show_toast(status, "info")

    def set_listening(self, is_listening: bool):
        state = VoiceState.LISTENING if is_listening else VoiceState.IDLE
        self.set_voice_state(state)

    def update_chat(self, text: str, sender: str = "bot"):
        if sender == "bot":
            self.chat_area.set_thinking(False)
            msg = self.chat_model.add_bot_message(text)
            self.right_panel.add_activity_log("AI Response", "chat")
        else:
            msg = self.chat_model.add_user_message(text)
            self.right_panel.add_activity_log("User Message", "chat")

        self.chat_area.append_message(msg)

    # ============================================================
    # MAIN-THREAD SIGNAL HANDLERS
    # ============================================================

    def _handle_update_bot_text(self, text: str):
        if not text:
            return
        self.update_chat(text, sender="bot")

    def _handle_update_user_text(self, text: str):
        if not text:
            return
        status_keywords = ["Đang lắng nghe...", "Pop không nghe rõ...", "..."]
        if text in status_keywords:
            if text == "Đang lắng nghe...":
                self._handle_set_voice_state(VoiceState.LISTENING)
            elif text == "Pop không nghe rõ...":
                self._handle_set_voice_state(VoiceState.IDLE)
            return
        
        self.update_chat(text, sender="user")

    def _handle_set_voice_state(self, state: VoiceState):
        self.right_panel.set_voice_state(state)
        self.mini_mascot.set_voice_state(state)
        is_listening = (state == VoiceState.LISTENING)
        self.chat_area.input_bar.set_listening(is_listening)

    def _handle_show_toast(self, message: str, toast_type: str = "info"):
        print(f"[POP UI Toast] {toast_type.upper()}: {message}")
        self.right_panel.add_activity_log(message, category=toast_type)

    def _handle_show_alert_notification(self, alert_data: dict):
        msg = alert_data.get("message", "Cảnh báo hệ thống")
        self._handle_show_toast(msg, "warning")

    def _handle_show_window(self):
        if hasattr(self, 'mini_mascot'):
            self.mini_mascot.hide()
        self.show()
        self.raise_()
        self.activateWindow()

    def _handle_hide_window(self):
        self._switch_to_mini_mascot()

    # ============================================================
    # PRIVATE INTERNAL HANDLERS & AGENT DISPATCHER
    # ============================================================

    def _on_user_send_message(self, text: str):
        msg = self.chat_model.add_user_message(text)
        self.chat_area.append_message(msg)
        self.right_panel.add_activity_log("User Message", "chat")

        # Process through Agentic Engine
        plan = self.agent_engine.analyze_request(text)

        if plan.is_clarification_needed:
            # Speak & show clarification question
            bot_msg = self.chat_model.add_bot_message(plan.clarification_question)
            self.chat_area.append_message(bot_msg)
            if self.controller and hasattr(self.controller, 'audio'):
                self.controller.audio.speak(plan.clarification_question)
            return

        if plan.needs_confirmation:
            # Display Action Confirmation Card
            self.chat_area.append_confirmation_card(
                title=plan.confirmation_title,
                summary=plan.summary_text,
                tool_name=plan.tool_name,
                tool_args=plan.tool_args
            )
            confirm_voice = f"Vui lòng xác nhận hành động: {plan.summary_text}"
            if self.controller and hasattr(self.controller, 'audio'):
                self.controller.audio.speak(confirm_voice)
            return

        if plan.tool_name == "file_search":
            from tools.file_search_tool import FileSearchTool
            files = FileSearchTool.search_files(plan.tool_args.get("query", ""))
            if files:
                self.chat_area.append_file_preview_card(files)
            else:
                bot_msg = self.chat_model.add_bot_message(f"Không tìm thấy tệp nào phù hợp với từ khóa '{plan.tool_args.get('query')}' trên máy tính.")
                self.chat_area.append_message(bot_msg)
            return

        if plan.tool_name == "web_search":
            from tools.web_tool import WebTool
            res = WebTool.search_or_read_web(plan.tool_args.get("query", ""))
            reply = res.get("summary") or res.get("content") or "Đã hoàn thành tra cứu web."
            bot_msg = self.chat_model.add_bot_message(reply)
            self.chat_area.append_message(bot_msg)
            return

        # General conversation -> Delegate to Controller
        self.chat_area.set_thinking(True)
        self.sendMessage.emit(text)

    def _on_execute_tool(self, tool_name: str, tool_args: dict):
        """Execute tool after user approves action confirmation card."""
        print(f"[PopView] User confirmed action -> Executing tool '{tool_name}' with args: {tool_args}")
        status_msg = ""
        if tool_name == "zalo_send":
            from tools.zalo_tool import ZaloTool
            res = ZaloTool.send_message(tool_args.get("recipient"), tool_args.get("message"))
            status_msg = res.get("message", "Đã gửi tin nhắn Zalo.")
        elif tool_name == "facebook_send":
            from tools.facebook_tool import FacebookTool
            res = FacebookTool.send_message(tool_args.get("recipient"), tool_args.get("message"))
            status_msg = res.get("message", "Đã gửi tin nhắn Facebook.")

        bot_msg = self.chat_model.add_bot_message(status_msg)
        self.chat_area.append_message(bot_msg)
        if self.controller and hasattr(self.controller, 'audio'):
            self.controller.audio.speak(status_msg)

    def _on_new_chat(self):
        self._show_chat_view()
        new_session = self.chat_model.create_new_session("Cuộc trò chuyện mới")
        self.sidebar.reload_conversations()
        self.chat_area.load_session(new_session)
        self.right_panel.add_activity_log("Cuộc trò chuyện mới", "chat")
        self.newConversation.emit()

    def _on_conversation_selected(self, session_id: str):
        self._show_chat_view()
        session = self.chat_model.get_active_session()
        if session:
            self.chat_area.load_session(session)
            self.loadConversation.emit(session_id)

    def _open_settings_page(self, initial_tab: int = 0):
        self.sidebar.set_mode(1, initial_tab)
        self.settings_page.open_tab(initial_tab)
        self.center_stack.setCurrentIndex(1)

    def _show_chat_view(self):
        self.sidebar.set_mode(0)
        self.center_stack.setCurrentIndex(0)

    def _toggle_right_panel(self):
        if self.right_panel.isVisible():
            self.right_panel.hide()
        else:
            self.right_panel.show()

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def closeEvent(self, event):
        if hasattr(self, 'mini_mascot') and self.mini_mascot:
            self.mini_mascot.close()
        self.viewClosed.emit()
        super().closeEvent(event)
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.quit()
