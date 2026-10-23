"""LLM Service - Local AI model wrapper using llama-cpp-python.

Default model: LFM2.5-2.6B Q5_K_M (Liquid AI, ~1.8GB VRAM, good for low-VRAM GPUs)
"""
from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)


# Default config — override via env vars or constructor args
DEFAULT_MODEL_FILENAME = "LFM2.5-2.6B.Q5_K_M.gguf"
DEFAULT_CONTEXT_SIZE = 4096
DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9
DEFAULT_N_GPU_LAYERS = -1  # -1 = all GPU layers (iGPU/dGPU default), 0 = CPU only
DEFAULT_N_THREADS = 0  # 0 = auto-detect optimal threads (prevents 100% CPU lock)


def get_optimal_threads(requested_threads: int = 0) -> int:
    """Calculate CPU threads to prevent pinning CPU at 100% and keep system responsive."""
    if requested_threads > 0:
        return requested_threads
    cpu_cnt = os.cpu_count() or 4
    if cpu_cnt <= 2:
        return 1
    elif cpu_cnt <= 4:
        return max(1, cpu_cnt - 1)
    else:
        # Reserve 1-2 cores for UI, audio, and OS to prevent stutter
        return max(2, cpu_cnt - 2)


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

        # Sync with llm_config if defaults are used
        try:
            from service.llm_config import get_llm_config
            cfg = get_llm_config()
            if n_gpu_layers == DEFAULT_N_GPU_LAYERS and cfg.n_gpu_layers != DEFAULT_N_GPU_LAYERS:
                n_gpu_layers = cfg.n_gpu_layers
            if n_threads == DEFAULT_N_THREADS and cfg.n_threads != DEFAULT_N_THREADS:
                n_threads = cfg.n_threads
            if n_ctx == DEFAULT_CONTEXT_SIZE and cfg.n_ctx != DEFAULT_CONTEXT_SIZE:
                n_ctx = cfg.n_ctx
        except Exception:
            pass

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
        env_path = os.environ.get("POP_LLM_MODEL_PATH")
        if env_path and not model_path:
            return str(Path(env_path).expanduser().resolve())

        if models_dir is None:
            project_root = Path(__file__).resolve().parent.parent
            dir_path = project_root / "LLM-agents"
        else:
            dir_path = Path(models_dir).expanduser().resolve()

        if not model_path:
            return str(dir_path / DEFAULT_MODEL_FILENAME)

        p = Path(model_path).expanduser()
        if p.is_absolute() and p.exists():
            return str(p.resolve())

        candidate = dir_path / model_path
        if candidate.exists():
            return str(candidate)

        if not model_path.endswith(".gguf"):
            candidate_gguf = dir_path / f"{model_path}.gguf"
            if candidate_gguf.exists():
                return str(candidate_gguf)

        if dir_path.exists():
            clean_search = model_path.lower().replace(" ", "").replace("-", "").replace("_", "")
            for item in dir_path.iterdir():
                clean_item = item.name.lower().replace(" ", "").replace("-", "").replace("_", "")
                if clean_search in clean_item or clean_item in clean_search:
                    return str(item)

        return str(candidate)

    # ------------------------------------------------------------------ #
    # Model loading
    # ------------------------------------------------------------------ #
    def is_model_available(self) -> Tuple[bool, str]:
        """Check if model exists and is valid without loading weights into memory."""
        try:
            model_p = Path(self.model_path)
            if model_p.is_dir():
                found_gguf = None
                for root, _, files in os.walk(str(model_p)):
                    for f in files:
                        if f.endswith(".gguf"):
                            fp = Path(root) / f
                            try:
                                if fp.stat().st_size >= 10 * 1024 * 1024:
                                    found_gguf = fp
                                    break
                            except OSError:
                                pass
                    if found_gguf:
                        break
                if found_gguf:
                    return True, str(found_gguf)
                return False, f"Thư mục '{model_p.name}' không chứa tệp .gguf hợp lệ (>10MB)."

            if not model_p.exists() or not model_p.is_file() or model_p.stat().st_size < 10 * 1024 * 1024:
                file_size_mb = 0
                if model_p.exists() and model_p.is_file():
                    try:
                        file_size_mb = round(model_p.stat().st_size / (1024 * 1024), 2)
                    except OSError:
                        pass
                return False, f"Chưa có tệp mô hình .gguf hợp lệ ({file_size_mb} MB tại '{model_p.name}')."
            return True, str(model_p)
        except Exception as e:
            return False, str(e)

    def _ensure_loaded(self) -> Any:
        """Lazy-load the model on first call. Thread-safe."""
        if self._llm is not None:
            return self._llm

        with self._load_lock:
            if self._llm is not None:
                return self._llm

            model_p = Path(self.model_path)
            # If directory, find any valid .gguf inside
            if model_p.is_dir():
                found_gguf = None
                for root, _, files in os.walk(str(model_p)):
                    for f in files:
                        if f.endswith(".gguf"):
                            fp = Path(root) / f
                            try:
                                if fp.stat().st_size >= 10 * 1024 * 1024:
                                    found_gguf = fp
                                    break
                            except OSError:
                                pass
                    if found_gguf:
                        break
                if found_gguf:
                    self.model_path = str(found_gguf)
                    model_p = found_gguf

            # Fail-fast if model file doesn't exist or is empty (0MB)
            if not model_p.exists() or not model_p.is_file() or model_p.stat().st_size < 10 * 1024 * 1024:
                file_size_mb = 0
                if model_p.exists() and model_p.is_file():
                    try:
                        file_size_mb = round(model_p.stat().st_size / (1024 * 1024), 2)
                    except OSError:
                        pass
                raise FileNotFoundError(
                    f"Mô hình AI chưa được tải về máy hoặc tệp không hợp lệ ({file_size_mb} MB tại '{model_p.name}'). "
                    f"Vui lòng vào 'Model++' để tải mô hình hoặc copy tệp .gguf vào thư mục LLM-agents."
                )

            try:
                from llama_cpp import Llama, llama_supports_gpu_offload  # type: ignore
            except ImportError as e:
                raise ImportError(
                    "[LLMService] llama-cpp-python is not installed.\n"
                    "Install with: pip install llama-cpp-python\n"
                    "For NVIDIA GPU: pip install llama-cpp-python --extra-index-url "
                    "https://abetlen.github.io/llama-cpp-python/whl/cu121\n"
                    "For Vulkan (Intel/AMD iGPU): pip install llama-cpp-python --extra-index-url "
                    "https://abetlen.github.io/llama-cpp-python/whl/vulkan"
                ) from e

            # Check GPU offload support
            gpu_supported = False
            try:
                gpu_supported = bool(llama_supports_gpu_offload())
            except Exception as e:
                logger.warning(f"[LLMService] Failed to check GPU offload support: {e}")

            actual_gpu_layers = self.n_gpu_layers
            if actual_gpu_layers != 0 and not gpu_supported:
                logger.warning(
                    "[LLMService] GPU offload is not supported by current llama-cpp-python installation. "
                    "Falling back to CPU only (n_gpu_layers=0)."
                )
                actual_gpu_layers = 0

            threads = get_optimal_threads(self.n_threads)

            logger.info(
                f"[LLMService] Loading model from {self.model_path} "
                f"(n_gpu_layers={actual_gpu_layers}, n_threads={threads})..."
            )
            try:
                self._llm = Llama(
                    model_path=self.model_path,
                    n_ctx=self.n_ctx,
                    n_gpu_layers=actual_gpu_layers,
                    n_threads=threads,
                    verbose=self.verbose,
                )
            except Exception as load_err:
                if actual_gpu_layers != 0:
                    logger.warning(
                        f"[LLMService] Loading with GPU failed ({load_err}). "
                        f"Retrying with CPU fallback (n_gpu_layers=0)..."
                    )
                    self._llm = Llama(
                        model_path=self.model_path,
                        n_ctx=self.n_ctx,
                        n_gpu_layers=0,
                        n_threads=threads,
                        verbose=self.verbose,
                    )
                else:
                    raise load_err
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
