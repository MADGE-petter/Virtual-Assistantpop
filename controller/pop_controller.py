from typing import Any, Optional

from PyQt6.QtCore import QObject, pyqtSignal

from controller.action import ActionHandler
from controller.conversation_controller import ConversationController
from controller.conversation_coordinator import ConversationCoordinator
from controller.shutdown_coordinator import ShutdownCoordinator
from controller.startup_coordinator import StartupCoordinator
from controller.voice_mode_coordinator import VoiceModeCoordinator
from model.Sql import SqlService
from service.analytics_service import get_analytics_service
from service.AudioService import AudioService
from service.user_service import UserService
from service.voice_service import VoiceService


class PopController(QObject):
    """Facade controller - điều phối thông qua các Coordinator chuyên biệt."""
    
    # Signal để wake up từ thread khác (thread-safe)
    wakeUpRequested = pyqtSignal()
    
    def __init__(self, view: Any = None, model: Any = None, login_username: Optional[str] = None):
        super().__init__()
        self.view: Any = view
        self.login_username = login_username
        
        # State
        self._started = False
        self._active = False
        
        # === KHỞI TẠO SERVICES ===
        self.audio = AudioService(view)
        self.sql = SqlService()
        self.actions = ActionHandler(self.audio, view, controller=self)
        
        # User service
        self._user_svc = UserService(self.sql)
        if login_username:
            self._user_svc.login_name = login_username
            loaded_name = self._user_svc.get_display_name_by_login(login_username)
            if loaded_name and loaded_name != "bạn":
                self._user_svc.display_name = loaded_name
        
        # Analytics
        analytics_user = self._user_svc.login_name if getattr(self._user_svc, 'login_name', None) and self._user_svc.login_name != "bạn" else getattr(self._user_svc, 'display_name', None) or "bạn"
        self._analytics = get_analytics_service(analytics_user or "user")

        if login_username:
            try:
                self.actions.set_login_name(login_username)
            except Exception:
                pass

        # === KHỞI TẠO SUB-CONTROLLERS & SERVICES ===
        self.voice = VoiceService(self.audio, view=view)
        self.user = self._user_svc
        self.analytics = self._analytics
        
        # Memory service
        from service.memory_service import MemoryService
        self.memory = MemoryService(self.sql)
        
        self.conversation = ConversationController(
            self.audio,
            self.sql,
            self.actions,
            self.user
        )
        # Connect MemoryService to ConversationService
        self.conversation.service.init_memory_service(self.memory)
        
        # === KHỞI TẠO MODULAR COORDINATORS ===
        self.voice_coordinator = VoiceModeCoordinator(
            audio=self.audio,
            voice=self.voice,
            view=view,
            on_wake_up=self._do_wake_up,
            on_go_sleep=self._on_go_sleep
        )
        self.conversation_coordinator = ConversationCoordinator(
            audio=self.audio,
            voice=self.voice,
            conversation=self.conversation
        )
        self.startup = StartupCoordinator(
            audio=self.audio,
            voice=self.voice,
            analytics=self._analytics,
            conversation=self.conversation,
            sql=self.sql,
            user_service=self._user_svc,
            view=view
        )
        self.shutdown = ShutdownCoordinator(
            audio=self.audio,
            voice=self.voice,
            analytics=self._analytics,
            conversation=self.conversation
        )
        
        # === SETUP CALLBACKS ===
        self.voice.on_wake_up = self._request_wake_up
        self.voice.on_go_sleep = self._on_go_sleep
        self.voice.on_idle_timeout = self._on_idle
        self.wakeUpRequested.connect(self._do_wake_up)
        
        # Inject controller vào view (view không cần biết services)
        if self.view is not None:
            self.view.set_controller(self)
            self.conversation.on_permission_requested = self.view.show_confirmation_card
            self.conversation.on_file_preview_requested = self.view.show_file_preview
            self.conversation.on_error = lambda err: self.view.update_chat(err, sender="bot")
            
            # Connect View signals
            self.view.sendMessage.connect(self._on_send_message)
            self.view.voiceToggled.connect(self._on_voice_toggled)
            self.view.stopGeneration.connect(self._on_stop_generation)
            self.view.newConversation.connect(self._on_new_conversation)
            self.view.switchModel.connect(self._on_switch_model)
            self.view.openSettings.connect(self._on_open_settings)
            self.view.loadConversation.connect(self._on_load_conversation)
            self.view.deleteConversation.connect(self._on_delete_conversation)
            self.view.viewClosed.connect(self._on_view_closed)

            # Sync active session ID with ConversationService
            self._sync_conversation_session()

    def _sync_conversation_session(self, conversation_id: Optional[str] = None):
        """Đồng bộ session ID hợp lệ (integer) sang ConversationService."""
        try:
            if not hasattr(self, 'conversation') or not hasattr(self.conversation, 'service'):
                return

            valid_id: Optional[int] = None

            if conversation_id and conversation_id.isdigit():
                valid_id = int(conversation_id)
            elif self.view and hasattr(self.view, 'chat_model'):
                session = self.view.chat_model.get_active_session()
                if session:
                    valid_id = self.view.chat_model._ensure_persisted_session(session)

            if valid_id is not None:
                self.conversation.service._session_id = valid_id
        except Exception as e:
            print(f"[PopController] Lỗi đồng bộ session ID: {e}")

    # ============================================================
    # VIEW SIGNAL HANDLERS (Controller slots)
    # ============================================================

    def _on_send_message(self, text: str):
        """Handle user sending a message from chat."""
        # Delegate to conversation controller
        self.conversation.handle_user_message(text)

    def _on_voice_toggled(self):
        """Handle voice input toggle."""
        self.voice.toggle_voice_input()

    def _on_stop_generation(self):
        """Handle stop generation request."""
        self.conversation.stop_generation()

    def _on_new_conversation(self):
        """Handle new conversation request."""
        self._sync_conversation_session()

    def _on_switch_model(self, model_name: str = ""):
        """Handle model switch request."""
        try:
            if hasattr(self, 'conversation') and hasattr(self.conversation, 'set_model'):
                self.conversation.set_model(model_name)

            if self.view:
                msg = f"Đã chuyển sang mô hình: {model_name}" if model_name else "Đã cập nhật mô hình AI"
                self.view.show_toast(msg, "info")
        except Exception as e:
            if self.view:
                self.view.show_toast(f"Lỗi chuyển model: {str(e)}", "error")

    def _on_open_settings(self):
        """Handle open settings request."""
        if self.view and hasattr(self.view, 'navigation'):
            self.view.navigation.open_settings_page(0)

    def _on_load_conversation(self, conversation_id: str):
        """Handle load conversation request."""
        try:
            if self.view and hasattr(self.view, 'chat_model'):
                self.view.chat_model.set_active_session(conversation_id)
                session = self.view.chat_model.get_active_session()
                if session and hasattr(self.view, 'chat_area'):
                    self.view.chat_area.load_session(session)
            self._sync_conversation_session(conversation_id)
        except Exception as e:
            print(f"[PopController] Lỗi tải cuộc trò chuyện: {e}")
    
    def _on_delete_conversation(self, conversation_id: str):
        """Handle delete conversation request."""
        try:
            if self.view and hasattr(self.view, 'chat_model'):
                self.view.chat_model.delete_session(conversation_id)
                if hasattr(self.view, 'sidebar'):
                    self.view.sidebar.reload_conversations()
                active = self.view.chat_model.get_active_session()
                if active and hasattr(self.view, 'chat_area'):
                    self.view.chat_area.load_session(active)
                elif hasattr(self.view, 'chat_area'):
                    new_session = self.view.chat_model.create_new_session("Cuộc trò chuyện mới")
                    if hasattr(self.view, 'sidebar'):
                        self.view.sidebar.reload_conversations()
                    self.view.chat_area.load_session(new_session)
                if hasattr(self.view, 'show_toast'):
                    self.view.show_toast("Đã xóa cuộc trò chuyện", "info")
        except Exception as e:
            print(f"[PopController] Lỗi xóa cuộc trò chuyện: {e}")
    
    def _on_view_closed(self):
        """Handle view closed."""
        self.stop()
    
    # ============================================================
    # PUBLIC API & DELEGATES (Facaded via Coordinators)
    # ============================================================
    
    def start(self):
        """Khởi động assistant qua Startup & Conversation Coordinator."""
        if self._started:
            self._active = True
            return
        
        self._started = True
        self._active = True
        self.startup.start(login_username=self.login_username)
        self._activate_view()
        self.conversation_coordinator.start_conversation()
    
    def stop(self):
        """Dừng assistant qua Shutdown Coordinator."""
        self._active = False
        self.shutdown.stop()

    def exit_app(self):
        """Thoát hoàn toàn ứng dụng Pop."""
        print("[PopController] exit_app called")
        self._active = False
        self._started = False
        if hasattr(self, "conversation_coordinator"):
            try:
                self.conversation_coordinator.stop()
            except Exception:
                pass
        if self.view and hasattr(self.view, "close"):
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self.view.close)
        else:
            if hasattr(self, "shutdown"):
                self.shutdown.stop()
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.quit()
    
    def sleep(self, manual=True):
        """Vào sleep mode qua VoiceModeCoordinator."""
        self.voice_coordinator.sleep(manual=manual)
    
    def wake(self):
        """Thức dậy từ sleep qua VoiceModeCoordinator."""
        self.voice_coordinator.wake()
    
    def speak(self, text):
        """Bot nói."""
        return self.voice.speak(text, update_ui=True)
    
    def listen(self):
        """Bot nghe."""
        return self.voice.get_voice_input()
    
    # ============================================================
    # PRIVATE HANDLERS
    # ============================================================
    
    def _request_wake_up(self):
        """Callback từ VoiceController khi wake word detected."""
        self.wakeUpRequested.emit()
    
    def _activate_view(self):
        """Activate and show main window."""
        if self.view:
            self.view.show_window()
    
    def _do_wake_up(self):
        """Thực hiện wake up trên main thread khi người dùng gọi wake word."""
        if self.view and hasattr(self.view, 'mini_mascot') and self.view.mini_mascot:
            self.view.mini_mascot.wake_up()
        if hasattr(self, 'voice_coordinator') and self.voice_coordinator.is_sleeping:
            self.voice_coordinator.wake()
        else:
            self._activate_view()
    
    def _on_go_sleep(self):
        """Callback khi vào sleep."""
        if self.view:
            self.view.hide_window()
    
    def _on_idle(self):
        """Callback khi idle (Sleep mode disabled)."""
        pass
    
    def _on_gesture(self, gesture_type):
        """Callback từ gesture service."""
        pass
    
    # ============================================================
    # PRIVATE - Conversation management
    # ============================================================
    
    def _enter_active_mode(self):
        """Vào active mode - hiện app và bắt đầu conversation."""
        self._activate_view()
        self.conversation_coordinator.start_conversation(from_wake_up=False)
        self.voice.start_idle_monitor(self._on_idle)
    
    def _start_conversation(self, from_wake_up: bool = False):
        """Bắt đầu conversation thread qua ConversationCoordinator."""
        self.conversation_coordinator.start_conversation(from_wake_up=from_wake_up)
    
    def execute_tool(self, tool_name: str, tool_args: dict):
        """Thực thi tool sau khi user xác nhận."""
        print(f"[PopController] Execute Tool: {tool_name} with args: {tool_args}")
        status_msg = ""
        
        sensitive_actions = ["open_website", "open_app", "system_control", "open_file"]
        
        try:
            if tool_name in sensitive_actions:
                # Execute using ActionHandler with execute=True
                text = tool_args.get("text", "")
                result = self.actions.handle(tool_name, text, execute=True)
                
                from service.conversation_service import ActionResult
                status_msg = result.text if isinstance(result, ActionResult) else str(result)
            elif tool_name == "zalo_send":
                from tools.zalo_tool import ZaloTool
                recipient = str(tool_args.get("recipient", "") or "")
                msg_content = str(tool_args.get("message", "") or "")
                res = ZaloTool.send_message(recipient, msg_content)
                status_msg = res.get("message", "Đã gửi tin nhắn Zalo.")
            elif tool_name == "facebook_send":
                from tools.facebook_tool import FacebookTool
                recipient = str(tool_args.get("recipient", "") or "")
                msg_content = str(tool_args.get("message", "") or "")
                res = FacebookTool.send_message(recipient, msg_content)
                status_msg = res.get("message", "Đã gửi tin nhắn Facebook.")
        except Exception as e:
            status_msg = f"Đã xảy ra lỗi khi thực thi lệnh: {e}"
        
        if status_msg and self.view:
            self.view.update_chat(status_msg, sender="bot")
            self.speak(status_msg)
            
    # ============================================================
    # LEGACY COMPATIBILITY
    # ============================================================
    
    @property
    def assistant_active(self):
        return self._active
    
    @property  
    def assistant_started(self):
        return self._started
    
    def set_wake_word_enabled(self, enabled):
        """Legacy."""
        self.voice.wake_word_enabled = enabled
    
    def classify_intent_simple(self, text):
        """Legacy."""
        from service.intern import IntentClassifier
        return IntentClassifier.classify(text)
