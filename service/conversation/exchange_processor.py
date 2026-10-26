"""Exchange Processor - Orchestrates single-turn user-assistant dialogue."""

import threading
from typing import Any, Callable, Optional, Tuple

from service.conversation.action_result import ActionResult
from service.conversation.context import ContextManager, ConversationContext
from service.conversation.llm_fallback_handler import LLMFallbackHandler
from service.intern.text_utils import extract_location
from utils.logger import get_logger

logger = get_logger(__name__)


class ExchangeProcessor:
    """Processes user exchanges by orchestrating Agent Engine, intents, tools, LLM and TTS."""

    def __init__(
        self,
        action_handler: Any,
        audio_service: Any,
        user_controller: Any,
        context_manager: ContextManager,
        generation_cancel_event: threading.Event,
        get_intent_service_fn: Callable[[], Any],
        get_llm_service_fn: Callable[[], Any],
        get_memory_service_fn: Callable[[], Any],
    ):
        self.actions = action_handler
        self.audio = audio_service
        self.user = user_controller
        self.context_manager = context_manager
        self.cancel_event = generation_cancel_event
        self.get_intent_service = get_intent_service_fn
        self.get_llm_service = get_llm_service_fn
        self.get_memory_service = get_memory_service_fn
        self._cached_agent = None

    def handle_habit_confirmation(
        self,
        user_input: str,
        pending_habit_app: str,
        speak_callback: Optional[Callable] = None,
    ) -> Tuple[Optional[ActionResult], Optional[str]]:
        """Check if user input agrees to open a suggested habit app.
        
        Returns:
            (ActionResult, None) if user agreed and action was handled,
            (None, pending_habit_app) if user did not agree.
        """
        user_lower = user_input.lower().strip()
        agree_keywords = [
            "mở cho tôi", "mở đi", "có", "ok", "oke", "okay",
            "ừ", "ừm", "uh", "đồng ý", "mở", "yes", "yeah", "yep",
        ]
        if any(kw in user_lower for kw in agree_keywords):
            app_to_open = pending_habit_app
            user_name = self.user.get_display_name() or "guest"
            result = self.actions.handle("open_app", app_to_open, user_name, None)
            response = result.text if isinstance(result, ActionResult) else str(result)

            if speak_callback:
                speak_callback(response)
            else:
                self.audio.speak(response)

            action_res = result if isinstance(result, ActionResult) else ActionResult(text=response)
            return action_res, None

        return None, pending_habit_app

    def process(
        self,
        user_input: str,
        speak_callback: Optional[Callable] = None,
        user_name: str = "bạn",
        session_id: str = "default",
    ) -> ActionResult:
        """Process a single user exchange and return ActionResult."""
        self.cancel_event.clear()

        result_action: Optional[ActionResult] = None
        should_save = False
        memory_service = self.get_memory_service()
        context = self.context_manager.get_or_create(session_id, memory_service)

        # 1. Check and summarize every 5 messages
        if memory_service and session_id:
            try:
                llm = self.get_llm_service()
                summary_data = memory_service.summarize_session_if_needed(session_id, llm)
                if summary_data:
                    context.long_term_summary = summary_data
            except Exception as sum_err:
                logger.error(f"[ExchangeProcessor] Summarization check error: {sum_err}")

        # 2. Check AgentEngine First
        from service.agent.agent_engine import OpenClawAgentEngine
        if not self._cached_agent:
            self._cached_agent = OpenClawAgentEngine()

        plan = self._cached_agent.analyze_request(user_input)
        if plan.is_clarification_needed:
            result_action = ActionResult(
                text=plan.clarification_question or "Bạn có thể nói rõ hơn yêu cầu được không?"
            )
            should_save = False
        elif plan.needs_confirmation:
            result_action = ActionResult(
                text="Vui lòng xác nhận hành động.",
                needs_permission=True,
                tool_name=plan.tool_name,
                tool_args=plan.tool_args,
                summary_text=plan.summary_text,
                confirmation_title=plan.confirmation_title,
            )
            should_save = False
        elif plan.tool_name == "file_search":
            from tools.file_search_tool import FileSearchTool
            files = FileSearchTool.search_files(plan.tool_args.get("query", ""))
            if files:
                result_action = ActionResult(
                    text="Đã tìm thấy tệp.",
                    needs_permission=False,
                    tool_name="file_search",
                    tool_args={"files": files},
                )
            else:
                result_action = ActionResult(
                    text=f"Không tìm thấy tệp nào với từ khóa '{plan.tool_args.get('query')}*'."
                )
            should_save = True
        elif plan.tool_name == "web_search":
            from tools.web_tool import WebTool
            res = WebTool.search_or_read_web(plan.tool_args.get("query", ""))
            reply = res.get("summary") or res.get("content") or "Đã hoàn thành tra cứu web."
            result_action = ActionResult(text=reply)
            should_save = True

        # 3. Fallback to pending weather intent
        if result_action is None and context.is_pending("weather"):
            location = extract_location(user_input)
            if location:
                context.set_slot("location", location)
                result = self.actions.handle("weather", user_input, user_name, context)
                context.clear_pending()

                if isinstance(result, ActionResult):
                    result_action = result
                else:
                    result_action = ActionResult(text=str(result))
                should_save = True
            else:
                result_action = ActionResult(text="Bạn muốn xem thời tiết ở đâu?")
                should_save = False

        # 4. Intent classification and handling
        if result_action is None:
            intent_service = self.get_intent_service()
            intent = intent_service.classify(user_input)

            # Clear context if intent changed
            if context.pending_intent and intent != context.pending_intent:
                print(f"[Context] User changed from '{context.pending_intent}' to '{intent}' - clearing pending")
                context.clear_pending()

            # Handle name update
            if intent in ["update_name", "name"]:
                extracted_name = intent_service.extract_name(user_input)
                if extracted_name:
                    old_name, new_name = self.user.update_user_name(extracted_name)
                    if new_name:
                        user_name = new_name
                        self.actions.set_user_name(new_name)
                        result_action = ActionResult(
                            text=f"Chào {new_name}! Rất vui được gặp bạn. Bạn cần mình giúp gì không?"
                        )
                    else:
                        result_action = ActionResult(
                            text=f"Chào {extracted_name}! Rất vui được gặp bạn. Bạn cần mình giúp gì không?"
                        )
                else:
                    result_action = ActionResult(text="Bạn có thể nói rõ tên của bạn được không?")
                should_save = True
            elif intent == "unknown":
                # LLM fallback
                try:
                    llm = self.get_llm_service()
                    result_action = LLMFallbackHandler.generate(
                        user_input=user_input,
                        session_id=session_id,
                        context=context,
                        memory_service=memory_service,
                        llm_service=llm,
                    )
                    if result_action:
                        should_save = True
                except Exception as e:
                    logger.error(f"[ExchangeProcessor] LLM failed: {e}")
                    is_missing_model = (
                        isinstance(e, FileNotFoundError)
                        or "Model++" in str(e)
                        or "chưa được tải" in str(e)
                    )
                    if is_missing_model:
                        friendly_msg = "Không tìm thấy Model AI để xử lý yêu cầu của bạn."
                        result_action = ActionResult(text=friendly_msg)
                    else:
                        result_action = ActionResult(text=f"{e}")
                    should_save = True
            else:
                # Normal action handling
                result = self.actions.handle(intent, user_input, user_name, context)

                if isinstance(result, ActionResult):
                    if result.needs_slot:
                        pending_intent = result.intent if result.intent is not None else intent
                        if pending_intent is not None:
                            context.set_pending(pending_intent)
                        should_save = False
                    else:
                        should_save = True
                    result_action = result
                else:
                    result_action = ActionResult(text=str(result))
                    should_save = True

        # Final fallback if still None
        if result_action is None:
            result_action = ActionResult(text="Mình chưa hiểu ý bạn, bạn có thể nói rõ hơn không?")
            should_save = False

        # 5. Output delivery (TTS / UI notice)
        if self.cancel_event.is_set():
            logger.info("[ExchangeProcessor] Generation cancelled before TTS.")
            return ActionResult(text="")

        self._deliver_output(result_action, speak_callback)

        # 6. Save completed exchange
        if should_save and memory_service and result_action.text:
            try:
                if isinstance(session_id, int):
                    session_id_int = session_id
                elif isinstance(session_id, str) and session_id.isdigit():
                    session_id_int = int(session_id)
                else:
                    session_id_int = None

                memory_service.save_exchange(user_name, user_input, result_action.text, session_id_int)
                self.context_manager.save(session_id, memory_service)

                # Trigger background summarization
                memory_service.trigger_summarization_if_needed(session_id, self.get_llm_service())
            except Exception as e:
                print(f"[Warning] Failed to save exchange: {e}")

        return result_action

    def _deliver_output(self, result_action: ActionResult, speak_callback: Optional[Callable]) -> None:
        """Deliver text output to user via speech or direct UI update."""
        if result_action.text and not result_action.needs_permission and result_action.tool_name != "file_search":
            is_special_notice = (
                result_action.text.startswith("⚠️")
                or "Mô hình AI hiện chưa được tải" in result_action.text
            )
            if is_special_notice:
                audio_view = getattr(self.audio, "view", None)
                if audio_view and hasattr(audio_view, "update_bot_text"):
                    audio_view.update_bot_text(result_action.text)
                elif speak_callback:
                    speak_callback(result_action.text, update_ui=True)
            else:
                if speak_callback:
                    speak_callback(result_action.text)
                else:
                    self.audio.speak(result_action.text)
        elif result_action.needs_permission:
            confirm_voice = f"Vui lòng xác nhận hành động: {result_action.summary_text}"
            if speak_callback:
                speak_callback(confirm_voice)
            else:
                self.audio.speak(confirm_voice)
