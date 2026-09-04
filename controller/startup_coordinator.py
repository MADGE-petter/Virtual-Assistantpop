"""Startup Coordinator - Handles assistant initialization and warmup."""
from typing import Optional, Callable

from service.AudioService import AudioService
from service.voice_service import VoiceService
from service.analytics_service import AnalyticsService
from controller.conversation_controller import ConversationController
from model.Sql import SqlService


import threading


class StartupCoordinator:
    """Handles assistant startup sequence."""
    
    def __init__(
        self,
        audio: AudioService,
        voice: VoiceService,
        analytics: AnalyticsService,
        conversation: ConversationController,
        sql: SqlService,
        user_service,
        view=None
    ):
        self.audio = audio
        self.voice = voice
        self.analytics = analytics
        self.conversation = conversation
        self.sql = sql
        self.user_service = user_service
        self.view = view
        self._started = False
    
    def start(self, login_username: Optional[str] = None) -> bool:
        """Execute startup sequence asynchronously so GUI renders instantaneously (<0.1s)."""
        if self._started:
            return True
        
        self._started = True
        print("[StartupCoordinator] Starting assistant in background...")

        def _async_bg_worker():
            try:
                # 1. Audio warmup (ASR on GPU -> inference -> CPU)
                if hasattr(self.audio, 'startup_warmup'):
                    self.audio.startup_warmup()
                
                # 2. Start monitoring services (Analytics only)
                self.analytics.start()
                
                # 3. Set user name for app handler
                if login_username:
                    try:
                        if hasattr(self.conversation, 'service') and hasattr(self.conversation.service, 'actions'):
                            self.conversation.service.actions.app_handler.set_login_name(login_username)
                    except Exception:
                        pass
                        
                # 4. Start ProactiveService
                try:
                    from service.proactive_service import get_proactive_service
                    proactive = get_proactive_service(user_id=1, callback=self.audio.speak)
                    proactive.start()
                except Exception as e:
                    print(f"[StartupCoordinator] Error starting ProactiveService: {e}")
                    
                print("[StartupCoordinator] Async background startup complete.")
            except Exception as e:
                print(f"[StartupCoordinator] Async startup warning: {e}")

        bg_thread = threading.Thread(target=_async_bg_worker, name="PopAsyncStartup", daemon=True)
        bg_thread.start()
        return True
    
    def enter_active_mode(self, activate_view: Callable, start_conversation: Callable):
        """Enter active mode after startup."""
        if not self._started:
            return
        
        # Activate view
        activate_view()
        
        # Start conversation
        start_conversation(from_wake_up=False)
        
        # Start idle monitor
        self.voice.start_idle_monitor(lambda: None)  # Callback set by PopController
    
    @property
    def started(self) -> bool:
        return self._started