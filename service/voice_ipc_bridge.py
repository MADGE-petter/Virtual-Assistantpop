"""Voice IPC Bridge - C++ Native Voice & LLM Engine with Seamless Fallback.

Connects to `native/bin/PopVoiceEngine.exe` via Windows Named Pipe `\\\\.\\pipe\\pop_voice_ipc`.
If the native binary is not compiled or unavailable, it transparently falls back to
the Python in-process runtime with streaming sentence chunking to TTS.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
from typing import Any, Callable, Dict, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

PIPE_NAME = r"\\.\pipe\pop_voice_ipc"


class PythonSentenceStreamer:
    """Python counterpart of native sentence_streamer.h for streaming LLM tokens to TTS."""

    def __init__(self, callback: Optional[Callable[[str], None]] = None):
        self.callback = callback
        self.buffer = ""
        self.sentence_count = 0

    def reset(self):
        self.buffer = ""
        self.sentence_count = 0

    def feed_token(self, token: str):
        self.buffer += token
        split_pos = self._find_boundary(self.buffer)
        while split_pos != -1:
            sentence = self.buffer[: split_pos + 1]
            self.buffer = self.buffer[split_pos + 1 :]
            self._emit(sentence)
            split_pos = self._find_boundary(self.buffer)

    def flush(self):
        if self.buffer.strip():
            self._emit(self.buffer)
            self.buffer = ""

    def _find_boundary(self, text: str) -> int:
        if not text:
            return -1
        for i, c in enumerate(text):
            if c in ".!?\n":
                if i + 1 < len(text) and text[i + 1] == ".":
                    continue
                return i
            if c in ",;:" and i >= 35:
                return i
        return -1

    def _emit(self, text: str):
        cleaned = re.sub(r"[\*\_`#\[\]\(\)]", "", text).strip()
        if cleaned:
            self.sentence_count += 1
            if self.callback:
                self.callback(cleaned)


class VoiceIpcBridge:
    """Orchestrates C++ Native Voice Engine and Python fallback."""

    _instance: Optional["VoiceIpcBridge"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._initialized = True
        self._is_native = False
        self._process: Optional[subprocess.Popen] = None
        self._pipe_handle: Optional[Any] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Callbacks
        self.on_stt_text: Optional[Callable[[str], None]] = None
        self.on_llm_sentence: Optional[Callable[[str], None]] = None
        self.on_audio_level: Optional[Callable[[float], None]] = None
        self.on_voice_state: Optional[Callable[[str], None]] = None
        self.on_interrupt: Optional[Callable[[], None]] = None

        self._check_and_init_native()

    def _resolve_binary_path(self) -> Optional[str]:
        candidates = [
            os.path.join(os.path.dirname(__file__), "..", "native", "bin", "PopVoiceEngine.exe"),
            os.path.join(os.path.dirname(__file__), "native", "bin", "PopVoiceEngine.exe"),
            os.path.abspath(r"native\bin\PopVoiceEngine.exe"),
        ]
        for p in candidates:
            if os.path.isfile(p):
                return os.path.abspath(p)
        return None

    def _check_and_init_native(self):
        bin_path = self._resolve_binary_path()
        if not bin_path:
            logger.info("[VoiceIpcBridge] PopVoiceEngine.exe not found. Running in Python Fallback mode.")
            self._is_native = False
            return

        try:
            logger.info(f"[VoiceIpcBridge] Found PopVoiceEngine at {bin_path}. Launching...")
            self._process = subprocess.Popen(
                [bin_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            time.sleep(0.3)
            self._connect_pipe()
        except Exception as e:
            logger.warning(f"[VoiceIpcBridge] Failed to launch native voice engine: {e}. Falling back to Python.")
            self._is_native = False

    def _connect_pipe(self):
        try:
            # Open Windows Named Pipe in read/write binary mode
            self._pipe_handle = open(PIPE_NAME, "r+b", buffering=0)
            self._is_native = True
            logger.info("[VoiceIpcBridge] Connected to C++ Voice Engine Named Pipe.")
            self._stop_event.clear()
            self._reader_thread = threading.Thread(target=self._pipe_reader_loop, daemon=True)
            self._reader_thread.start()
        except Exception as e:
            logger.warning(f"[VoiceIpcBridge] Pipe connect failed: {e}. Fallback active.")
            self._is_native = False

    def _pipe_reader_loop(self):
        while not self._stop_event.is_set() and self._pipe_handle:
            try:
                line = self._pipe_handle.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    time.sleep(0.01)
                    continue

                msg = json.loads(line)
                ev = msg.get("event", "")
                data = msg.get("data", {})

                if ev == "stt_text":
                    text = data.get("text", "")
                    if self.on_stt_text and text:
                        self.on_stt_text(text)
                elif ev == "llm_sentence":
                    sentence = data.get("sentence", "")
                    if self.on_llm_sentence and sentence:
                        self.on_llm_sentence(sentence)
                elif ev == "audio_level":
                    level = float(data.get("level", 0.0))
                    if self.on_audio_level:
                        self.on_audio_level(level)
                elif ev == "voice_state":
                    st = data.get("state", "")
                    if self.on_voice_state:
                        self.on_voice_state(st)
                elif ev == "interrupt":
                    if self.on_interrupt:
                        self.on_interrupt()
            except Exception as e:
                if not self._stop_event.is_set():
                    logger.debug(f"[VoiceIpcBridge] Pipe read error: {e}")
                break

    def is_native_active(self) -> bool:
        return self._is_native

    def send_command(self, cmd: str, **kwargs):
        if not self._is_native or not self._pipe_handle:
            return
        try:
            payload = {"cmd": cmd}
            payload.update(kwargs)
            line = (json.dumps(payload) + "\n").encode("utf-8")
            self._pipe_handle.write(line)
            self._pipe_handle.flush()
        except Exception as e:
            logger.error(f"[VoiceIpcBridge] Failed to send cmd '{cmd}': {e}")

    # ==================== PUBLIC API ====================

    def start_listening(self):
        if self._is_native:
            self.send_command("start_listen")
        else:
            logger.debug("[VoiceIpcBridge] Fallback: start_listening triggered.")

    def stop_listening(self):
        if self._is_native:
            self.send_command("stop_listen")
        else:
            logger.debug("[VoiceIpcBridge] Fallback: stop_listening triggered.")

    def interrupt(self):
        if self._is_native:
            self.send_command("interrupt")
        if self.on_interrupt:
            self.on_interrupt()

    def set_voice_state(self, state: str):
        if self._is_native:
            self.send_command("set_state", state=state)
        if self.on_voice_state:
            self.on_voice_state(state)

    def stream_generate(
        self,
        llm_service: Any,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
        on_token: Optional[Callable[[str], None]] = None,
        on_sentence: Optional[Callable[[str], None]] = None,
        cancel_event: Optional[threading.Event] = None,
    ) -> str:
        """Stream LLM response with real-time sentence chunking for instant TTS playback."""
        full_text: List[str] = []

        def handle_sentence(sent: str):
            if on_sentence:
                on_sentence(sent)
            if self.on_llm_sentence:
                self.on_llm_sentence(sent)

        streamer = PythonSentenceStreamer(callback=handle_sentence)

        msgs: List[Dict[str, str]] = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)

        self.set_voice_state("THINKING_LLM")

        try:
            llm = llm_service._ensure_loaded()
            # Request token streaming from llama_cpp
            response_stream = llm.create_chat_completion(
                messages=msgs,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )

            for chunk in response_stream:
                if cancel_event and cancel_event.is_set():
                    logger.info("[VoiceIpcBridge] Streaming cancelled.")
                    break

                delta = chunk["choices"][0].get("delta", {})
                token = delta.get("content", "")
                if token:
                    full_text.append(token)
                    if on_token:
                        on_token(token)
                    streamer.feed_token(token)

            streamer.flush()
        except Exception as e:
            logger.error(f"[VoiceIpcBridge] Stream generate failed: {e}")
            raise

        self.set_voice_state("IDLE")
        return "".join(full_text).strip()

    def shutdown(self):
        self._stop_event.set()
        if self._is_native:
            self.send_command("quit")
        if self._pipe_handle:
            try:
                self._pipe_handle.close()
            except Exception:
                pass
            self._pipe_handle = None
        if self._process:
            try:
                self._process.terminate()
            except Exception:
                pass
            self._process = None


def get_voice_ipc_bridge() -> VoiceIpcBridge:
    return VoiceIpcBridge()

