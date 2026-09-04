"""LLM Service - Local AI model wrapper using llama-cpp-python.

Default model: LFM2.5-2.6B Q5_K_M (Liquid AI, ~1.8GB VRAM, good for low-VRAM GPUs)
"""
from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


# Default config — override via env vars or constructor args
DEFAULT_MODEL_FILENAME = "LFM2.5-2.6B.Q5_K_M.gguf"
DEFAULT_CONTEXT_SIZE = 4096
DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9
DEFAULT_N_GPU_LAYERS = 0  # 0 = CPU only (safe for 4GB VRAM), -1 = all GPU layers
DEFAULT_N_THREADS = 0  # 0 = auto-detect


class LLMService:
    """Singleton-style wrapper around llama-cpp-python Llama model.

    Thread-safe lazy initialization. The model is loaded once on first use
    and reused for subsequent calls.

    Usage:
        llm = LLMService()
        reply = llm.chat([{"role": "user", "content": "Xin chào"}])
    """

    _instance: Optional["LLMService"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # Singleton — only one model instance per process
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        model_path: Optional[str] = None,
        n_ctx: int = DEFAULT_CONTEXT_SIZE,
        n_gpu_layers: int = DEFAULT_N_GPU_LAYERS,
        n_threads: int = DEFAULT_N_THREADS,
        verbose: bool = False,
        models_dir: Optional[str] = None,
    ):
        # Skip re-init if already constructed
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.model_path = self._resolve_model_path(model_path, models_dir)
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.n_threads = n_threads
        self.verbose = verbose

        self._llm: Any = None  # llama_cpp.Llama instance
        self._initialized = True
        self._load_lock = threading.Lock()

        logger.info(
            f"[LLMService] Configured: model={self.model_path}, "
            f"n_ctx={n_ctx}, n_gpu_layers={n_gpu_layers}, n_threads={n_threads}"
        )

    # ------------------------------------------------------------------ #
    # Path resolution
    # ------------------------------------------------------------------ #
    def _resolve_model_path(
        self, model_path: Optional[str], models_dir: Optional[str]
    ) -> str:
        """Resolve model path from explicit arg, env var, or default location."""
        # 1. Explicit arg wins
        if model_path:
            return str(Path(model_path).expanduser().resolve())

        # 2. Env var
        env_path = os.environ.get("POP_LLM_MODEL_PATH")
        if env_path:
            return str(Path(env_path).expanduser().resolve())

        # 3. Default: <project_root>/models/<DEFAULT_MODEL_FILENAME>
        if models_dir is None:
            # project_root = service/../
            project_root = Path(__file__).resolve().parent.parent
            # Updated folder name to "LLM-agents"
            models_dir = project_root / "LLM-agents"
        else:
            models_dir = Path(models_dir).expanduser().resolve()

        candidate = models_dir / DEFAULT_MODEL_FILENAME
        return str(candidate)

    # ------------------------------------------------------------------ #
    # Model loading
    # ------------------------------------------------------------------ #
    def _ensure_loaded(self) -> Any:
        """Lazy-load the model on first call. Thread-safe."""
        if self._llm is not None:
            return self._llm

        with self._load_lock:
            if self._llm is not None:
                return self._llm

            if not Path(self.model_path).exists():
                # Try to auto‑download the model via huggingface_hub if it is missing.
                try:
                    from huggingface_hub import hf_hub_download
                    cache_dir = Path(self.model_path).parent
                    downloaded_path = hf_hub_download(
                        repo_id="LiquidAI/LFM2.5-2.6B-GGUF",
                        filename=Path(self.model_path).name,
                        cache_dir=str(cache_dir),
                    )
                    logger.info(f"[LLMService] Auto‑downloaded model to {downloaded_path}")
                    self.model_path = str(downloaded_path)
                except Exception as e:
                    raise FileNotFoundError(
                        f"[LLMService] Model file not found and auto‑download failed: {e}\n"
                        f"Please download the GGUF model manually and place it at {self.model_path} "
                        f"or set POP_LLM_MODEL_PATH env var."
                    )

            try:
                from llama_cpp import Llama  # type: ignore
            except ImportError as e:
                raise ImportError(
                    "[LLMService] llama-cpp-python is not installed.\n"
                    "Install with: pip install llama-cpp-python\n"
                    "For NVIDIA GPU: pip install llama-cpp-python --extra-index-url "
                    "https://abetlen.github.io/llama-cpp-python/whl/cu121"
                ) from e

            logger.info(f"[LLMService] Loading model from {self.model_path}...")
            self._llm = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                n_threads=self.n_threads,
                verbose=self.verbose,
            )
            logger.info("[LLMService] Model loaded successfully.")
            return self._llm

    def is_loaded(self) -> bool:
        return self._llm is not None

    def unload(self) -> None:
        """Free GPU/CPU memory by dropping the model reference."""
        with self._load_lock:
            if self._llm is not None:
                logger.info("[LLMService] Unloading model.")
                self._llm = None
                
    def switch_model(self, model_filename: str) -> None:
        """Switch to a new model."""
        new_path = self._resolve_model_path(model_filename, None)
        if new_path == self.model_path:
            logger.info(f"[LLMService] Model is already {model_filename}, skipping switch.")
            return
            
        logger.info(f"[LLMService] Switching model from {self.model_path} to {new_path}")
        self.unload()
        self.model_path = new_path
        # Force load immediately
        self._ensure_loaded()

    # ------------------------------------------------------------------ #
    # Inference
    # ------------------------------------------------------------------ #
    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        stop: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
        response_format: Optional[Dict] = None,
    ) -> str:
        """Run a chat completion.

        Args:
            messages: list of {"role": ..., "content": ...} dicts
            max_tokens: max new tokens to generate
            temperature: sampling temperature (0 = greedy)
            top_p: nucleus sampling
            stop: optional list of stop strings
            system_prompt: optional system message prepended to messages

        Returns:
            Assistant reply text (stripped).
        """
        llm = self._ensure_loaded()

        msgs: List[Dict[str, str]] = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)

        try:
            kwargs = {
                "messages": msgs,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "stop": stop or [],
            }
            if response_format is not None:
                kwargs["response_format"] = response_format
                
            response = llm.create_chat_completion(**kwargs)
            content = response["choices"][0]["message"]["content"]
            return (content or "").strip()
        except Exception as e:
            logger.error(f"[LLMService] chat() failed: {e}")
            raise

    def complete(
        self,
        prompt: str,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        stop: Optional[List[str]] = None,
    ) -> str:
        """Raw text completion (no chat template)."""
        llm = self._ensure_loaded()
        try:
            response = llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop or [],
            )
            return response["choices"][0]["text"].strip()
        except Exception as e:
            logger.error(f"[LLMService] complete() failed: {e}")
            raise

    # ------------------------------------------------------------------ #
    # Health check
    # ------------------------------------------------------------------ #
    def health_check(self) -> Dict[str, Any]:
        """Return status info — useful for diagnostics."""
        info: Dict[str, Any] = {
            "model_path": self.model_path,
            "model_exists": Path(self.model_path).exists(),
            "loaded": self.is_loaded(),
            "n_ctx": self.n_ctx,
            "n_gpu_layers": self.n_gpu_layers,
        }
        if self.is_loaded():
            try:
                # llama-cpp exposes n_vocab / n_params via internal handle
                info["n_vocab"] = getattr(self._llm, "n_vocab", lambda: None)()
            except Exception:
                pass
        return info
