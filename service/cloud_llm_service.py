"""Cloud LLM Service - Universal OpenAI-compatible API client for cloud models.
Supports OpenAI, DeepSeek, Groq, Google Gemini, OpenRouter, and Custom endpoints.
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional, Tuple
import requests

from utils.logger import get_logger

logger = get_logger(__name__)


# Standard Pre-configured Providers
CLOUD_PROVIDERS: Dict[str, Dict[str, Any]] = {
    "deepseek": {
        "name": "DeepSeek AI",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "api_key_url": "https://platform.deepseek.com/api_keys",
        "description": "DeepSeek V3 / R1 reasoning - Siêu nhanh, thông minh & chi phí tối ưu."
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        "api_key_url": "https://platform.openai.com/api-keys",
        "description": "Mô hình GPT-4o hàng đầu từ OpenAI."
    },
    "groq": {
        "name": "Groq LPU",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        "api_key_url": "https://console.groq.com/keys",
        "description": "Tốc độ xử lý siêu tốc cực cao (hàng trăm token/giây) chạy Llama 3.3."
    },
    "gemini": {
        "name": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "default_model": "gemini-1.5-flash",
        "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"],
        "api_key_url": "https://aistudio.google.com/app/apikey",
        "description": "Mô hình thế hệ mới của Google với context window siêu lớn."
    },
    "openrouter": {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "meta-llama/llama-3.3-70b-instruct",
        "models": [
            "meta-llama/llama-3.3-70b-instruct",
            "anthropic/claude-3.5-sonnet",
            "deepseek/deepseek-chat",
            "google/gemini-flash-1.5"
        ],
        "api_key_url": "https://openrouter.ai/keys",
        "description": "Cổng kết nối thống nhất với hơn 200+ mô hình AI toàn cầu."
    },
    "custom": {
        "name": "Tùy chỉnh (Custom API)",
        "base_url": "http://localhost:11434/v1",
        "default_model": "llama3.2",
        "models": ["llama3.2", "qwen2.5", "mistral"],
        "api_key_url": "",
        "description": "Kết nối máy chủ OpenAI-compatible cá nhân (Ollama, LM Studio, vLLM...)."
    }
}


class CloudLLMService:
    """Universal OpenAI-compatible Cloud LLM Service."""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "",
        model: str = "",
        provider: str = "deepseek",
        timeout: int = 45,
    ):
        self.api_key = api_key.strip()
        self.provider = provider.lower()
        self.base_url = (base_url or CLOUD_PROVIDERS.get(self.provider, {}).get("base_url", "")).rstrip("/")
        self.model = model or CLOUD_PROVIDERS.get(self.provider, {}).get("default_model", "")
        self.timeout = timeout

    @classmethod
    def from_settings(cls) -> "CloudLLMService":
        """Instantiate client using saved settings in user_settings.json."""
        from view.ui.settings.settings_config import load_user_settings
        settings = load_user_settings()

        provider = settings.get("cloud_provider", "deepseek")
        api_key = settings.get("cloud_api_key", "")
        base_url = settings.get("cloud_base_url", "")
        model = settings.get("cloud_model", "")

        return cls(
            api_key=api_key,
            base_url=base_url,
            model=model,
            provider=provider
        )

    def is_configured(self) -> bool:
        """Check if minimum credentials are provided."""
        # For custom/local servers (like Ollama), api_key may be empty or dummy
        if self.provider == "custom":
            return bool(self.base_url and self.model)
        return bool(self.api_key and self.base_url and self.model)

    def test_connection(self) -> Tuple[bool, str]:
        """Test API connection with a minimal test message.
        Returns: (success: bool, message: str)
        """
        if not self.base_url:
            return False, "Chưa cấu hình Base URL"
        if not self.api_key and self.provider != "custom":
            return False, "Chưa điền API Key"
        if not self.model:
            return False, "Chưa chọn hoặc điền tên Model"

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
        }
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/madge-petter/Virtual-Assistantpop-Linux"
            headers["X-Title"] = "POP Assistant"

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 10,
            "temperature": 0.1
        }

        start_time = time.time()
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=12)
            elapsed_ms = int((time.time() - start_time) * 1000)

            if resp.status_code == 200:
                data = resp.json()
                reply = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                return True, f"Kết nối thành công! ({elapsed_ms}ms) — Phản hồi: {reply[:30]}"
            elif resp.status_code == 401:
                return False, f"Lỗi 401: API Key không hợp lệ hoặc đã hết hạn."
            elif resp.status_code == 404:
                return False, f"Lỗi 404: Không tìm thấy model '{self.model}' hoặc sai đường dẫn endpoint."
            elif resp.status_code == 429:
                return False, f"Lỗi 429: Vượt quá giới hạn Rate Limit hoặc tài khoản hết credit."
            else:
                return False, f"Lỗi {resp.status_code}: {resp.text[:120]}"
        except requests.exceptions.Timeout:
            return False, "Hết thời gian chờ (Timeout sau 12 giây). Kiểm tra mạng hoặc Base URL."
        except requests.exceptions.ConnectionError as ce:
            return False, f"Không thể kết nối đến máy chủ: {ce}"
        except Exception as e:
            return False, f"Lỗi: {e}"

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 1500,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: Optional[List[str]] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Call OpenAI-compatible chat completion endpoint."""
        if not self.is_configured():
            raise ValueError("Cloud LLM chưa được cấu hình đầy đủ API Key và Model trong Cài đặt.")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
        }
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/madge-petter/Virtual-Assistantpop-Linux"
            headers["X-Title"] = "POP Assistant"

        # Format message chain
        formatted_msgs: List[Dict[str, str]] = []
        if system_prompt:
            formatted_msgs.append({"role": "system", "content": system_prompt})
        formatted_msgs.extend(messages)

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": formatted_msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }
        if stop:
            payload["stop"] = stop
        if response_format and isinstance(response_format, dict):
            # Pass json_object if supported
            if response_format.get("type") == "json_object":
                payload["response_format"] = {"type": "json_object"}

        logger.info(f"[CloudLLMService] Requesting {self.provider} ({self.model}) at {url}...")
        start_time = time.time()

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            elapsed = time.time() - start_time

            if resp.status_code != 200:
                err_body = resp.text[:250]
                logger.error(f"[CloudLLMService] HTTP {resp.status_code}: {err_body}")
                raise RuntimeError(f"Cloud API HTTP {resp.status_code}: {err_body}")

            result = resp.json()
            content = result["choices"][0]["message"]["content"]
            logger.info(f"[CloudLLMService] Success ({elapsed:.2f}s, {len(content)} chars)")
            return content.strip()

        except requests.exceptions.Timeout as e:
            logger.error(f"[CloudLLMService] Timeout after {self.timeout}s: {e}")
            raise TimeoutError(f"Cloud API timeout sau {self.timeout} giây.") from e
        except Exception as e:
            logger.error(f"[CloudLLMService] Chat failed: {e}")
            raise

