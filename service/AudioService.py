"""AudioService - sherpa-onnx Vietnamese ASR + TTS.

Lightweight architecture optimized for RTX 2050 4GB VRAM:
- ASR: sherpa-onnx Zipformer Vietnamese (offline) - runs on CPU/GPU
- TTS: sherpa-onnx Piper Vietnamese (offline) - runs on CPU
- No VRAM management needed - models are tiny (~30M + ~50M params)
- No sequential loading complexity - both models fit easily in memory
- Models downloaded from GitHub releases (public, no auth required)
"""
import os
import threading
import time
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional

try:
    import numpy as np
    import soundfile as sf
    AUDIO_DEPS_AVAILABLE = True
except ImportError:
    np = None
    sf = None
    AUDIO_DEPS_AVAILABLE = False

# New lightweight imports
try:
    import sherpa_onnx
    SHERPA_AVAILABLE = True
except ImportError:
    SHERPA_AVAILABLE = False
    sherpa_onnx = None

# Fallback for audio playback
try:
    import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False


class AudioService:
    """Lightweight Audio Service using sherpa-onnx Vietnamese ASR + TTS."""
    
    # Model configurations - publicly available on GitHub releases
    ASR_MODEL_CONFIG = {
        "name": "sherpa-onnx-zipformer-vi-30M-int8-2026-02-09",
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-zipformer-vi-30M-int8-2026-02-09.tar.bz2",
        "encoder": "encoder-epoch-12-avg-2-chunk-16-left-64.int8.onnx",
        "decoder": "decoder-epoch-12-avg-2-chunk-16-left-64.int8.onnx",
        "joiner": "joiner-epoch-12-avg-2-chunk-16-left-64.int8.onnx",
        "tokens": "tokens.txt",
        "sample_rate": 16000,
        "feature_dim": 80,
    }
    
    TTS_MODEL_CONFIG = {
        "name": "vits-piper-vi_VN-25hours_single-low",
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-vi_VN-25hours_single-low.tar.bz2",
        "model": "vi_VN-25hours_single-low.onnx",
        "tokens": "tokens.txt",
        "data_dir": "espeak-ng-data",
        "sample_rate": 22050,
    }
    
    def __init__(self, view=None):
        self.view = view
        self.assistant_name = "Pop"
        
        # Thread safety
        self.gate_lock = threading.Lock()
        self.is_speaking = False
        self.is_listening = False
        
        # Cooldown after speaking
        self.post_speak_cooldown = 0.3
        self.last_speak_end_time = 0
        
        # Models directory
        self.models_dir = os.path.join(os.path.dirname(__file__), "..", "LLM-agents")
        self.asr_model_dir = os.path.join(self.models_dir, self.ASR_MODEL_CONFIG["name"])
        self.tts_model_dir = os.path.join(self.models_dir, self.TTS_MODEL_CONFIG["name"])
        
        # Models (lazy loaded)
        self._asr_recognizer = None
        self._tts_engine = None
        
        print(f"[AudioService] Initialized. sherpa-onnx: {SHERPA_AVAILABLE}")
        if not SHERPA_AVAILABLE:
            print("[AudioService] WARNING: sherpa-onnx not available. ASR/TTS will not work.")
    
    # ==================== MODEL DOWNLOAD ====================
    
    def _download_and_extract(self, url: str, dest_dir: str) -> bool:
        """Download and extract a model from GitHub releases."""
        if os.path.exists(dest_dir):
            print(f"[AudioService] Model already exists at {dest_dir}")
            return True
        
        print(f"[AudioService] Downloading model from {url}...")
        os.makedirs(dest_dir, exist_ok=True)
        
        try:
            # Download to temp file
            temp_file = os.path.join(tempfile.gettempdir(), os.path.basename(url))
            urllib.request.urlretrieve(url, temp_file)
            
            # Extract
            print(f"[AudioService] Extracting to {dest_dir}...")
            if url.endswith('.tar.bz2'):
                import tarfile
                with tarfile.open(temp_file, 'r:bz2') as tar:
                    tar.extractall(dest_dir)
            elif url.endswith('.zip'):
                with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                    zip_ref.extractall(dest_dir)
            
            # Cleanup
            os.remove(temp_file)
            print(f"[AudioService] Model extracted successfully!")
            return True
            
        except Exception as e:
            print(f"[AudioService] Download failed: {e}")
            return False
    
    def _ensure_asr_model(self) -> bool:
        """Ensure ASR model is downloaded."""
        return self._download_and_extract(
            self.ASR_MODEL_CONFIG["url"],
            self.asr_model_dir
        )
    
    def _ensure_tts_model(self) -> bool:
        """Ensure TTS model is downloaded."""
        return self._download_and_extract(
            self.TTS_MODEL_CONFIG["url"],
            self.tts_model_dir
        )
    
    # ==================== MODEL LOADING ====================
    
    def _load_asr_model(self):
        """Load Vietnamese Zipformer ASR model via sherpa-onnx (offline)."""
        if self._asr_recognizer is not None:
            return
            
        if not SHERPA_AVAILABLE:
            raise RuntimeError("sherpa-onnx not installed")
        
        # Ensure model is downloaded
        if not self._ensure_asr_model():
            raise RuntimeError("Failed to download ASR model")
        
        print("[AudioService] Loading Vietnamese Zipformer ASR model (30M params, int8)...")
        
        # Model files are nested one level deeper
        model_subdir = os.path.join(self.asr_model_dir, self.ASR_MODEL_CONFIG["name"])
        encoder_path = os.path.join(model_subdir, "encoder.int8.onnx")
        decoder_path = os.path.join(model_subdir, "decoder.onnx")
        joiner_path = os.path.join(model_subdir, "joiner.int8.onnx")
        tokens_path = os.path.join(model_subdir, "tokens.txt")
        
        self._asr_recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
            tokens=tokens_path,
            encoder=encoder_path,
            decoder=decoder_path,
            joiner=joiner_path,
            num_threads=4,
            sample_rate=self.ASR_MODEL_CONFIG["sample_rate"],
            feature_dim=self.ASR_MODEL_CONFIG["feature_dim"],
            decoding_method="greedy_search",
        )
        print("[AudioService] Vietnamese Zipformer ASR loaded successfully!")
    
    def _load_tts_model(self):
        """Load Vietnamese Piper TTS model via sherpa-onnx (offline)."""
        if self._tts_engine is not None:
            return
            
        if not SHERPA_AVAILABLE:
            raise RuntimeError("sherpa-onnx not installed")
        
        # Ensure model is downloaded
        if not self._ensure_tts_model():
            raise RuntimeError("Failed to download TTS model")
        
        print("[AudioService] Loading Vietnamese Piper TTS model...")
        
        # Model files are nested one level deeper
        model_subdir = os.path.join(self.tts_model_dir, self.TTS_MODEL_CONFIG["name"])
        model_path = os.path.join(model_subdir, self.TTS_MODEL_CONFIG["model"])
        tokens_path = os.path.join(model_subdir, self.TTS_MODEL_CONFIG["tokens"])
        data_dir = os.path.join(model_subdir, self.TTS_MODEL_CONFIG["data_dir"])
        
        # Create config for VITS Piper model
        config = sherpa_onnx.OfflineTtsConfig()
        config.model.vits.model = model_path
        config.model.vits.tokens = tokens_path
        config.model.vits.data_dir = data_dir
        config.model.num_threads = 4
        config.model.debug = False
        
        self._tts_engine = sherpa_onnx.OfflineTts(config)
        print("[AudioService] Vietnamese Piper TTS loaded successfully!")
    
    # ==================== STARTUP ====================
    
    def startup_warmup(self):
        """Startup: Pre-load both models (they're small, no VRAM issues)."""
        print("=== STARTUP WARMUP (Lightweight) ===")
        
        # Load ASR
        try:
            self._load_asr_model()
        except Exception as e:
            print(f"[AudioService] ASR load failed: {e}")
        
        # Load TTS
        try:
            self._load_tts_model()
        except Exception as e:
            print(f"[AudioService] TTS load failed: {e}")
        
        print("[AudioService] Startup complete - Ready to use!")
    
    # ==================== SPEAK (TTS) ====================
    
    def speak(self, text: str, update_ui: bool = True, speaker: str = None) -> bool:
        """Synthesize and play speech using sherpa-onnx Piper TTS."""
        # Piper TTS doesn't support multiple speakers, ignore speaker parameter
        threading.Thread(
            target=self._speak_worker,
            args=(text, update_ui),
            daemon=True
        ).start()
        return True
    
    def _speak_worker(self, text: str, update_ui: bool):
        self.gate_lock.acquire()
        self.is_speaking = True
        
        try:
            if update_ui and self.view:
                self.view.update_bot_text(text)
            
            print(f"[BOT] {text}")
            
            if SHERPA_AVAILABLE:
                self._synthesize_and_play(text)
            else:
                # Fallback
                time.sleep(len(text) * 0.05)
            
            time.sleep(0.3)  # Cooldown
            
        finally:
            self.is_speaking = False
            self.last_speak_end_time = time.time()
            self._mic_warmup()
            self.gate_lock.release()
    
    def _synthesize_and_play(self, text: str):
        """Synthesize with sherpa-onnx Piper TTS and play."""
        # Load TTS model if needed
        self._load_tts_model()
        
        # Generate audio using sherpa-onnx OfflineTts
        # Returns GeneratedAudio object with samples and sample_rate
        generated_audio = self._tts_engine.generate(text)
        
        # Extract samples and sample rate from GeneratedAudio
        audio = generated_audio.samples
        sr = generated_audio.sample_rate
        
        # Save to temp file and play
        temp_path = os.path.join(tempfile.gettempdir(), f"tts_output_{int(time.time()*1000)}.wav")
        
        # Ensure correct shape
        if hasattr(audio, 'ndim') and audio.ndim > 1:
            audio = audio.squeeze()
        
        sf.write(temp_path, audio, sr)
        
        # Play
        if PLAYSOUND_AVAILABLE:
            playsound.playsound(temp_path, True)
        else:
            # Fallback: use sounddevice to play
            import sounddevice as sd
            sd.play(audio, sr)
            sd.wait()
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    def _mic_warmup(self):
        time.sleep(0.1)
    
    # ==================== LISTEN (ASR) ====================
    
    def listen(self, timeout: int = 12, phrase_time_limit: int = 10) -> Optional[str]:
        """Listen and transcribe using Vietnamese Zipformer via sherpa-onnx (offline)."""
        if self.is_listening:
            return None
        
        # Check cooldown after bot speaks
        time_since_speak = time.time() - self.last_speak_end_time
        if time_since_speak < self.post_speak_cooldown:
            return None
        
        got_lock = self.gate_lock.acquire(timeout=0.5)
        if not got_lock:
            return None
        
        try:
            self.is_listening = True
            
            if not SHERPA_AVAILABLE:
                return "..."
            
            # Update UI
            if self.view:
                self.view.update_user_text("Đang lắng nghe...")
            
            try:
                import speech_recognition as sr
                r = sr.Recognizer()
                with sr.Microphone() as source:
                    r.pause_threshold = 0.8
                    r.energy_threshold = 300
                    audio = r.listen(source, phrase_time_limit=phrase_time_limit, timeout=timeout)
                
                # Save audio to temp file for sherpa-onnx
                temp_path = os.path.join(tempfile.gettempdir(), f"asr_input_{int(time.time()*1000)}.wav")
                with open(temp_path, "wb") as f:
                    f.write(audio.get_wav_data())
                
                # Transcribe with Gipformer
                text = self._transcribe_audio(temp_path)
                
                # Cleanup
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
                # Update UI
                if self.view and text:
                    self.view.update_user_text(text)
                
                print(f"[USER] {text}")
                return text
                
            except ImportError:
                print("[AudioService] speech_recognition not installed, using sherpa-onnx ASR directly")
                # Fallback to sherpa-onnx ASR directly
                return self._listen_with_sherpa(timeout, phrase_time_limit)
            except sr.UnknownValueError:
                if self.view:
                    self.view.update_user_text("Pop không nghe rõ...")
                return "..."
            except sr.RequestError as e:
                return "..."
            except Exception as e:
                print(f"[AudioService] Listen error: {e}")
                return "..."
                
        finally:
            self.is_listening = False
            self.gate_lock.release()
    
    def _transcribe_audio(self, audio_path: str) -> Optional[str]:
        """Transcribe audio file using Vietnamese Zipformer via sherpa-onnx (offline)."""
        if self._asr_recognizer is None:
            self._load_asr_model()
        
        # Read audio file
        import soundfile as sf
        audio_data, sample_rate = sf.read(audio_path)
        
        # Resample to 16kHz if needed
        if sample_rate != 16000:
            import librosa
            audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)
        
        # Convert to float32
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        
        # Use offline recognizer - simpler API
        stream = self._asr_recognizer.create_stream()
        stream.accept_waveform(16000, audio_data)
        self._asr_recognizer.decode_stream(stream)
        
        result = self._asr_recognizer.get_result(stream)
        text = result.text.strip()
        
        return text if text else None
    
    def _listen_with_sherpa(self, timeout: int = 12, phrase_time_limit: int = 10) -> Optional[str]:
        """Listen using sherpa-onnx ASR directly (without speech_recognition)."""
        try:
            import sounddevice as sd
            import numpy as np
            
            # Record audio
            sample_rate = 16000
            duration = phrase_time_limit
            print(f"[AudioService] Recording for {duration}s...")
            
            audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
            sd.wait()
            audio_data = audio_data.flatten()
            
            # Save to temp file
            temp_path = os.path.join(tempfile.gettempdir(), f"asr_input_{int(time.time()*1000)}.wav")
            sf.write(temp_path, audio_data, sample_rate)
            
            # Transcribe
            text = self._transcribe_audio(temp_path)
            
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            # Update UI
            if self.view and text:
                self.view.update_user_text(text)
            
            print(f"[USER] {text}")
            return text
            
        except Exception as e:
            print(f"[AudioService] Sherpa listen error: {e}")
            return "..."
    
    def get_text_with_retry(self, max_retries: int = 3, retry_message: str = None) -> str:
        """Get text with retry mechanism."""
        if retry_message is None:
            retry_message = f"{self.assistant_name} không nghe rõ, bạn có thể nói lại không?"
        
        for i in range(max_retries):
            text = self.listen()
            if text and text != "..." and text != 0:
                return text.lower()
            elif i < max_retries - 1:
                self.speak(retry_message)
        
        self.speak("Tôi không nghe rõ. Tôi sẽ hỏi lại sau.")
        return "..."
    
    def wait_until_speaking_done(self):
        while self.is_speaking:
            time.sleep(0.05)
    
    def stop_speaking(self):
        """Stop current speech."""
        self.is_speaking = False
    
    def is_gate_open(self) -> bool:
        return not self.is_speaking
    
    # ==================== CLEANUP ====================
    
    def cleanup(self):
        """Cleanup models."""
        print("[AudioService] Cleaning up...")
        
        if self._asr_recognizer is not None:
            del self._asr_recognizer
            self._asr_recognizer = None
        
        if self._tts_engine is not None:
            del self._tts_engine
            self._tts_engine = None
        
        print("[AudioService] Cleanup complete")


# Backward compatibility alias
AudioService_Nemo = AudioService