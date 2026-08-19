"""Startup Coordinator - Handles assistant initialization and warmup."""
from typing import Optional, Callable

from service.AudioService import AudioService
from service.voice_service import VoiceService
from service.alert_service import AlertManager
from service.analytics_service import AnalyticsService
from controller.conversation_controller import ConversationController
from model.Sql import SqlService


class StartupCoordinator:
    """Handles assistant startup sequence."""
    
    def __init__(
        self,
        audio: AudioService,
        voice: VoiceService,
        alert_mgr: AlertManager,
        analytics: AnalyticsService,
        conversation: ConversationController,
        sql: SqlService,
        user_service,
        view=None
    ):
        self.audio = audio
        self.voice = voice
        self.alert_mgr = alert_mgr
        self.analytics = analytics
        self.conversation = conversation
        self.sql = sql
        self.user_service = user_service
        self.view = view
        self._started = False
    
    def start(self, login_username: Optional[str] = None) -> bool:
        """Execute startup sequence."""
        if self._started:
            return True
        
        print("[StartupCoordinator] Starting assistant...")
        
        # 1. Audio warmup (ASR on GPU -> inference -> CPU)
        if hasattr(self.audio, 'startup_warmup'):
            self.audio.startup_warmup()
        
        # 2. Initialize intent service
        self.conversation.init_intent_service()
        
        # 3. Start monitoring services
        self.alert_mgr.start()
        self.analytics.start()
        
        # 4. Set user name for app handler
        if login_username:
            try:
                from controller.action import ActionHandler
                # Access app_handler through conversation -> actions
                if hasattr(self.conversation, 'service') and hasattr(self.conversation.service, 'actions'):
                    self.conversation.service.actions.app_handler.set_login_name(login_username)
            except Exception:
                pass
        
        self._started = True
        print("[StartupCoordinator] Startup complete")
        return True
    
    def enter_active_mode(self, activate_view: Callable, start_conversation: Callable):
        """Enter active mode after startup."""
        if not self._started:
            return
        
        # Activate view
        activate_view()
        
        # Reset wellness timers
        self.alert_mgr.reset_wellness_timers()
        
        # Start conversation
        start_conversation(from_wake_up=False)
        
        # Start idle monitor
        self.voice.start_idle_monitor(lambda: None)  # Callback set by PopController
    
    @property
    def started(self) -> bool:
        return self._started