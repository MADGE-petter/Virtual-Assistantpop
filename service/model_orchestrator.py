"""Model Orchestrator - Tri-Model Multi-Agent Pipeline.

Pipeline:
1. LFM3 1.7B (Router & Dialogue Host - in-memory)
2. LFM3-VL (Vision Specialist - on-demand load/unload, fallback to Windows OCR)
3. DeepSeek Thinking (Reasoning Engine - on-demand load/unload with <think> tracing)
4. LFM3 1.7B (Final Dialogue Synthesizer & Voice/TTS output)
"""

from __future__ import annotations

import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from utils.logger import get_logger
from view.ui.settings import load_user_settings

logger = get_logger(__name__)


@dataclass
class PipelineStep:
    step_id: str
    title: str
    content: str
    model_name: str
    duration_s: float = 0.0


@dataclass
class OrchestrationResult:
    text: str
    steps: List[PipelineStep] = field(default_factory=list)
    has_thinking: bool = False
    thinking_text: str = ""
    error: Optional[str] = None


class ModelOrchestrator:
    """Điều phối chuỗi 3 mô hình (Tri-Model Pipeline) theo kiến trúc Hybrid On-Demand."""

    _instance: Optional["ModelOrchestrator"] = None
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

        # Models path cache
        self._router_path: Optional[str] = None
        self._vision_path: Optional[str] = None
        self._reasoning_path: Optional[str] = None

        # On-demand instances
        self._vision_llm: Any = None
        self._reasoning_llm: Any = None
        self._vision_unload_timer: Optional[threading.Timer] = None
        self._reasoning_unload_timer: Optional[threading.Timer] = None
        self._model_lock = threading.Lock()

        # Auto-detect models
        self.detect_installed_roles()

    def get_models_dir(self) -> str:
        settings = load_user_settings()
        return settings.get("model_dir", os.path.join(os.getcwd(), "LLM-agents"))

    def detect_installed_roles(self) -> Dict[str, Optional[str]]:
        """Quét và phân loại 3 vai trò mô hình từ thư mục LLM-agents."""
        models_dir = self.get_models_dir()
        self._router_path = None
        self._vision_path = None
        self._reasoning_path = None

        if not os.path.exists(models_dir):
            return {
                "router": None,
                "vision": None,
                "reasoning": None,
            }

        valid_files: List[str] = []
        for root, _, files in os.walk(models_dir):
            for f in files:
                if f.endswith(".gguf") and not f.startswith("."):
                    fp = os.path.join(root, f)
                    try:
                        if os.path.getsize(fp) >= 10 * 1024 * 1024:
                            valid_files.append(fp)
                    except OSError:
                        pass

        for fp in valid_files:
            fn = os.path.basename(fp).lower()
            # 1. Vision Specialist
            if ("vl" in fn or "vision" in fn) and not self._vision_path:
                self._vision_path = fp
            # 2. Reasoning Specialist (DeepSeek / R1 / Thinking)
            elif ("deepseek" in fn or "r1" in fn or "thinking" in fn or "reasoning" in fn) and not self._reasoning_path:
                self._reasoning_path = fp
            # 3. Router (LFM3 1.7B / LFM 1.7B / LFM2.5)
            elif ("lfm" in fn and "1.7" in fn) and not self._router_path:
                self._router_path = fp

        # Fallback router: any LFM model or any GGUF
        if not self._router_path:
            for fp in valid_files:
                fn = os.path.basename(fp).lower()
                if "lfm" in fn and fp != self._vision_path and fp != self._reasoning_path:
                    self._router_path = fp
                    break
        if not self._router_path and valid_files:
            self._router_path = valid_files[0]

        logger.info(
            f"[ModelOrchestrator] Roles detected: Router={Path(self._router_path).name if self._router_path else 'None'}, "
            f"Vision={Path(self._vision_path).name if self._vision_path else 'None (Fallback to OCR)'}, "
            f"Reasoning={Path(self._reasoning_path).name if self._reasoning_path else 'None (LFM3 Fallback)'}"
        )

        return {
            "router": self._router_path,
            "vision": self._vision_path,
            "reasoning": self._reasoning_path,
        }

    # ==================== ON-DEMAND MODEL LIFECYCLE ====================

    def _load_model(self, model_path: str, n_ctx: int = 4096) -> Any:
        from llama_cpp import Llama  # type: ignore
        from service.llm_service import get_optimal_threads

        threads = get_optimal_threads(0)
        n_batch = min(512, n_ctx)
        logger.info(f"[ModelOrchestrator] On-demand loading: {Path(model_path).name} (n_ctx={n_ctx}, n_batch={n_batch})...")
        try:
            # 1. Thử tải với FlashAttention để giảm 30-50% VRAM
            return Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=-1,
                n_threads=threads,
                n_batch=n_batch,
                flash_attn=True,
                verbose=False,
            )
        except Exception:
            try:
                # 2. Fallback tiêu chuẩn GPU
                return Llama(
                    model_path=model_path,
                    n_ctx=n_ctx,
                    n_gpu_layers=-1,
                    n_threads=threads,
                    n_batch=n_batch,
                    verbose=False,
                )
            except Exception:
                # 3. Fallback CPU
                return Llama(
                    model_path=model_path,
                    n_ctx=n_ctx,
                    n_gpu_layers=0,
                    n_threads=threads,
                    n_batch=n_batch,
                    verbose=False,
                )

    def _schedule_unload_vision(self, delay_seconds: float = 60.0):
        if self._vision_unload_timer:
            self._vision_unload_timer.cancel()

        def _unload():
            with self._model_lock:
                if self._vision_llm is not None:
                    logger.info("[ModelOrchestrator] Auto-unloading LFM3-VL to free VRAM/RAM.")
                    self._vision_llm = None

        self._vision_unload_timer = threading.Timer(delay_seconds, _unload)
        self._vision_unload_timer.daemon = True
        self._vision_unload_timer.start()

    def _schedule_unload_reasoning(self, delay_seconds: float = 60.0):
        if self._reasoning_unload_timer:
            self._reasoning_unload_timer.cancel()

        def _unload():
            with self._model_lock:
                if self._reasoning_llm is not None:
                    logger.info("[ModelOrchestrator] Auto-unloading DeepSeek Thinking to free VRAM/RAM.")
                    self._reasoning_llm = None

        self._reasoning_unload_timer = threading.Timer(delay_seconds, _unload)
        self._reasoning_unload_timer.daemon = True
        self._reasoning_unload_timer.start()

    # ==================== TRI-MODEL PIPELINE ====================

    def process_multimodal_request(
        self,
        user_prompt: str,
        image_paths: List[str],
        router_llm_service: Any,
        session_id: str = "default",
        on_step_callback: Optional[Any] = None,
    ) -> OrchestrationResult:
        """Thực thi chuỗi xử lý 3 mô hình khi phát hiện tệp ảnh."""
        steps: List[PipelineStep] = []
        self.detect_installed_roles()

        logger.info(
            f"[ModelOrchestrator] Starting Tri-Model Pipeline for {len(image_paths)} images: '{user_prompt[:40]}...'"
        )

        # ------------------------------------------------------------------ #
        # BƯỚC 1: LFM3 1.7B (Router) - Phân tích yêu cầu & tạo truy vấn thị giác
        # ------------------------------------------------------------------ #
        t0 = time.time()
        step1_title = "🧭 LFM3 1.7B: Phân tích & Điều phối nhiệm vụ"
        router_prompt = (
            f"Bạn là bộ điều phối LFM3 1.7B. Người dùng gửi yêu cầu: \"{user_prompt}\" kèm {len(image_paths)} tệp ảnh.\n"
            f"Hãy tóm tắt ngắn gọn trong 1-2 câu mục tiêu cần phân tích từ hình ảnh."
        )
        try:
            analysis_text = router_llm_service.chat(
                messages=[{"role": "user", "content": router_prompt}],
                max_tokens=150,
                temperature=0.3,
            )
        except Exception as e:
            analysis_text = f"Phân tích nội dung {len(image_paths)} hình ảnh đính kèm theo yêu cầu của bạn."

        step1 = PipelineStep(
            step_id="router_analysis",
            title=step1_title,
            content=analysis_text,
            model_name="LFM3 1.7B Router",
            duration_s=round(time.time() - t0, 2),
        )
        steps.append(step1)
        if on_step_callback:
            on_step_callback(step1)

        # ------------------------------------------------------------------ #
        # BƯỚC 2: LFM3-VL (Vision Specialist) - Đọc và trích xuất dữ liệu ảnh
        # ------------------------------------------------------------------ #
        t1 = time.time()
        visual_description = ""
        vision_model_name = "LFM3-VL (GGUF)" if self._vision_path else "Windows Native OCR (Fallback)"

        if self._vision_path and os.path.exists(self._vision_path):
            with self._model_lock:
                if self._vision_llm is None:
                    self._vision_llm = self._load_model(self._vision_path)
            self._schedule_unload_vision(60.0)

            try:
                # Run vision query
                v_res = self._vision_llm.create_chat_completion(
                    messages=[
                        {
                            "role": "user",
                            "content": f"Hãy quan sát hình ảnh thật kỹ và mô tả chi tiết các phần tử, văn bản, số liệu và bối cảnh để giải quyết yêu cầu: {user_prompt}",
                        }
                    ],
                    max_tokens=512,
                    temperature=0.2,
                )
                visual_description = v_res["choices"][0]["message"]["content"]
            except Exception as v_err:
                logger.warning(f"[ModelOrchestrator] LFM3-VL inference error: {v_err}. Falling back to OCR.")
                visual_description = ""

        # Fallback to OCR if VL failed or not installed
        if not visual_description:
            from utils.document_reader import read_image_file
            ocr_parts = []
            for img_p in image_paths:
                _, content, _ = read_image_file(img_p)
                if content:
                    ocr_parts.append(f"[{os.path.basename(img_p)}]:\n{content}")
            visual_description = (
                "\n\n".join(ocr_parts)
                if ocr_parts
                else "Hình ảnh đính kèm (Đã tiếp nhận tệp hình ảnh hợp lệ)."
            )

        step2 = PipelineStep(
            step_id="vision_extraction",
            title=f"👁️ {vision_model_name}: Trích xuất thị giác",
            content=visual_description,
            model_name=vision_model_name,
            duration_s=round(time.time() - t1, 2),
        )
        steps.append(step2)
        if on_step_callback:
            on_step_callback(step2)

        # ------------------------------------------------------------------ #
        # BƯỚC 3: DeepSeek Thinking - Suy luận logic chuyên sâu (<think>...</think>)
        # ------------------------------------------------------------------ #
        t2 = time.time()
        reasoning_text = ""
        has_thinking = False
        thinking_trace = ""
        reasoning_model_name = (
            "DeepSeek Thinking (R1)" if self._reasoning_path else "LFM3 1.7B Reasoning (In-Memory)"
        )

        reasoning_input = (
            f"DỮ LIỆU ĐƯỢC TRÍCH XUẤT TỪ HÌNH ẢNH:\n{visual_description}\n\n"
            f"YÊU CẦU CỦA NGƯỜI DÙNG: {user_prompt}\n\n"
            f"Hãy suy luận thật chi tiết từng bước để đưa ra giải pháp/câu trả lời chính xác và logic nhất."
        )

        if self._reasoning_path and os.path.exists(self._reasoning_path):
            with self._model_lock:
                if self._reasoning_llm is None:
                    self._reasoning_llm = self._load_model(self._reasoning_path)
            self._schedule_unload_reasoning(60.0)

            try:
                r_res = self._reasoning_llm.create_chat_completion(
                    messages=[
                        {
                            "role": "system",
                            "content": "Bạn là DeepSeek Thinking, mô hình chuyên suy luận logic chuyên sâu. Hãy đặt toàn bộ chuỗi tư duy phân tích của bạn vào trong thẻ <think>...</think> trước khi đưa ra kết luận.",
                        },
                        {"role": "user", "content": reasoning_input},
                    ],
                    max_tokens=768,
                    temperature=0.6,
                )
                reasoning_text = r_res["choices"][0]["message"]["content"]
            except Exception as r_err:
                logger.warning(f"[ModelOrchestrator] DeepSeek inference error: {r_err}. Falling back to LFM3.")
                reasoning_text = ""

        # Fallback to router if DeepSeek not installed or failed
        if not reasoning_text:
            try:
                fallback_prompt = (
                    f"Bạn là trợ lý logic. Dựa vào thông tin hình ảnh sau:\n{visual_description}\n\n"
                    f"Hãy giải đáp yêu cầu: {user_prompt}"
                )
                reasoning_text = router_llm_service.chat(
                    messages=[{"role": "user", "content": fallback_prompt}],
                    max_tokens=512,
                    temperature=0.5,
                )
            except Exception as fb_err:
                reasoning_text = f"Kết quả phân tích dựa trên hình ảnh: {visual_description}"

        # Extract <think> if present
        think_match = re.search(r"<think>(.*?)</think>", reasoning_text, flags=re.DOTALL)
        if think_match:
            has_thinking = True
            thinking_trace = think_match.group(1).strip()
            answer_without_think = re.sub(r"<think>.*?</think>", "", reasoning_text, flags=re.DOTALL).strip()
        else:
            answer_without_think = reasoning_text

        step3 = PipelineStep(
            step_id="deep_reasoning",
            title=f"🧠 {reasoning_model_name}: Chuỗi suy luận chuyên sâu",
            content=reasoning_text,
            model_name=reasoning_model_name,
            duration_s=round(time.time() - t2, 2),
        )
        steps.append(step3)
        if on_step_callback:
            on_step_callback(step3)

        # ------------------------------------------------------------------ #
        # BƯỚC 4: LFM3 1.7B (Dialogue Synthesizer) - Tổng hợp lời thoại tự nhiên
        # ------------------------------------------------------------------ #
        t3 = time.time()
        step4_title = "💬 LFM3 1.7B: Tổng hợp đàm thoại tự nhiên"
        synthesis_prompt = (
            f"Bạn là trợ lý ảo POP Assistant (sử dụng LFM3 1.7B). Dựa vào kết quả suy luận dưới đây, "
            f"hãy tổng hợp thành câu trả lời bằng tiếng Việt thân thiện, rõ ràng, gãy gọn và tự nhiên để trò chuyện với người dùng:\n\n"
            f"{answer_without_think}"
        )
        try:
            final_reply = router_llm_service.chat(
                messages=[{"role": "user", "content": synthesis_prompt}],
                max_tokens=512,
                temperature=0.7,
            )
        except Exception:
            final_reply = answer_without_think

        step4 = PipelineStep(
            step_id="dialogue_synthesis",
            title=step4_title,
            content=final_reply,
            model_name="LFM3 1.7B Synthesizer",
            duration_s=round(time.time() - t3, 2),
        )
        steps.append(step4)
        if on_step_callback:
            on_step_callback(step4)

        logger.info(f"[ModelOrchestrator] Tri-Model Pipeline finished in {sum(s.duration_s for s in steps):.2f}s.")

        return OrchestrationResult(
            text=final_reply,
            steps=steps,
            has_thinking=has_thinking,
            thinking_text=thinking_trace,
        )


def get_model_orchestrator() -> ModelOrchestrator:
    return ModelOrchestrator()


def find_attached_images(text: str) -> List[str]:
    """Tìm kiếm tất cả đường dẫn tệp ảnh hợp lệ trong tin nhắn người dùng."""
    if not text:
        return []

    found_paths: List[str] = []

    # 1. Tìm đường dẫn file tuyệt đối
    path_pattern = r'([A-Za-z]:\\[^\n\r"\'\*<>\|]+\.(?:png|jpg|jpeg|webp|bmp|gif))'
    matches = re.findall(path_pattern, text, flags=re.IGNORECASE)
    for p in matches:
        p_clean = p.strip()
        if os.path.isfile(p_clean) and p_clean not in found_paths:
            found_paths.append(p_clean)

    # 2. Tìm trong cấu trúc đính kèm [Tệp X: filename.png]
    file_pattern = r'\[Tệp \d+:\s*([^\]\n]+\.(?:png|jpg|jpeg|webp|bmp|gif))'
    file_matches = re.findall(file_pattern, text, flags=re.IGNORECASE)
    for fn in file_matches:
        fn_clean = fn.strip()
        if os.path.isfile(fn_clean) and fn_clean not in found_paths:
            found_paths.append(fn_clean)

    return found_paths
