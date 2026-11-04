"""LLM Fallback Handler - Context building, prompt generation, structured output parsing."""

import json
from typing import Any, List, Optional

from service.conversation.action_result import ActionResult
from service.conversation.context import ConversationContext
from utils.logger import get_logger

logger = get_logger(__name__)


class LLMFallbackHandler:
    """Handles LLM fallback response generation when intent is unknown or unstructured."""

    @staticmethod
    def generate(
        user_input: str,
        session_id: str,
        context: ConversationContext,
        memory_service: Any,
        llm_service: Any,
    ) -> Optional[ActionResult]:
        """Call LLM with conversation context and return ActionResult or None if LLM is disabled."""
        from service.llm_config import get_llm_config
        config = get_llm_config()

        if not config.enabled:
            return None

        logger.info(f"[LLMFallbackHandler] Calling LLM for: {user_input[:30]}...")

        # ----------------------------------------------------
        # KIỂM TRA ĐÍNH KÈM HÌNH ẢNH: KÍCH HOẠT CHUỖI 3 MODEL
        # ----------------------------------------------------
        try:
            from service.model_orchestrator import get_model_orchestrator, find_attached_images
            image_paths = find_attached_images(user_input)
            if image_paths:
                logger.info(f"[LLMFallbackHandler] Detected {len(image_paths)} attached images. Executing Tri-Model Orchestrator...")
                orchestrator = get_model_orchestrator()
                orch_result = orchestrator.process_multimodal_request(
                    user_prompt=user_input,
                    image_paths=image_paths,
                    router_llm_service=llm_service,
                    session_id=session_id,
                )
                pipeline_data = json.dumps([
                    {
                        "step_id": s.step_id,
                        "title": s.title,
                        "content": s.content,
                        "model": s.model_name,
                        "duration": s.duration_s
                    }
                    for s in orch_result.steps
                ], ensure_ascii=False)
                payload = f"<pipeline>{pipeline_data}</pipeline>\n{orch_result.text}"
                return ActionResult(text=payload)
        except Exception as orch_err:
            logger.error(f"[LLMFallbackHandler] Tri-Model Orchestrator error: {orch_err}. Falling back to standard LLM.")

        if hasattr(llm_service, 'is_model_available'):
            avail, err_detail = llm_service.is_model_available()
            if not avail:
                raise FileNotFoundError(
                    f"Mô hình AI chưa được tải về máy hoặc tệp không hợp lệ ({err_detail}). "
                    f"Vui lòng vào 'Model++' để tải mô hình hoặc copy tệp .gguf vào thư mục LLM-agents."
                )

        # 1. Build Context (long-term summary + recent history)
        history: List[dict] = []
        if memory_service and session_id:
            try:
                if hasattr(context, 'long_term_summary') and context.long_term_summary:
                    summary_text = (
                        f"TÓM TẮT HỘI THOẠI TRƯỚC ĐÓ (Ngữ cảnh tổng hợp sau mỗi 5 đoạn chat):\n"
                        f"- Ý định chính: {context.long_term_summary.get('user_intent', '')}\n"
                        f"- Thông tin / Sự kiện quan trọng: {', '.join(context.long_term_summary.get('key_facts', []))}\n"
                        f"- Tóm tắt diễn biến: {context.long_term_summary.get('summary', '')}"
                    )
                    history.append({"role": "system", "content": summary_text})

                sid_int = int(session_id) if session_id.isdigit() else 1
                raw_messages = memory_service.get_session_chat_messages(sid_int)
                if raw_messages:
                    hist_msgs = raw_messages[:-1] if raw_messages and raw_messages[-1][2] == user_input else raw_messages
                    for r in hist_msgs[-6:]:
                        sender = r[1]
                        role = "user" if sender == "user" else "assistant"
                        history.append({"role": role, "content": r[2]})
                else:
                    raw_history = memory_service.get_session_history(sid_int)
                    if raw_history:
                        for um, br, _ in raw_history[-5:]:
                            history.append({"role": "user", "content": um})
                            history.append({"role": "assistant", "content": br})
            except Exception as hist_err:
                logger.error(f"[LLMFallbackHandler] Error fetching history: {hist_err}")

        messages = history + [{"role": "user", "content": user_input}]

        schema = {
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "response": {"type": "string"},
            },
            "required": ["action", "response"],
        }

        try:
            from service.voice_ipc_bridge import get_voice_ipc_bridge
            get_voice_ipc_bridge().set_voice_state("THINKING_LLM")
        except Exception:
            pass

        try:
            raw_result_text = llm_service.chat(
                messages=messages,
                system_prompt=config.system_prompt,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                response_format={"type": "json_object", "schema": schema},
            )
        finally:
            try:
                from service.voice_ipc_bridge import get_voice_ipc_bridge
                get_voice_ipc_bridge().set_voice_state("IDLE")
            except Exception:
                pass

        # 2. Parse Structured Output (JSON)
        try:
            parsed_data = json.loads(raw_result_text)
            llm_text = parsed_data.get("response", "Mình không biết phải nói sao.")
            logger.info(f"[LLMFallbackHandler] Parsed JSON Action: {parsed_data.get('action')}")
        except Exception as json_err:
            logger.error(f"[LLMFallbackHandler] JSON Parse failed: {json_err}, raw: {raw_result_text[:50]}")
            llm_text = raw_result_text

        if llm_text:
            logger.info(f"[LLMFallbackHandler] LLM final response: {llm_text[:50]}...")
            return ActionResult(text=llm_text)

        return None
