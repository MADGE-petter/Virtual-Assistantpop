"""PopController - Facade điều phối chính."""
import os
import sys
import threading

from PyQt6.QtCore import QObject, pyqtSignal

from controller.action import ActionHandler
from controller.conversation_controller import ConversationController
from model.Sql import SqlService
from service.alert_service import AlertManager
from service.analytics_service import get_analytics_service
from service.AudioService import AudioService
from service.interactive_alert_service import InteractiveAlertService
from service.user_service import UserService
from service.voice_service import VoiceService


class PopController(QObject):
    """Facade controller - chỉ điều phối, không xử lý logic chi tiết."""
    
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
            # Only load display_name if exists, don't fallback to login_username
            # Bot will ask for name if display_name is None
            loaded_name = self._user_svc.get_display_name_by_login(login_username)
            if loaded_name and loaded_name != "bạn":
                self._user_svc.display_name = loaded_name
            # else: leave as None so bot asks for name
        
        # Alert interaction service
        self._interactive_alert_service = InteractiveAlertService(self.audio, view=view)

        # Alert & Analytics - use login username when available, fall back to display name
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
        self._analytics.start()

        # Ensure app logging uses the canonical login username whenever available
        if login_username:
            try:
                self.actions.app_handler.set_login_name(login_username)
            except Exception:
                pass

        # === KHỞI TẠO SUB-CONTROLLERS ===
        self.voice = VoiceService(self.audio, view=view)
        self.user = self._user_svc  # Use UserService directly (merged UserController)
        self.alert_mgr = self._alert_mgr  # Direct reference to AlertManager
        self.analytics = self._analytics  # Direct reference to AnalyticsService
        self.conversation = ConversationController(
            self.audio,
            self.sql,
            self.actions,
            self.user,
            self._interactive_alert_service,
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
    # PUBLIC API
    # ============================================================
    
    def start(self):
        """Khởi động assistant."""
        if self._started:
            self._active = True
            return
        
        self._started = True
        self._active = True
        self.conversation.set_assistant_active(True)
        
        # Startup warmup: Load ASR on GPU -> warmup -> move to CPU
        if hasattr(self.audio, 'startup_warmup'):
            self.audio.startup_warmup()
        
        # Init intent service early to avoid race conditions
        self.conversation.init_intent_service()
        
        self.alert_mgr.start()
        self.analytics.start()
        self._enter_active_mode()
    
    def stop(self):
        """Dừng assistant."""
        self._active = False
        self.conversation.set_assistant_active(False)
        self.voice.stop_wake_word_detection()
        self.alert_mgr.stop()
        self.analytics.stop()
        self.conversation.end_session()
        # Cleanup audio models to free GPU memory
        if hasattr(self.audio, 'cleanup'):
            self.audio.cleanup()
    
    def sleep(self, manual=True):
        """Vào sleep mode."""
        self.voice.go_to_sleep(manual, self.audio.speak)
    
    def wake(self):
        """Thức dậy từ sleep."""
        self.voice.handle_wake_up()
    
    # ============================================================
    # DELEGATE METHODS 
    # ============================================================
    
    def speak(self, text):
        """Bot nói."""
        return self.voice.speak(text, update_ui=True)
    
    def listen(self):
        """Bot nghe."""
        return self.voice.get_voice_input()
    
    # ============================================================
    # PRIVATE 
    # ============================================================
    
    def _request_wake_up(self):
        """Callback từ VoiceController khi wake word detected."""
        self.wakeUpRequested.emit()
    
    def _activate_view(self):
        """Activate and show main window (helper to avoid duplication)."""
        if self.view:
            self.view.show_window()
    
    def _do_wake_up(self):
        """Thực hiện wake up trên main thread."""
        self.alert_mgr.set_sleep_mode(False)
        self.alert_mgr.reset_wellness_timers()
        
        self._activate_view()
        self._start_conversation(from_wake_up=True)
    
    def _on_go_sleep(self):
        """Callback khi vào sleep."""
        self.alert_mgr.set_sleep_mode(True)
        if self.view:
            self.view.hide_window()
    
    def _on_idle(self):
        """Callback khi idle timeout."""
        self.sleep(manual=False)
    
    def _on_alert(self, alert_data):
        """Callback khi có alert."""
        self.alertReceived.emit(alert_data)
    
    def _handle_alert_received(self, alert_data):
        if self.view:
            self.view.show_alert_notification(alert_data)
    
    def _on_interactive_alert(self, alert, action, context=None):
        """Callback khi có interactive alert - xử lý conversation với user"""
        try:
            if action == 'ask_details':
                # Hỏi user có muốn xem chi tiết không
                message = f"{alert.message}. Bạn có muốn xem tiến trình chi tiết không?"
                self.audio.speak(message)
                
            elif action == 'remind':
                # Nhắc lại cảnh báo
                message = f"Nhắc nhở: {alert.message}. Bạn có muốn xem tiến trình chi tiết không?"
                self.audio.speak(message)
                
            elif action == 'show_details':
                # Hiển thị top processes và hỏi có muốn đóng không
                from service.system_monitoring_service import (
                    format_process_list,
                    get_top_cpu_processes,
                    get_top_ram_processes,
                )
                
                if alert.metric == 'ram':
                    processes = get_top_ram_processes(5)
                    process_list = format_process_list(processes, 'ram')
                    message = f"Top 5 ứng dụng dùng RAM nhiều nhất:\n{process_list}\n\nBạn có muốn đóng ứng dụng nào không?"
                else:  # temperature
                    processes = get_top_cpu_processes(5)
                    process_list = format_process_list(processes, 'cpu')
                    message = f"Top 5 ứng dụng dùng CPU nhiều nhất:\n{process_list}\n\nBạn có muốn đóng ứng dụng nào không?"
                
                # Lưu context để parse selection sau
                self._interactive_context = {
                    'metric': alert.metric,
                    'top_processes': processes
                }
                
                self.audio.speak(message)
                
            elif action == 'ask_close_app':
                # Hỏi user muốn đóng app nào
                message = "Bạn muốn đóng ứng dụng nào? Hãy nói tên ứng dụng hoặc số thứ tự (1, 2, 3...)"
                self.audio.speak(message)
                
            elif action == 'close_success':
                # Thông báo đóng thành công
                closed_apps = context.get('closed_apps')
                failed_apps = context.get('failed_apps')
                if closed_apps:
                    app_names = ', '.join([app.get('name', 'ứng dụng') for app in closed_apps])
                    if failed_apps:
                        failed_names = ', '.join([app.get('name', 'ứng dụng') for app in failed_apps])
                        message = f"Đã đóng {app_names} thành công. Không thể đóng {failed_names}."
                    else:
                        message = f"Đã đóng {app_names} thành công."
                else:
                    closed_app = context.get('closed_app', {})
                    app_name = closed_app.get('name', 'ứng dụng')
                    message = f"Đã đóng {app_name} thành công."
                self.audio.speak(message)
                
            elif action == 'close_failed':
                # Thông báo đóng thất bại
                failed_apps = context.get('failed_apps')
                if failed_apps:
                    failed_names = ', '.join([app.get('name', 'ứng dụng') for app in failed_apps])
                    message = f"Không thể đóng {failed_names}. Vui lòng thử lại hoặc đóng thủ công."
                else:
                    failed_app = context.get('failed_app', {})
                    app_name = failed_app.get('name', 'ứng dụng')
                    message = f"Không thể đóng {app_name}. Vui lòng thử lại hoặc đóng thủ công."
                self.audio.speak(message)
                
        except Exception as e:
            print(f"[PopController] Error in interactive alert: {e}")
            import traceback
            traceback.print_exc()
    
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
        self._start_conversation()
        self.voice.start_idle_monitor(self._on_idle)
    
    def _start_conversation(self, from_wake_up: bool = False):
        """Bắt đầu conversation thread."""
        threading.Thread(target=self._run_conversation, args=(from_wake_up,), daemon=True).start()
    
    def _run_conversation(self, from_wake_up: bool = False):
        """Conversation main loop."""
        try:
            self.conversation.start_session()
            self.conversation.run_first_interaction(
                get_input_callback=self.voice.get_voice_input,
                speak_callback=self.audio.speak,
                from_wake_up=from_wake_up
            )
            self.conversation.run_main_loop(
                get_input_callback=self.voice.get_voice_input,
                on_idle_callback=lambda: self.sleep(manual=False),
                idle_timeout=45
            )
        except Exception as e:
            print(f"[PopController] Conversation error: {e}")
            import traceback
            traceback.print_exc()
    
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
