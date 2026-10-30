"""AudioService - sherpa-onnx Vietnamese ASR + MeloTTS Vietnamese TTS.

Lightweight architecture:
- ASR: sherpa-onnx Zipformer Vietnamese (offline) - runs on CPU/GPU
- TTS: MeloTTS Vietnamese VITS-2 (offline, high naturalness) - runs on CPU/GPU
"""
import os
import threading
import time
import tempfile
import urllib.request
import zipfile
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
    playsound = None  # type: ignore
    PLAYSOUND_AVAILABLE = False

# Speech recognition for microphone capture
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    sr = None
    SR_AVAILABLE = False



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
        "name": "melotts",
        "config_path": "checkpoints/config.json",
        "ckpt_path": "checkpoints/G_463000.pth",
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
        self.last_speak_end_time: float = 0.0
        
        # Models directory
        try:
            from utils.paths import resource_path
            self.models_dir = resource_path("voice-models")
        except Exception:
            self.models_dir = os.path.join(os.path.dirname(__file__), "..", "voice-models")
        self.asr_model_dir = os.path.join(self.models_dir, self.ASR_MODEL_CONFIG["name"])
        self.tts_model_dir = os.path.join(self.models_dir, self.TTS_MODEL_CONFIG["name"])
        
        # Models (lazy loaded)
        self._asr_recognizer = None
        self._tts_engine = None
        self._tts_speaker_id = 0
        
        print(f"[AudioService] Initialized. sherpa-onnx: {SHERPA_AVAILABLE}, MeloTTS: True")
        if not SHERPA_AVAILABLE:
            print("[AudioService] WARNING: sherpa-onnx not available. ASR/TTS will not work.")
    
    # ==================== MODEL FILE HELPERS ====================

    def _find_file(self, base_dir: str, target_name: str) -> Optional[str]:
        """Search recursively for a target file within base_dir."""
        if not os.path.exists(base_dir):
            return None
        for root, _, files in os.walk(base_dir):
            if target_name in files:
                return os.path.join(root, target_name)
        return None

    def _find_dir(self, base_dir: str, target_name: str) -> Optional[str]:
        """Search recursively for a target directory within base_dir."""
        if not os.path.exists(base_dir):
            return None
        for root, dirs, _ in os.walk(base_dir):
            if target_name in dirs:
                return os.path.join(root, target_name)
        return None

    # ==================== MODEL DOWNLOAD ====================
    
    def _download_and_extract(self, url: str, dest_dir: str, required_file: str) -> bool:
        """Download and extract a model from GitHub releases if required file is missing."""
        found = self._find_file(dest_dir, required_file)
        if found and os.path.exists(found):
            print(f"[AudioService] Model already exists at {found}")
            return True
        
        print(f"[AudioService] Downloading model from {url}...")
        os.makedirs(dest_dir, exist_ok=True)
        
        try:
            # Download to temp file
            temp_file = os.path.join(tempfile.gettempdir(), os.path.basename(url))
            if not os.path.exists(temp_file):
                print(f"[AudioService] Retrieving {url}...")
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
            if os.path.exists(temp_file):
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
            self.asr_model_dir,
            "encoder.int8.onnx"
        )
    
    def _ensure_tts_model(self) -> bool:
        """Ensure MeloTTS model checkpoint is downloaded."""
        ckpt_path = os.path.join(self.tts_model_dir, "checkpoints", "G_463000.pth")
        cfg_path = os.path.join(self.tts_model_dir, "checkpoints", "config.json")
        return os.path.exists(ckpt_path) and os.path.exists(cfg_path)
    
    # ==================== MODEL LOADING ====================
    
    def _load_asr_model(self):
        """Load Vietnamese Zipformer ASR model via sherpa-onnx (offline)."""
        if self._asr_recognizer is not None:
            return
            
        if not SHERPA_AVAILABLE or sherpa_onnx is None:
            raise RuntimeError("sherpa-onnx not installed")
        
        # Ensure model is downloaded
        if not self._ensure_asr_model():
            raise RuntimeError("Failed to download ASR model")
        
        print("[AudioService] Loading Vietnamese Zipformer ASR model (30M params, int8)...")
        
        encoder_path = self._find_file(self.asr_model_dir, "encoder.int8.onnx") or self._find_file(self.asr_model_dir, self.ASR_MODEL_CONFIG.get("encoder", ""))
        decoder_path = self._find_file(self.asr_model_dir, "decoder.onnx") or self._find_file(self.asr_model_dir, self.ASR_MODEL_CONFIG.get("decoder", ""))
        joiner_path = self._find_file(self.asr_model_dir, "joiner.int8.onnx") or self._find_file(self.asr_model_dir, self.ASR_MODEL_CONFIG.get("joiner", ""))
        tokens_path = self._find_file(self.asr_model_dir, "tokens.txt")
        
        if not (encoder_path and decoder_path and joiner_path and tokens_path):
            raise RuntimeError(f"Missing ASR model files in {self.asr_model_dir}")
        
        provider = "cpu"
        self._asr_recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
            tokens=tokens_path,
            encoder=encoder_path,
            decoder=decoder_path,
            joiner=joiner_path,
            num_threads=4,
            sample_rate=self.ASR_MODEL_CONFIG["sample_rate"],
            feature_dim=self.ASR_MODEL_CONFIG["feature_dim"],
            decoding_method="greedy_search",
            provider=provider,
        )
        print(f"[AudioService] Vietnamese Zipformer ASR loaded successfully on RAM/CPU (provider={provider})!")
    
    def _get_voice_device(self) -> str:
        """Get target compute device for voice models (default: cpu / system RAM)."""
        env_dev = os.environ.get("POP_VOICE_DEVICE")
        if env_dev:
            return env_dev.strip().lower()
        try:
            from view.ui.settings.settings_config import load_user_settings
            cfg = load_user_settings()
            return cfg.get("voice_device", "cpu").strip().lower()
        except Exception:
            return "cpu"

    def _load_tts_model(self):
        """Load Vietnamese MeloTTS model (offline)."""
        if self._tts_engine is not None:
            return
            
        import sys
        melotts_dir = self.tts_model_dir
        if melotts_dir not in sys.path:
            sys.path.insert(0, melotts_dir)
            
        config_path = os.path.join(melotts_dir, "checkpoints", "config.json")
        ckpt_path = os.path.join(melotts_dir, "checkpoints", "G_463000.pth")
        
        if not (os.path.exists(config_path) and os.path.exists(ckpt_path)):
            raise RuntimeError(f"Missing MeloTTS checkpoint files in {melotts_dir}/checkpoints")
            
        try:
            import torch
            from melo.api import TTS  # type: ignore
        except ImportError as e:
            raise RuntimeError(f"MeloTTS dependencies missing: {e}")
            
        # Voice models run on RAM/CPU to reserve VRAM for LLM on eGPU
        target_dev = self._get_voice_device()
        if target_dev == "cpu":
            device = "cpu"
        else:
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"[AudioService] Loading Vietnamese MeloTTS model on {device} (RAM/CPU mode: {device == 'cpu'})...")
        
        model = TTS(
            language="VI",
            device=device,
            use_hf=False,
            config_path=config_path,
            ckpt_path=ckpt_path
        )
        self._tts_engine = model
        # MeloTTS stores config dynamically in HParams at runtime
        hps_data = getattr(model.hps, "data", None)
        spk2id = getattr(hps_data, "spk2id", {}) if hps_data is not None else {}
        self._tts_speaker_id = list(spk2id.values())[0] if spk2id else 0
        print("[AudioService] Vietnamese MeloTTS loaded successfully on RAM/CPU!")
    
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
    
    def speak(self, text: str, update_ui: bool = True, speaker: Optional[str] = None) -> bool:
        """Synthesize and play speech using sherpa-onnx Piper TTS."""
        # Piper TTS doesn't support multiple speakers, ignore speaker parameter
        threading.Thread(
            target=self._speak_worker,
            args=(text, update_ui),
            daemon=True
        ).start()
        return True
    
    def _speak_worker(self, text: str, update_ui: bool):
        # 1. Update UI ngay lập tức để chat và thinking indicator được cập nhật, không bị phụ thuộc vào audio
        try:
            if update_ui and self.view:
                self.view.update_bot_text(text)
        except Exception as e:
            print(f"[AudioService] Error updating UI text: {e}")

        print(f"[BOT] {text}")

        # 2. Acquire lock có timeout để không bị deadlock nếu audio đang bận
        got_lock = self.gate_lock.acquire(timeout=2.0)
        if not got_lock:
            print("[AudioService] Could not acquire audio lock for speaking (timeout). Skipping TTS.")
            return

        self.is_speaking = True
        try:
            if SHERPA_AVAILABLE:
                try:
                    self._synthesize_and_play(text)
                except Exception as tts_err:
                    print(f"[AudioService] TTS synthesis warning: {tts_err}")
                    time.sleep(min(3.0, len(text) * 0.05))
            else:
                # Native System Fallback (macOS 'say -v Linh' / Windows pyttsx3)
                try:
                    import subprocess
                    import platform
                    if platform.system() == "Darwin":
                        subprocess.run(["say", "-v", "Linh", text], check=False)
                    else:
                        time.sleep(min(3.0, len(text) * 0.05))
                except Exception:
                    time.sleep(min(3.0, len(text) * 0.05))
            
            time.sleep(0.3)  # Cooldown
            
        finally:
            self.is_speaking = False
            self.last_speak_end_time = time.time()
            self._mic_warmup()
            self.gate_lock.release()
    
    def _get_equipped_character_id(self) -> str:
        """Return currently equipped mascot character ID."""
        try:
            from service.collection import get_collection_service
            svc = get_collection_service()
            char = svc.equipped()
            return char.id if char else "pop"
        except Exception:
            return "pop"

    def play_mascot_sfx(self, char_id: Optional[str] = None) -> None:
        """Play Phoebe Chupi ('Phoebe Chupi!') or Nono ('Nono~!') authentic voice sample asynchronously."""
        cid = char_id or self._get_equipped_character_id()
        if cid not in ("phoebe_chuby", "nono_chubby"):
            return

        sample_file = "phoebe_chupi.wav" if cid == "phoebe_chuby" else "nono_chubby.wav"
        sample_path = os.path.join(self.models_dir, "samples", sample_file)
        if not os.path.isfile(sample_path):
            return

        def _worker():
            try:
                if sf is not None:
                    data, sr_rate = sf.read(sample_path)
                    import sounddevice as sd
                    sd.play(data, sr_rate)
                    sd.wait()
                elif PLAYSOUND_AVAILABLE and playsound is not None:
                    playsound.playsound(sample_path, True)
            except Exception as e:
                print(f"[AudioService] SFX play error: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_character_voice_clone(self, audio: "np.ndarray", sr_rate: int, char_id: str) -> "np.ndarray":
        """Transform TTS audio pitch & timbre to match Phoebe Chupi (~452Hz) or Nono (~422Hz) authentic voice."""
        if char_id not in ("phoebe_chuby", "nono_chubby") or np is None:
            return audio
        try:
            import librosa
            # Phoebe Chupi: ~452Hz (+5.8 semitones) | Nono (Nuonuo): ~422Hz (+4.6 semitones)
            n_steps = 5.8 if char_id == "phoebe_chuby" else 4.6
            shifted = librosa.effects.pitch_shift(
                y=audio.astype(np.float32),
                sr=sr_rate,
                n_steps=n_steps
            )
            # Gentle high-shelf brightness boost for crisp anime vocal timbre
            pre_emphasis = 0.18 if char_id == "phoebe_chuby" else 0.14
            bright = np.append(shifted[0], shifted[1:] - pre_emphasis * shifted[:-1])
            peak = np.max(np.abs(bright))
            if peak > 0:
                bright = bright / peak * 0.92
            return bright.astype(np.float32)
        except Exception as e:
            print(f"[AudioService] Voice clone transform warning: {e}")
            return audio

    def _synthesize_and_play(self, text: str):
        """Synthesize with MeloTTS Vietnamese, apply character voice clone DSP, and play."""
        self._load_tts_model()
        if self._tts_engine is None:
            raise RuntimeError("TTS engine not initialized")
        
        char_id = self._get_equipped_character_id()
        tts_speed = 1.08 if char_id == "phoebe_chuby" else (1.03 if char_id == "nono_chubby" else 1.0)
        temp_path = os.path.join(tempfile.gettempdir(), f"tts_output_{int(time.time()*1000)}.wav")
        
        # Generate audio using MeloTTS
        self._tts_engine.tts_to_file(
            text=text,
            speaker_id=self._tts_speaker_id,
            output_path=temp_path,
            speed=tts_speed,
            quiet=True
        )
        
        if sf is None:
            raise RuntimeError("soundfile not installed")
            
        audio, sr = sf.read(temp_path)
        if char_id in ("phoebe_chuby", "nono_chubby"):
            audio = self._apply_character_voice_clone(audio, sr, char_id)
            try:
                sf.write(temp_path, audio, sr)
            except Exception:
                pass
        
        # Play directly with sounddevice
        try:
            import sounddevice as sd
            sd.play(audio, sr)
            sd.wait()
        except Exception:
            if PLAYSOUND_AVAILABLE and playsound is not None:
                try:
                    playsound.playsound(temp_path, True)
                except Exception:
                    pass
        
        # Cleanup
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass
    
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
            
            # Check if speech_recognition is installed
            if not SR_AVAILABLE or sr is None:
                print("[AudioService] speech_recognition not installed, using sherpa-onnx ASR directly")
                return self._listen_with_sherpa(timeout, phrase_time_limit)

            try:
                r = sr.Recognizer()
                with sr.Microphone() as source:
                    r.pause_threshold = 0.8
                    r.energy_threshold = 300
                    audio = r.listen(source, phrase_time_limit=phrase_time_limit, timeout=timeout)
                
                # Save audio to temp file for sherpa-onnx
                temp_path = os.path.join(tempfile.gettempdir(), f"asr_input_{int(time.time()*1000)}.wav")
                with open(temp_path, "wb") as f:
                    f.write(audio.get_wav_data())
                
                # Transcribe with Zipformer
                text = self._transcribe_audio(temp_path)
                
                # Cleanup
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
                # Update UI
                if self.view and text:
                    self.view.update_user_text(text)
                elif self.view and not text:
                    self.view.update_user_text("Pop không nghe rõ...")
                
                print(f"[USER] {text}")
                return text if text else "..."
                
            except Exception as e:
                # Handle timeout (no speech detected) or recognition errors gracefully
                ignored_errors = tuple(
                    err for err in (
                        getattr(sr, "WaitTimeoutError", None),
                        getattr(sr, "UnknownValueError", None),
                        getattr(sr, "RequestError", None),
                    ) if err is not None
                )
                if ignored_errors and isinstance(e, ignored_errors):
                    if self.view:
                        self.view.update_user_text("Pop không nghe rõ...")
                    return "..."
                print(f"[AudioService] Listen error: {e}")
                return "..."
                
        finally:
            self.is_listening = False
            self.gate_lock.release()
    
    def _transcribe_audio(self, audio_path: str) -> Optional[str]:
        """Transcribe audio file using Vietnamese Zipformer via sherpa-onnx (offline)."""
        if self._asr_recognizer is None:
            self._load_asr_model()
        if self._asr_recognizer is None:
            return None
        
        # Read audio file
        import soundfile as sf
        audio_data, sample_rate = sf.read(audio_path)
        
        # Resample to 16kHz if needed
        if sample_rate != 16000:
            import librosa
            audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)
        
        # Convert to float32
        if np is not None and audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        
        # Use offline recognizer - simpler API
        stream = self._asr_recognizer.create_stream()
        stream.accept_waveform(16000, audio_data)
        self._asr_recognizer.decode_stream(stream)
        
        get_res_fn = getattr(self._asr_recognizer, "get_result", None)
        if callable(get_res_fn):
            result = get_res_fn(stream)
            text = getattr(result, "text", "").strip()
        else:
            text = getattr(getattr(stream, "result", None), "text", "").strip()
        
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
            
            audio_data = sd.rec(duration * sample_rate, samplerate=sample_rate, channels=1, dtype='float32')
            sd.wait()
            audio_data = audio_data.flatten()
            
            # Save to temp file
            temp_path = os.path.join(tempfile.gettempdir(), f"asr_input_{int(time.time()*1000)}.wav")
            if sf is None:
                raise RuntimeError("soundfile not installed")
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
    
    def get_text_with_retry(self, max_retries: int = 3, retry_message: Optional[str] = None) -> str:
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