"""
PopView - Main Window View implementing MVC interface for POP AI Assistant matching images po1 and po.
"""

import sys
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QIcon, QMouseEvent
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel,
    QApplication, QGraphicsDropShadowEffect
)

from view.ui.styles import STYLE_SHEET, DesignTokens
from view.ui.starfield_widget import StarfieldWidget
from view.ui.sidebar_widget import SidebarWidget
from view.ui.chat_area_widget import ChatAreaWidget
from view.ui.right_panel_widget import RightPanelWidget
from view.ui.icons import get_pop_logo_icon
from model.pop_chat_model import PopChatModel, ChatMessage
from model.voice_state_model import VoiceState


class PopView(QMainWindow):
    """Main Application Window for POP AI Assistant adhering strictly to MVC architecture."""

    # View Signals (connected to Controller slots)
    sendMessage = pyqtSignal(str)
    voiceToggled = pyqtSignal()
    stopGeneration = pyqtSignal()
    newConversation = pyqtSignal()
    switchModel = pyqtSignal(str)
    openSettings = pyqtSignal()
    searchConversations = pyqtSignal(str)
    loadConversation = pyqtSignal(str)
    deleteConversation = pyqtSignal(str)
    viewClosed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.controller = None
        self.user_name = "Tuấn"

        self.setWindowTitle("POP - AI Assistant")
        self.setWindowIcon(get_pop_logo_icon(32))
        self.resize(1280, 800)
        self.setMinimumSize(960, 600)

        # Frameless dark window style
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Chat Data Model
        self.chat_model = PopChatModel()

        # Frameless window drag state
        self._drag_pos = QPoint()

        self._setup_ui()
        self.setStyleSheet(STYLE_SHEET)

    def _setup_ui(self):
        # Main Container
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        root_layout = QVBoxLayout(self.central_widget)
        root_layout.setContentsMargins(10, 10, 10, 10)

        # Outer Glass Container Box
        self.container_box = QFrame()
        self.container_box.setObjectName("mainContainer")
        self.container_box.setStyleSheet(
            f"QFrame#mainContainer {{ background-color: {DesignTokens.BG_BASE}; border: 1px solid {DesignTokens.BORDER}; border-radius: 16px; }}"
        )
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(Qt.GlobalColor.black)
        shadow.setOffset(0, 8)
        self.container_box.setGraphicsEffect(shadow)

        box_layout = QHBoxLayout(self.container_box)
        box_layout.setContentsMargins(0, 0, 0, 0)
        box_layout.setSpacing(0)

        # ----------------------------------------------------
        # 1. STARFIELD BACKGROUND CANVAS
        # ----------------------------------------------------
        self.starfield = StarfieldWidget(self.container_box)
        self.starfield.setGeometry(0, 0, 1280, 800)
        self.starfield.lower()

        # ----------------------------------------------------
        # 2. LEFT SIDEBAR (po #2 to #6)
        # ----------------------------------------------------
        self.sidebar = SidebarWidget(self.chat_model, self.container_box)
        self.sidebar.newChatRequested.connect(self._on_new_chat)
        self.sidebar.conversationSelected.connect(self._on_conversation_selected)
        self.sidebar.deleteConversationRequested.connect(lambda sid: self.deleteConversation.emit(sid))
        self.sidebar.searchChanged.connect(lambda query: self.searchConversations.emit(query))
        self.sidebar.settingsClicked.connect(lambda: self.openSettings.emit())

        # ----------------------------------------------------
        # 3. CENTRAL CHAT AREA (po #1, #7 to #11)
        # ----------------------------------------------------
        self.chat_area = ChatAreaWidget(self.container_box)
        self.chat_area.sendMessage.connect(self._on_user_send_message)
        self.chat_area.voiceToggled.connect(lambda: self.voiceToggled.emit())
        self.chat_area.stopGeneration.connect(lambda: self.stopGeneration.emit())
        self.chat_area.switchModel.connect(lambda m: self.switchModel.emit(m))
        self.chat_area.openSettings.connect(lambda: self.openSettings.emit())
        self.chat_area.toggleRightPanel.connect(self._toggle_right_panel)
        self.chat_area.windowMinimize.connect(self.showMinimized)
        self.chat_area.windowMaximize.connect(self._toggle_maximize)
        self.chat_area.windowClose.connect(self.close)

        # ----------------------------------------------------
        # 4. RIGHT TELEMETRY PANEL (po #12 to #15)
        # ----------------------------------------------------
        self.right_panel = RightPanelWidget(self.container_box)

        box_layout.addWidget(self.sidebar)
        box_layout.addWidget(self.chat_area, stretch=1)
        box_layout.addWidget(self.right_panel)

        root_layout.addWidget(self.container_box)

        # Load initial conversation matching po1
        active_session = self.chat_model.get_active_session()
        if active_session:
            self.chat_area.load_session(active_session)

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

    # ============================================================
    # CONTROLLER COMPATIBILITY API
    # ============================================================

    def set_controller(self, controller):
        self.controller = controller

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_window(self):
        self.hide()

    def show_welcome(self):
        self.show_toast("Chào mừng bạn quay trở lại với POP AI!", "info")

    def show_toast(self, message: str, toast_type: str = "info"):
        print(f"[POP UI Toast] {toast_type.upper()}: {message}")
        self.right_panel.add_activity_log(message, category=toast_type)

    def show_alert_notification(self, alert_data: dict):
        msg = alert_data.get("message", "Cảnh báo hệ thống")
        self.show_toast(msg, "warning")

    def set_voice_state(self, state: VoiceState):
        self.right_panel.set_voice_state(state)
        is_listening = (state == VoiceState.LISTENING)
        self.chat_area.input_bar.set_listening(is_listening)

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
    # PRIVATE INTERNAL HANDLERS
    # ============================================================

    def _on_user_send_message(self, text: str):
        msg = self.chat_model.add_user_message(text)
        self.chat_area.append_message(msg)
        self.chat_area.set_thinking(True)
        self.right_panel.add_activity_log("User Message", "chat")
        self.sendMessage.emit(text)

    def _on_new_chat(self):
        new_session = self.chat_model.create_new_session("Cuộc trò chuyện mới")
        self.sidebar.reload_conversations()
        self.chat_area.load_session(new_session)
        self.right_panel.add_activity_log("Cuộc trò chuyện mới", "chat")
        self.newConversation.emit()

    def _on_conversation_selected(self, session_id: str):
        session = self.chat_model.get_active_session()
        if session:
            self.chat_area.load_session(session)
            self.loadConversation.emit(session_id)

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
        self.viewClosed.emit()
        super().closeEvent(event)
