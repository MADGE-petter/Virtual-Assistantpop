"""Shutdown Coordinator - Handles assistant cleanup and shutdown."""
from typing import Optional

from service.AudioService import AudioService
from service.voice_service import VoiceService
from service.analytics_service import AnalyticsService
from controller.conversation_controller import ConversationController


import threading


class ShutdownCoordinator:
    """Handles assistant shutdown sequence."""
    
    def __init__(
        self,
        audio: AudioService,
        voice: VoiceService,
        analytics: AnalyticsService,
        conversation: ConversationController,
    ):
        self.audio = audio
        self.voice = voice
        self.analytics = analytics
        self.conversation = conversation
        self._active = True
    
    def stop(self):
        """Execute fast non-blocking shutdown sequence."""
        if not self._active:
            return
        
        self._active = False
        print("[ShutdownCoordinator] Initiating fast non-blocking shutdown...")
        
        # 1. Deactivate conversation immediately
        try:
            self.conversation.set_assistant_active(False)
        except Exception:
            pass
        
        def _async_teardown():
            try:
                # 2. Stop voice detection
                self.voice.stop_wake_word_detection()
                self.voice.stop_idle_monitor()
                
                # 3. Stop monitoring services
                self.analytics.stop()
                
                # 4. End conversation session
                self.conversation.end_session()
                # 5. Stop ProactiveService
                try:
                    from service.proactive_service import get_proactive_service
                    get_proactive_service().stop()
                except Exception as e:
                    print(f"[ShutdownCoordinator] Error stopping ProactiveService: {e}")
                    
                # 6. Cleanup audio models
                if hasattr(self.audio, 'cleanup'):
                    self.audio.cleanup()
                
                # 7. Cleanup voice service
                self.voice.cleanup()
                print("[ShutdownCoordinator] Shutdown cleanup complete.")
            except Exception as e:
                print(f"[ShutdownCoordinator] Teardown warning: {e}")

        teardown_thread = threading.Thread(target=_async_teardown, name="PopAsyncShutdown", daemon=True)
        teardown_thread.start()
    
    @property
    def active(self) -> bool:
        return self._active