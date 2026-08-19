"""Conversation Coordinator - Handles conversation loop and flow."""
from typing import Optional, Callable

from service.AudioService import AudioService
from service.voice_service import VoiceService
from controller.conversation_controller import ConversationController


class ConversationCoordinator:
    """Handles conversation lifecycle and main loop."""
    
    def __init__(
        self,
        audio: AudioService,
        voice: VoiceService,
        conversation: ConversationController,
        on_idle: Optional[Callable] = None,
    ):
        self.audio = audio
        self.voice = voice
        self.conversation = conversation
        self._on_idle = on_idle
        self._active = False
    
    def start_conversation(self, from_wake_up: bool = False):
        """Start conversation in background thread."""
        import threading
        self._active = True
        self.conversation.set_assistant_active(True)
        
        thread = threading.Thread(
            target=self._run_conversation,
            args=(from_wake_up,),
            daemon=True
        )
        thread.start()
    
    def _run_conversation(self, from_wake_up: bool):
        """Run conversation loop."""
        try:
            self.conversation.start_session()
            self.conversation.run_first_interaction(
                get_input_callback=self.voice.get_voice_input,
                speak_callback=self.audio.speak,
                from_wake_up=from_wake_up
            )
            self.conversation.run_main_loop(
                get_input_callback=self.voice.get_voice_input,
                on_idle_callback=self._on_idle,
                idle_timeout=45
            )
        except Exception as e:
            print(f"[ConversationCoordinator] Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._active = False
    
    def stop(self):
        """Stop conversation."""
        self._active = False
        self.conversation.set_assistant_active(False)
        self.conversation.end_session()
    
    @property
    def active(self) -> bool:
        return self._active