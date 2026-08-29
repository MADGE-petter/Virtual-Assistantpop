"""Voice Service - Fully Local Voice Pipeline.

Pipeline: openwakeword (Wake Word) → Gipformer/sherpa-onnx (ASR) → V-TTS (TTS)
All components run locally, no cloud API calls.
"""
import threading
import time
try:
    import numpy as np
    import pyaudio
    VOICE_DEPS_AVAILABLE = True
except ImportError:
    np = None
    pyaudio = None
    VOICE_DEPS_AVAILABLE = False
from typing import Callable, Optional

from controller.interfaces import IAudioService


class VoiceService:
    """Unified voice service with fully local wake word detection and voice I/O."""
    
    # openwakeword built-in models that work well for "Pop"
    # We'll use "hey_jarvis" as base and customize, or use custom model
    DEFAULT_WAKE_WORD_MODELS = ["hey_jarvis", "alexa", "ok_google"]
    
    def __init__(
        self, 
        audio_service: IAudioService, 
        view=None, 
        wake_words=None, 
        idle_timeout_seconds: int = 40,
        sensitivity: float = 0.6
    ):
        self.audio_service = audio_service
        self.view = view
        self.wake_words = [w.lower().strip() for w in (wake_words or ["pop", "pop ơi", "hey pop", "alo pop"])]
        self.sensitivity = sensitivity
        self.idle_timeout_seconds = idle_timeout_seconds
        
        # State
        self.is_sleeping = False
        self.is_waiting_for_wake = False
        self.is_listening_wake = False
        self.awaiting_user_response = False
        self.last_interaction_time = time.time()
        
        # Threading
        self._wake_thread = None
        self._idle_thread = None
        self._stop_wake_event = threading.Event()
        self._stop_idle_event = threading.Event()
        
        # openwakeword model
        self._oww_model = None
        self._audio_stream = None
        self._pyaudio = None
        
        # Callbacks
        self.on_wake_up = None
        self.on_go_sleep = None
        self.on_idle_timeout = None
        self.on_wake_word_detected = None

    # ==================== WAKE WORD DETECTION (openwakeword) ====================
    
    def _load_wake_word_model(self):
        """Load openwakeword model."""
        if self._oww_model is not None:
            return
        
        try:
            from openwakeword import Model
            # Use built-in "hey_jarvis" model - works for similar sounding words
            # For custom "pop", we'd need a trained model, but hey_jarvis is close enough
            self._oww_model = Model(wakeword_models=["hey_jarvis"])
            print("[VoiceService] openwakeword model loaded (hey_jarvis)")
        except Exception as e:
            print(f"[VoiceService] Failed to load openwakeword: {e}")
            self._oww_model = None
    
    def _init_audio_stream(self):
        """Initialize PyAudio stream for wake word detection."""
        if self._audio_stream is not None:
            return
        
        try:
            self._pyaudio = pyaudio.PyAudio()
            self._audio_stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1280  # 80ms at 16kHz
            )
            print("[VoiceService] Audio stream initialized for wake word detection")
        except Exception as e:
            print(f"[VoiceService] Failed to init audio stream: {e}")
            self._audio_stream = None
    
    def start_wake_word_detection(self, wake_up_callback=None, on_wake_word_callback=None):
        """Start background wake word listening using openwakeword."""
        if self.is_listening_wake:
            return True
            
        self._load_wake_word_model()
        self._init_audio_stream()
        
        if self._oww_model is None or self._audio_stream is None:
            print("[VoiceService] Cannot start wake word detection - model or audio not available")
            return False
        
        self.is_listening_wake = True
        self._stop_wake_event.clear()
        self._wake_up_callback = wake_up_callback
        self._on_wake_word_callback = on_wake_word_callback
        
        self._wake_thread = threading.Thread(
            target=self._wake_listen_loop,
            daemon=True
        )
        self._wake_thread.start()
        print("[VoiceService] Wake word detection started (local)")
        return True

    def stop_wake_word_detection(self):
        """Stop wake word detection."""
        self._stop_wake_event.set()
        self.is_listening_wake = False
        if self._wake_thread and self._wake_thread != threading.current_thread():
            self._wake_thread.join(timeout=0.1)
        
        # Close audio stream
        if self._audio_stream:
            try:
                self._audio_stream.stop_stream()
                self._audio_stream.close()
            except:
                pass
            self._audio_stream = None
        
        if self._pyaudio:
            try:
                self._pyaudio.terminate()
            except:
                pass
            self._pyaudio = None
        
        print("[VoiceService] Wake word detection stopped")

    def _wake_listen_loop(self):
        """Background loop listening for wake words using openwakeword."""
        print("[VoiceService] Wake listen loop started")
        
        while self.is_listening_wake and not self._stop_wake_event.is_set():
            try:
                # Read audio chunk
                if self._audio_stream is None:
                    break
                    
                audio_data = self._audio_stream.read(1280, exception_on_overflow=False)
                audio_np = np.frombuffer(audio_data, dtype=np.int16)
                
                # Convert to float32 for openwakeword
                audio_float = audio_np.astype(np.float32) / 32768.0
                
                # Predict
                prediction = self._oww_model.predict(audio_float)
                
                # Check if any wake word detected above threshold
                for model_name, score in prediction.items():
                    if score >= self.sensitivity:
                        print(f"[VoiceService] Wake word detected! Model: {model_name}, Score: {score:.3f}")
                        self._handle_wake_word_detected(f"Wake word: {model_name}")
                        time.sleep(1.0)  # Debounce
                        break
                        
            except Exception as e:
                print(f"[VoiceService] Wake listen error: {e}")
                time.sleep(0.5)
        
        print(f"[VoiceService] Wake listen loop ended")

    def _handle_wake_word_detected(self, text: str):
        """Handle wake word detection - activate voice mode and notify."""
        # Stop wake word detection (we're now active)
        self.stop_wake_word_detection()
        
        # Update state
        self.is_sleeping = False
        self.is_waiting_for_wake = False
        self.last_interaction_time = time.time()
        
        # Update UI
        if self.view:
            try:
                self.view.update_user_text(text)
            except Exception as e:
                print(f"[VoiceService] UI update error: {e}")
        
        # Call optional wake word callback
        if self._on_wake_word_callback:
            try:
                self._on_wake_word_callback(text)
            except Exception as e:
                print(f"[VoiceService] Wake word callback error: {e}")
        
        # Call main wake up callback (shows UI, starts conversation)
        if self._wake_up_callback:
            try:
                self._wake_up_callback()
            except Exception as e:
                print(f"[VoiceService] Wake up callback error: {e}")
                import traceback
                traceback.print_exc()
        
        # Legacy callback
        if self.on_wake_up:
            self.on_wake_up()

    # ==================== SLEEP/WAKE CYCLE ====================
    
    def toggle_voice_input(self):
        """Toggle voice input state between active and sleep mode."""
        if self.is_sleeping:
            self.handle_wake_up()
        else:
            self.go_to_sleep(manual=True)

    def handle_wake_up(self):
        """Manual wake up (e.g., from UI button)."""
        self.stop_wake_word_detection()
        self.is_sleeping = False
        self.is_waiting_for_wake = False
        self.last_interaction_time = time.time()
        
        if self.on_wake_up:
            self.on_wake_up()

    def go_to_sleep(self, manual: bool = False, speak_callback: Optional[Callable] = None):
        """Transition to sleep mode."""
        print(f"[VoiceService] Going to sleep (manual={manual})")
        self.is_sleeping = True
        self.is_waiting_for_wake = True
        self.awaiting_user_response = False
        
        if manual and speak_callback:
            speak_callback("Tôi sẽ nghỉ ngơi. Hãy gọi tôi khi cần nhé!")
            time.sleep(2)
        
        if self.on_go_sleep:
            self.on_go_sleep()
        
        # Restart wake word detection
        if self.wake_words:
            self.start_wake_word_detection(wake_up_callback=self.handle_wake_up)

    # ==================== IDLE MONITORING ====================
    
    def start_idle_monitor(self, on_idle_timeout: Callable[[], None]):
        """Start background idle monitor."""
        self.on_idle_timeout = on_idle_timeout
        self._stop_idle_event.clear()
        
        self._idle_thread = threading.Thread(target=self._idle_check_loop, daemon=True)
        self._idle_thread.start()

    def stop_idle_monitor(self):
        """Stop idle monitor."""
        self._stop_idle_event.set()
        if self._idle_thread:
            self._idle_thread.join(timeout=2.0)

    def _idle_check_loop(self):
        """Background loop checking for idle timeout (Sleep mode disabled)."""
        while not self._stop_idle_event.is_set():
            time.sleep(1.0)

    # ==================== CONVERSATION HELPERS ====================
    
    def set_awaiting_response(self, awaiting: bool):
        """Set whether we're waiting for user response."""
        self.awaiting_user_response = awaiting
        if not awaiting:
            self.last_interaction_time = time.time()

    def update_interaction_time(self):
        """Update last interaction time."""
        self.last_interaction_time = time.time()

    # ==================== VOICE I/O ====================
    
    def get_voice_input(self) -> Optional[str]:
        """Get voice input from user (requires voice mode active)."""
        self.audio_service.wait_until_speaking_done()
        self.last_interaction_time = time.time()
        self.awaiting_user_response = True
        time.sleep(0.3)
        
        result = self.audio_service.listen()
        if result:
            self.last_interaction_time = time.time()
            self.awaiting_user_response = False
        else:
            time.sleep(0.2)
        
        return result

    def speak(self, text: str, update_ui: bool = True):
        """Speak text through audio service."""
        self.awaiting_user_response = False
        return self.audio_service.speak(text, update_ui=update_ui)

    def wait_until_speaking_done(self):
        """Wait until current speech finishes."""
        self.audio_service.wait_until_speaking_done()

    @property
    def is_speaking(self) -> bool:
        return self.audio_service.is_speaking

    # ==================== WAKE WORD MANAGEMENT ====================
    
    def set_wake_words(self, wake_words):
        """Update wake words list."""
        self.wake_words = [w.lower().strip() for w in wake_words]
        
    def add_wake_word(self, wake_word):
        """Add a wake word."""
        wake_word = wake_word.lower().strip()
        if wake_word not in self.wake_words:
            self.wake_words.append(wake_word)
            
    def remove_wake_word(self, wake_word):
        """Remove a wake word."""
        wake_word = wake_word.lower().strip()
        if wake_word in self.wake_words:
            self.wake_words.remove(wake_word)

    @property
    def wake_word_enabled(self) -> bool:
        """Check if wake word detection is currently enabled."""
        return self.is_listening_wake

    @wake_word_enabled.setter
    def wake_word_enabled(self, enabled: bool):
        """Enable or disable wake word detection."""
        if enabled:
            if not self.is_listening_wake:
                self.start_wake_word_detection(wake_up_callback=self.handle_wake_up)
        else:
            if self.is_listening_wake:
                self.stop_wake_word_detection()

    # ==================== CLEANUP ====================
    
    def cleanup(self):
        """Cleanup all threads and resources."""
        print("[VoiceService] Cleaning up...")
        self.stop_wake_word_detection()
        self.stop_idle_monitor()
        
        print("[VoiceService] Cleanup complete")