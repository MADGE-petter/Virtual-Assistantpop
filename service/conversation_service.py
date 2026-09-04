"""Conversation Service - Unified conversation handling (merges Flow + Service + Controller).

Handles:
- Session management (start/end)
- First interaction (greeting, name collection)
- Main conversation loop
- Habit suggestions (non-blocking)
- Interactive alert responses
- Intent classification + LLM fallback
- Context/slot management
"""
import time
import threading
from typing import Any, Callable, Dict, List, Optional

from controller.interfaces import (
    IActionHandler,
    IAudioService,
    ISqlService,
    IUserController,
)
from service.intern.text_utils import extract_location
from utils.logger import get_logger

logger = get_logger(__name__)


class ActionResult:
    def __init__(self, text: str, needs_slot: Optional[str] = None, 
                 intent: Optional[str] = None, needs_permission: bool = False,
                 tool_name: Optional[str] = None, tool_args: Optional[Dict] = None,
                 summary_text: Optional[str] = None, confirmation_title: Optional[str] = None):
        self.text = text
        self.needs_slot = needs_slot
        self.intent = intent
        self.needs_permission = needs_permission
        self.tool_name = tool_name
        self.tool_args = tool_args or {}
        self.summary_text = summary_text
        self.confirmation_title = confirmation_title
    
    def __str__(self):
        return self.text
    
    def __repr__(self):
        return f"ActionResult(text={self.text!r}, needs_permission={self.needs_permission})"


class ConversationContext:
    def __init__(self):
        self.pending_intent: Optional[str] = None
        self.slots: Dict[str, Any] = {} 
        self.slot_history: Dict[str, List[Any]] = {} 
        self.long_term_summary: Optional[dict] = None
        self.last_summarized_count: int = 0
    
    def set_pending(self, intent: str, **slots):
        self.pending_intent = intent
        self.slots.update(slots)
    
    def set_slot(self, key: str, value: Any) -> bool:
        overwritten = key in self.slots
        if overwritten:
            if key not in self.slot_history:
                self.slot_history[key] = []
            self.slot_history[key].append(self.slots[key])
            print(f"[Context] Slot '{key}' changed: '{self.slots[key]}' → '{value}'")
        self.slots[key] = value
        return overwritten
    
    def clear_pending(self):
        self.pending_intent = None
        self.slots.clear()
        self.slot_history.clear()
    
    def is_pending(self, intent: str) -> bool:
        return self.pending_intent == intent
    
    def get_slot(self, key: str, default=None):
        return self.slots.get(key, default)


class ConversationService:
    """Unified conversation service - handles all conversation logic."""
    
    def __init__(
        self,
        audio_service: IAudioService,
        sql_service: ISqlService,
        action_handler: IActionHandler,
        user_controller: IUserController,
    ):
        self.audio = audio_service
        self.sql = sql_service
        self.actions = action_handler
        self.user = user_controller

        # State
        self._assistant_active = False
        self._session_id: Optional[int] = None
        self._last_input: Optional[str] = None
        self._first_greeting_done = False
        self._pending_habit_app: Optional[str] = None
        self._generation_cancel_event = threading.Event()

        # Lazy services
        self._intent_service = None
        self._memory_service = None
        self._llm_service = None
        
        # Session-based contexts
        self._contexts: Dict[str, ConversationContext] = {}

    # ==================== SESSION MANAGEMENT ====================
    
    def start_session(self) -> None:
        user_name = self.user.get_display_name() or "guest"
        self._session_id = self.sql.start_session(user_name)
        print(f"[ConversationService] Session started: {self._session_id}")

    def end_session(self) -> None:
        if self._session_id:
            self.sql.end_session(self._session_id)
            print(f"[ConversationService] Session ended: {self._session_id}")
            self._session_id = None
        # Clear contexts for this session
        if self._session_id and str(self._session_id) in self._contexts:
            del self._contexts[str(self._session_id)]

    def set_assistant_active(self, active: bool) -> None:
        self._assistant_active = active

    def stop_conversation(self) -> None:
        """Stop the main conversation loop (End current interaction)."""
        logger.info("[ConversationService] stop_conversation triggered.")
        self.set_assistant_active(False)

    def stop_generation(self) -> None:
        """Stop current LLM generation and stop TTS."""
        logger.info("[ConversationService] stop_generation triggered.")
        self._generation_cancel_event.set()
        if hasattr(self.audio, 'stop_speaking'):
            self.audio.stop_speaking()

    def init_intent_service(self):
        """Eager init IntentService at startup."""
        return self._get_intent_service()

    # ==================== MAIN CONVERSATION LOOP ====================
    
    def run_main_loop(
        self,
        get_input_callback: Callable[[], Optional[str]],
        on_idle_callback: Optional[Callable] = None,
        idle_timeout: int = 15,
    ) -> None:
        print("[ConversationService] Main loop starting...")
        self._assistant_active = True
        last_interaction = time.time()

        try:
            while self._assistant_active:
                if getattr(self.audio, "is_speaking", False):
                    last_interaction = time.time()
                    time.sleep(0.1)
                    continue

                idle_time = time.time() - last_interaction
                # Sleep mode disabled: assistant remains active continuously for mascot interaction

                user_input = get_input_callback()

                if not user_input or user_input in ["...", "", None, 0]:
                    time.sleep(1)
                    continue

                if user_input == self._last_input:
                    time.sleep(1)
                    continue

                self._last_input = user_input
                last_interaction = time.time()

                if self._should_exit(user_input):
                    self._assistant_active = False
                    break

                self._process_exchange(user_input)

        except Exception as e:
            print(f"[ConversationService] Error in main loop: {e}")
            import traceback
            traceback.print_exc()

    def run_first_interaction(
        self,
        get_input_callback: Callable[[], Optional[str]],
        speak_callback: Optional[Callable] = None,
        from_wake_up: bool = False,
    ) -> None:
        user_name = self.user.get_display_name() or "bạn"

        if from_wake_up:
            greeting = f"Pop đây! Chào {user_name}, bạn cần giúp gì?"
            if speak_callback:
                speak_callback(greeting)
            else:
                self.audio.speak(greeting)
                self.audio.wait_until_speaking_done()
                
        self._first_greeting_done = True

    def set_model(self, model_name: str) -> None:
        """Forward switch model request to LLM Service."""
        try:
            llm = self._get_llm_service()
            if hasattr(llm, 'switch_model'):
                llm.switch_model(model_name)
                logger.info(f"[ConversationService] Forwarded set_model('{model_name}') to LLMService.")
        except Exception as e:
            logger.error(f"[ConversationService] Failed to set model: {e}")

    # ==================== EXCHANGE PROCESSING ====================
    
    def _process_exchange(
        self,
        user_input: str,
        speak_callback: Optional[Callable] = None,
    ) -> str:
        # Check pending habit suggestion
        if self._pending_habit_app:
            user_lower = user_input.lower().strip()
            agree_keywords = ["mở cho tôi", "mở đi", "có", "ok", "oke", "okay", 
                            "ừ", "ừm", "uh", "đồng ý", "mở", "yes", "yeah", "yep"]
            if any(kw in user_lower for kw in agree_keywords):
                app_to_open = self._pending_habit_app
                self._pending_habit_app = None
                
                result = self.actions.handle("open_app", app_to_open, 
                                            self.user.get_display_name() or "guest", None)
                response = result.text if isinstance(result, ActionResult) else str(result)
                
                if speak_callback:
                    speak_callback(response)
                else:
                    self.audio.speak(response)
                return response

        return self.process_exchange(user_input, speak_callback)

    def process_exchange(self, user_input: str, 
                         speak_callback: Optional[Callable] = None,
                         user_name: str = "bạn",
                         session_id: str = "default"):
        """Process a single user-bot exchange and return ActionResult."""
        self._generation_cancel_event.clear()
        
        result_action = None  
        should_save = False  
        context = self.get_or_create_context(session_id)
        
        # Check AgentEngine First
        from service.agent.agent_engine import OpenClawAgentEngine
        agent_engine = getattr(self, '_cached_agent', None)
        if not agent_engine:
            agent_engine = OpenClawAgentEngine()
            self._cached_agent = agent_engine
        
        plan = agent_engine.analyze_request(user_input)
        if plan.is_clarification_needed:
            result_action = ActionResult(text=plan.clarification_question)
            should_save = False
        elif plan.needs_confirmation:
            result_action = ActionResult(
                text="Vui lòng xác nhận hành động.",
                needs_permission=True,
                tool_name=plan.tool_name,
                tool_args=plan.tool_args,
                summary_text=plan.summary_text,
                confirmation_title=plan.confirmation_title
            )
            should_save = False
        elif plan.tool_name == "file_search":
            from tools.file_search_tool import FileSearchTool
            files = FileSearchTool.search_files(plan.tool_args.get("query", ""))
            if files:
                result_action = ActionResult(text="Đã tìm thấy tệp.", needs_permission=False, tool_name="file_search", tool_args={"files": files})
            else:
                result_action = ActionResult(text=f"Không tìm thấy tệp nào với từ khóa '{plan.tool_args.get('query')}'.")
            should_save = True
        elif plan.tool_name == "web_search":
            from tools.web_tool import WebTool
            res = WebTool.search_or_read_web(plan.tool_args.get("query", ""))
            reply = res.get("summary") or res.get("content") or "Đã hoàn thành tra cứu web."
            result_action = ActionResult(text=reply)
            should_save = True
        
        # Fallback to legacy context & intents
        
        # Handle pending weather intent
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
        
        if result_action is None:
            intent_service = self._get_intent_service()
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
                        result_action = ActionResult(text=f"Chào {new_name}! Rất vui được gặp bạn. Bạn cần mình giúp gì không?")
                    else:
                        result_action = ActionResult(text=f"Chào {extracted_name}! Rất vui được gặp bạn. Bạn cần mình giúp gì không?")
                else:
                    result_action = ActionResult(text="Bạn có thể nói rõ tên của bạn được không?")
                should_save = True
            elif intent == "unknown":
                # LLM fallback with Context & Structured Output
                try:
                    from service.llm_config import get_llm_config
                    config = get_llm_config()
                    
                    if config.enabled:
                        logger.info(f"[ConversationService] Intent unknown, calling LLM for: {user_input[:30]}...")
                        llm = self._get_llm_service()
                        
                        # 1. Build Context (Lấy 5 lượt hội thoại gần nhất)
                        history = []
                        if self._memory_service and session_id:
                            try:
                                # Inject long term memory first
                                ctx = self.get_or_create_context(session_id)
                                if hasattr(ctx, 'long_term_summary') and ctx.long_term_summary:
                                    summary_text = (
                                        f"TÓM TẮT HỘI THOẠI TRƯỚC ĐÓ:\n"
                                        f"- Ý định chính: {ctx.long_term_summary.get('user_intent', '')}\n"
                                        f"- Sự kiện: {', '.join(ctx.long_term_summary.get('key_facts', []))}\n"
                                        f"- Tóm tắt: {ctx.long_term_summary.get('summary', '')}"
                                    )
                                    history.append({"role": "system", "content": summary_text})
                                
                                sid_int = int(session_id) if str(session_id).isdigit() else 1
                                raw_history = self._memory_service.get_session_history(sid_int)
                                if raw_history:
                                    # Lấy 5 lượt cuối
                                    for um, br, _ in raw_history[-5:]:
                                        history.append({"role": "user", "content": um})
                                        history.append({"role": "assistant", "content": br})
                            except Exception as hist_err:
                                logger.error(f"[ConversationService] Error fetching history: {hist_err}")
                        
                        messages = history + [{"role": "user", "content": user_input}]
                        
                        schema = {
                            "type": "object",
                            "properties": {
                                "action": {"type": "string"},
                                "response": {"type": "string"}
                            },
                            "required": ["action", "response"]
                        }
                        
                        raw_result_text = llm.chat(
                            messages=messages,
                            system_prompt=config.system_prompt,
                            temperature=config.temperature,
                            max_tokens=config.max_tokens,
                            response_format={"type": "json_object", "schema": schema}
                        )
                        
                        # 2. Parse Structured Output (JSON)
                        try:
                            import json
                            parsed_data = json.loads(raw_result_text)
                            llm_text = parsed_data.get("response", "Mình không biết phải nói sao.")
                            logger.info(f"[ConversationService] Parsed JSON Action: {parsed_data.get('action')}")
                        except Exception as json_err:
                            logger.error(f"[ConversationService] JSON Parse failed: {json_err}, raw: {raw_result_text[:50]}")
                            llm_text = raw_result_text # Fallback to raw text
                        
                        if llm_text:
                            logger.info(f"[ConversationService] LLM final response: {llm_text[:50]}...")
                            result_action = ActionResult(text=llm_text)
                            should_save = True
                except Exception as e:
                    logger.error(f"[ConversationService] LLM failed: {e}")
                    if not config.fallback_to_rules:
                        result_action = ActionResult(text="Xin lỗi, mình đang gặp chút sự cố với bộ não AI. Bạn nói lại được không?")
            else:
                # Normal action handling
                result = self.actions.handle(intent, user_input, user_name, context)
                
                if isinstance(result, ActionResult):
                    if result.needs_slot:
                        context.set_pending(result.intent)
                        should_save = False
                    else:
                        should_save = True
                    result_action = result
                else:
                    result_action = ActionResult(text=str(result))
                    should_save = True
        
        # Final fallback
        if result_action is None:
            result_action = ActionResult(text="Mình chưa hiểu ý bạn, bạn có thể nói rõ hơn không?")
            should_save = False
        
        # Speak result (Only speak if it doesn't need permission, or speak confirmation)
        if self._generation_cancel_event.is_set():
            logger.info("[ConversationService] Generation cancelled before TTS.")
            return ActionResult(text="")
            
        if result_action.text and not result_action.needs_permission and result_action.tool_name != "file_search":
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
        
        # Save completed exchange
        if should_save and self._memory_service and result_action.text:
            try:
                if isinstance(session_id, int):
                    session_id_int = session_id
                elif isinstance(session_id, str) and session_id.isdigit():
                    session_id_int = int(session_id)
                else:
                    session_id_int = None
                self._memory_service.save_exchange(user_name, user_input, result_action.text, session_id_int)
                self.save_context(session_id)
                # Trigger background summarization
                if hasattr(self, '_get_llm_service'):
                    self._memory_service.trigger_summarization_if_needed(session_id, self._get_llm_service())
            except Exception as e:
                print(f"[Warning] Failed to save exchange: {e}")
        
        return result_action
    
    def _should_exit(self, user_input: str) -> bool:
        exit_words = ["goodbye", "tạm biệt", "bye", "thôi"]
        return any(word in user_input.lower() for word in exit_words)

    # ==================== LAZY SERVICE INIT ====================
    
    def _get_intent_service(self):
        if self._intent_service is None:
            from service.intern import IntentService
            self._intent_service = IntentService()
        return self._intent_service
    
    def _get_llm_service(self):
        if self._llm_service is None:
            from service.llm_service import LLMService
            self._llm_service = LLMService()
        return self._llm_service

    def init_memory_service(self, memory_service):
        """Inject MemoryService."""
        self._memory_service = memory_service

    def get_or_create_context(self, session_id: str) -> ConversationContext:
        if session_id not in self._contexts:
            ctx = ConversationContext()
            if self._memory_service:
                saved = self._memory_service.load_context(session_id)
                if saved:
                    ctx.pending_intent = saved.get("pending_intent")
                    ctx.slots = saved.get("slots", {})
                    ctx.slot_history = saved.get("slot_history", {})
                    ctx.long_term_summary = saved.get("long_term_summary")
                    ctx.last_summarized_count = saved.get("last_summarized_count", 0)
            self._contexts[session_id] = ctx
        return self._contexts[session_id]
    
    def save_context(self, session_id: str):
        if self._memory_service and session_id in self._contexts:
            ctx = self._contexts[session_id]
            data = {
                "pending_intent": ctx.pending_intent,
                "slots": ctx.slots,
                "slot_history": ctx.slot_history,
                "long_term_summary": getattr(ctx, "long_term_summary", None),
                "last_summarized_count": getattr(ctx, "last_summarized_count", 0)
            }
            self._memory_service.save_context(session_id, data)
    
    def end_session_context(self, session_id: str):
        if session_id in self._contexts:
            self.save_context(session_id)
            del self._contexts[session_id]