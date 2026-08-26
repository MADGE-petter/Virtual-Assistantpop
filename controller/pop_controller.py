from PyQt6.QtCore import QObject, pyqtSignal

from controller.action import ActionHandler
from controller.alert_coordinator import AlertCoordinator
from controller.conversation_controller import ConversationController
from controller.conversation_coordinator import ConversationCoordinator
from controller.shutdown_coordinator import ShutdownCoordinator
from controller.startup_coordinator import StartupCoordinator
from controller.voice_mode_coordinator import VoiceModeCoordinator
from model.Sql import SqlService
from service.alert_service import AlertManager
from service.analytics_service import get_analytics_service
from service.AudioService import AudioService
from service.interactive_alert_service import InteractiveAlertService
from service.user_service import UserService
from service.voice_service import VoiceService


class PopController(QObject):
    """Facade controller - điều phối thông qua các Coordinator chuyên biệt."""
    
    # Signal để wake up từ thread khác (thread-safe)
    wakeUpRequested = pyqtSignal()
    alertReceived = pyqtSignal(dict)
    
    def __init__(self, view=None, model=None, login_username=None):
        super().__init__()
        self.view = view
        self.login_username = login_username
        
        # State
        self._started = False
        self._active = False
        
        # === KHỞI TẠO SERVICES ===
        self.audio = AudioService(view)
        self.sql = SqlService()
        self.actions = ActionHandler(self.audio, view)
        
        # User service
        self._user_svc = UserService(self.sql)
        if login_username:
            self._user_svc.login_name = login_username
            loaded_name = self._user_svc.get_display_name_by_login(login_username)
            if loaded_name and loaded_name != "bạn":
                self._user_svc.display_name = loaded_name
        
        # Alert interaction service
        self._interactive_alert_service = InteractiveAlertService(self.audio, view=view)

        # Alert & Analytics
        analytics_user = self._user_svc.login_name if getattr(self._user_svc, 'login_name', None) and self._user_svc.login_name != "bạn" else getattr(self._user_svc, 'display_name', None) or "bạn"
        self._alert_mgr = AlertManager(
            self.audio,
            self._interactive_alert_service.on_alert,
            30,
            analytics_user,
            interactive_callback=self._interactive_alert_service.on_interactive_alert,
        )
        self._interactive_alert_service.set_alert_manager(self._alert_mgr)
        self._analytics = get_analytics_service(analytics_user or "user")

        if login_username:
            try:
                self.actions.app_handler.set_login_name(login_username)
            except Exception:
                pass

        # === KHỞI TẠO SUB-CONTROLLERS & SERVICES ===
        self.voice = VoiceService(self.audio, view=view)
        self.user = self._user_svc
        self.alert_mgr = self._alert_mgr
        self.analytics = self._analytics
        self.conversation = ConversationController(
            self.audio,
            self.sql,
            self.actions,
            self.user,
            self._interactive_alert_service,
        )
        
        # === KHỞI TẠO MODULAR COORDINATORS ===
        self.alert_coordinator = AlertCoordinator(self.audio, view=view)
        self.voice_coordinator = VoiceModeCoordinator(
            audio=self.audio,
            voice=self.voice,
            alert_mgr=self._alert_mgr,
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
            alert_mgr=self._alert_mgr,
            analytics=self._analytics,
            conversation=self.conversation,
            sql=self.sql,
            user_service=self._user_svc,
            view=view
        )
        self.shutdown = ShutdownCoordinator(
            audio=self.audio,
            voice=self.voice,
            alert_mgr=self._alert_mgr,
            analytics=self._analytics,
            conversation=self.conversation
        )
        
        # === SETUP CALLBACKS ===
        self.voice.on_wake_up = self._request_wake_up
        self.voice.on_go_sleep = self._on_go_sleep
        self.voice.on_idle_timeout = self._on_idle
        self.wakeUpRequested.connect(self._do_wake_up)
        self.alertReceived.connect(self._handle_alert_received)
        
        # Inject controller vào view (view không cần biết services)
        if view:
            view.set_controller(self)
            # Connect View signals to Controller slots
            view.sendMessage.connect(self._on_send_message)
            view.voiceToggled.connect(self._on_voice_toggled)
            view.stopGeneration.connect(self._on_stop_generation)
            view.newConversation.connect(self._on_new_conversation)
            view.switchModel.connect(self._on_switch_model)
            view.openSettings.connect(self._on_open_settings)
            view.searchConversations.connect(self._on_search_conversations)
            view.loadConversation.connect(self._on_load_conversation)
            view.deleteConversation.connect(self._on_delete_conversation)
            view.viewClosed.connect(self._on_view_closed)
    
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
        self.conversation.start_new_conversation()
        if self.view:
            self.view.show_welcome()
    
    def _on_switch_model(self):
        """Handle model switch request."""
        # TODO: Implement model switching
        if self.view:
            self.view.show_toast("Model switching coming soon", "info")
    
    def _on_open_settings(self):
        """Handle open settings request."""
        # TODO: Implement settings dialog
        if self.view:
            self.view.show_toast("Settings dialog coming soon", "info")
    
    def _on_search_conversations(self, query: str):
        """Handle conversation search."""
        # TODO: Implement conversation search
        pass
    
    def _on_load_conversation(self, conversation_id: str):
        """Handle load conversation request."""
        # TODO: Implement conversation loading
        pass
    
    def _on_delete_conversation(self, conversation_id: str):
        """Handle delete conversation request."""
        # TODO: Implement conversation deletion
        pass
    
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
        """Thực hiện wake up trên main thread."""
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
    
    def _on_alert(self, alert_data):
        """Callback khi có alert."""
        self.alertReceived.emit(alert_data)
    
    def _handle_alert_received(self, alert_data):
        if self.view:
            self.view.show_alert_notification(alert_data)
    
    def _on_interactive_alert(self, alert, action, context=None):
        """Callback khi có interactive alert - ủy quyền cho AlertCoordinator."""
        self.alert_coordinator.handle_interactive_alert(alert, action, context=context)
    
    def _on_gesture(self, gesture_type):
        """Callback từ gesture service."""
        self.handle_gesture(gesture_type)
    
    # ============================================================
    # PRIVATE - Conversation management
    # ============================================================
    
    def _enter_active_mode(self):
        """Vào active mode - hiện app và bắt đầu conversation."""
        self._activate_view()
        self.alert_mgr.reset_wellness_timers()
        self.conversation_coordinator.start_conversation(from_wake_up=False)
        self.voice.start_idle_monitor(self._on_idle)
    
    def _start_conversation(self, from_wake_up: bool = False):
        """Bắt đầu conversation thread qua ConversationCoordinator."""
        self.conversation_coordinator.start_conversation(from_wake_up=from_wake_up)
    
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
