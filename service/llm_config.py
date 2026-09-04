"""LLM Configuration - Centralized settings for the local LLM service.

Override via environment variables:
    POP_LLM_MODEL_PATH     - absolute path to .gguf file
    POP_LLM_N_CTX          - context window size (default 4096)
    POP_LLM_N_GPU_LAYERS   - layers to offload to GPU (-1 = all, 0 = CPU only)
    POP_LLM_N_THREADS      - CPU threads (0 = auto)
    POP_LLM_ENABLED        - "1" to enable LLM, "0" to disable (default "1")
    POP_LLM_FALLBACK       - "1" to fall back to rule-based on error (default "1")
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _get_env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _get_env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _get_env_str(name: str, default: Optional[str]) -> Optional[str]:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return raw


@dataclass(frozen=True)
class LLMConfig:
    """Immutable LLM configuration."""

    enabled: bool = True
    fallback_to_rules: bool = True
    model_path: Optional[str] = None
    n_ctx: int = 4096
    n_gpu_layers: int = -1
    n_threads: int = 0
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    verbose: bool = False

    # System prompt used when LLM is asked to generate a free-form reply
    system_prompt: str = (
        "Bạn là một trợ lý ảo thân thiện, thông minh, nói tiếng Việt.\n"
        "BẠN PHẢI LUÔN LUÔN TRẢ LỜI BẰNG ĐỊNH DẠNG JSON. KHÔNG ĐƯỢC IN RA TEXT BÌNH THƯỜNG.\n"
        "Cấu trúc JSON bắt buộc:\n"
        "{\n"
        '  "action": "chat",\n'
        '  "response": "Câu trả lời thân thiện dành cho user (tối đa 2-3 câu)"\n'
        "}\n"
        "Tuyệt đối chỉ in ra một khối JSON duy nhất."
    )

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls(
            enabled=_get_env_bool("POP_LLM_ENABLED", True),
            fallback_to_rules=_get_env_bool("POP_LLM_FALLBACK", True),
            model_path=_get_env_str("POP_LLM_MODEL_PATH", None),
            n_ctx=_get_env_int("POP_LLM_N_CTX", 4096),
            n_gpu_layers=_get_env_int("POP_LLM_N_GPU_LAYERS", -1),
            n_threads=_get_env_int("POP_LLM_N_THREADS", 0),
            verbose=_get_env_bool("POP_LLM_VERBOSE", False),
        )

    def resolve_model_path(self) -> Path:
        """Resolve to absolute path. Falls back to <project>/models/."""
        if self.model_path:
            return Path(self.model_path).expanduser().resolve()
        project_root = Path(__file__).resolve().parent.parent
        # Updated folder name to "LLM-agents"
        return project_root / "LLM-agents" / "LFM2.5-2.6B.Q5_K_M.gguf"


# Module-level singleton (lazy)
_default_config: Optional[LLMConfig] = None


def get_llm_config() -> LLMConfig:
    """Return the process-wide LLM config (loaded from env on first call)."""
    global _default_config
    if _default_config is None:
        _default_config = LLMConfig.from_env()
    return _default_config
