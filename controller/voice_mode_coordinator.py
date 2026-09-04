"""Voice Mode Coordinator - Handles wake/sleep cycle and voice mode activation."""
from typing import Optional, Callable

from service.AudioService import AudioService
from service.voice_service import VoiceService


class VoiceModeCoordinator:
    """Handles transitions between active and sleep (voice-only) modes."""
    
    def __init__(
        self,
        audio: AudioService,
        voice: VoiceService,
        view=None,
        on_wake_up: Optional[Callable] = None,
        on_go_sleep: Optional[Callable] = None
    ):
        self.audio = audio
        self.voice = voice
        self.view = view
        self._on_wake_up = on_wake_up
        self._on_go_sleep = on_go_sleep
        self._sleeping = False
    
    def handle_wake_up(self):
        """Handle wake word detection - activate voice mode."""
        if self._sleeping:
            self._sleeping = False
        
        # Activate voice mode
        self.voice.handle_wake_up()
        
        # Show view
        if self.view:
            self.view.show()
            self.view.raise_()
            self.view.activateWindow()
        
        # Call wake up callback
        if self._on_wake_up:
            self._on_wake_up()
    
    def go_to_sleep(self, manual: bool = False, speak_callback: Optional[Callable] = None):
        """Transition to sleep mode."""
        print(f"[VoiceModeCoordinator] Going to sleep (manual={manual})")
        self._sleeping = True
        
        # Deactivate voice mode
        self.voice.go_to_sleep(manual=manual, speak_callback=speak_callback)
        
        # Hide view
        if manual and self.view:
            self.view.hide()
        
        # Call sleep callback
        if self._on_go_sleep:
            self._on_go_sleep()
    
    def wake(self):
        """Manual wake (e.g., from UI)."""
        self.handle_wake_up()
    
    def sleep(self, manual: bool = True):
        """Manual sleep."""
        self.go_to_sleep(manual=manual, speak_callback=self.audio.speak)
    
    @property
    def is_sleeping(self) -> bool:
        return self._sleeping or self.voice.is_sleeping