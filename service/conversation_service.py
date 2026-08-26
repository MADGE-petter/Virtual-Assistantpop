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
from service.interactive_alert_service import InteractiveAlertService
from utils.logger import get_logger

logger = get_logger(__name__)


class ActionResult:
    def __init__(self, text: str, needs_slot: Optional[str] = None, 
                 intent: Optional[str] = None):
        self.text = text
        self.needs_slot = needs_slot
        self.intent = intent
    
    def __str__(self):
        return self.text
    
    def __repr__(self):
        return f"ActionResult(text={self.text!r}, needs_slot={self.needs_slot!r}, intent={self.intent!r})"


class ConversationContext:
    def __init__(self):
        self.pending_intent: Optional[str] = None
        self.slots: Dict[str, Any] = {} 
        self.slot_history: Dict[str, List[Any]] = {} 
    
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
        interactive_alert_service: Optional[InteractiveAlertService] = None,
    ):
        self.audio = audio_service
        self.sql = sql_service
        self.actions = action_handler
        self.user = user_controller
        self.interactive_alert_service = interactive_alert_service

        # State
        self._assistant_active = False
        self._session_id: Optional[int] = None
        self._last_input: Optional[str] = None
        self._first_greeting_done = False
        self._pending_habit_app: Optional[str] = None

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
            
            self._speak_habit_suggestion_if_any(speak_callback)
            
        self._first_greeting_done = True

    # ==================== HABIT SUGGESTIONS ====================
    
    def _get_habit_suggestion(self) -> Optional[str]:
        """Get habit suggestion with timeout to avoid blocking."""
        try:
            result = [None]
            
            def _query():
                try:
                    from controller.habit_tracker import get_habit_tracker
                    
                    user_id = 1
                    try:
                        user_name = self.user.get_display_name()
                        login_name = self.user.get_login_name() if hasattr(self.user, 'get_login_name') else None
                        lookup_name = login_name or user_name
                        if lookup_name and lookup_name not in ("bạn", "guest", None):
                            uid = self.sql.get_or_create_user(lookup_name)
                            if uid:
                                user_id = uid
                    except Exception:
                        pass
                    
                    tracker = get_habit_tracker()
                    suggestions = tracker.get_suggestions(user_id)
                    
                    if suggestions:
                        top = suggestions[0]
                        app_name = top.get('app', '')
                        confidence = top.get('confidence', 0)
                        count = top.get('count', 0)
                        
                        if confidence >= 0.6 and app_name:
                            self._pending_habit_app = app_name
                            result[0] = f"Gợi ý: Bạn thường dùng {app_name} vào giờ này ({count} lần gần đây). Có muốn mở không?"
                except Exception as e:
                    print(f"[ConversationService] Error getting habit suggestion: {e}")
            
            thread = threading.Thread(target=_query, daemon=True)
            thread.start()
            thread.join(timeout=1.5)
            
            return result[0]
        except Exception as e:
            print(f"[ConversationService] Error in _get_habit_suggestion: {e}")
            return None
    
    def _speak_habit_suggestion_if_any(self, speak_callback):
        """Speak habit suggestion if available, non-blocking."""
        try:
            def _query_and_speak():
                suggestion = self._get_habit_suggestion()
                if suggestion:
                    if speak_callback:
                        speak_callback(suggestion)
                    else:
                        self.audio.speak(suggestion)
            
            thread = threading.Thread(target=_query_and_speak, daemon=True)
            thread.start()
        except Exception as e:
            print(f"[ConversationService] Error in _speak_habit_suggestion: {e}")

    # ==================== EXCHANGE PROCESSING ====================
    
    def _process_exchange(
        self,
        user_input: str,
        speak_callback: Optional[Callable] = None,
    ) -> str:
        # Check interactive alert response first
        if self._is_interactive_response(user_input):
            return ""

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
                         session_id: str = "default") -> str:
        """Process a single user-bot exchange."""
        result_text = None  
        should_save = False  
        context = self.get_or_create_context(session_id)
        
        # Handle pending weather intent
        if context.is_pending("weather"):
            location = extract_location(user_input)
            if location:
                context.set_slot("location", location)
                result = self.actions.handle("weather", user_input, user_name, context)
                context.clear_pending()
                
                if isinstance(result, ActionResult):
                    result_text = result.text
                else:
                    result_text = str(result)
                should_save = True  
            else:
                result_text = "Bạn muốn xem thời tiết ở đâu?"
                should_save = False 
        
        if result_text is None:
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
                        result_text = f"Chào {new_name}! Rất vui được gặp bạn. Bạn cần mình giúp gì không?"
                    else:
                        result_text = f"Chào {extracted_name}! Rất vui được gặp bạn. Bạn cần mình giúp gì không?"
                else:
                    result_text = "Bạn có thể nói rõ tên của bạn được không?"
                should_save = True
            elif intent == "unknown":
                # LLM fallback
                try:
                    from service.llm_config import get_llm_config
                    config = get_llm_config()
                    
                    if config.enabled:
                        logger.info(f"[ConversationService] Intent unknown, calling LLM for: {user_input[:30]}...")
                        llm = self._get_llm_service()
                        
                        messages = [{"role": "user", "content": user_input}]
                        result_text = llm.chat(
                            messages=messages,
                            system_prompt=config.system_prompt,
                            temperature=config.temperature,
                            max_tokens=config.max_tokens
                        )
                        
                        if result_text:
                            logger.info(f"[ConversationService] LLM responded: {result_text[:50]}...")
                            should_save = True
                except Exception as e:
                    logger.error(f"[ConversationService] LLM failed: {e}")
                    if not config.fallback_to_rules:
                        result_text = "Xin l��i, mình đang gặp chút sự cố với bộ não AI. Bạn nói lại được không?"
            else:
                # Normal action handling
                result = self.actions.handle(intent, user_input, user_name, context)
                
                if isinstance(result, ActionResult):
                    if result.needs_slot:
                        context.set_pending(result.intent)
                        should_save = False
                    else:
                        should_save = True
                    result_text = result.text
                else:
                    result_text = str(result)
                    should_save = True
        
        # Final fallback
        if result_text is None:
            result_text = "Mình chưa hiểu ý bạn, bạn có thể nói rõ hơn không?"
            should_save = False
        
        # Speak result
        if result_text:
            if speak_callback:
                speak_callback(result_text)
            else:
                self.audio.speak(result_text)
        
        # Save completed exchange
        if should_save and self._memory_service and result_text:
            try:
                if isinstance(session_id, int):
                    session_id_int = session_id
                elif isinstance(session_id, str) and session_id.isdigit():
                    session_id_int = int(session_id)
                else:
                    session_id_int = None
                self._memory_service.save_exchange(user_name, user_input, result_text, session_id_int)
            except Exception as e:
                print(f"[Warning] Failed to save exchange: {e}")
        
        return result_text or ""
    
    def _is_interactive_response(self, user_input: str) -> bool:
        if not self.interactive_alert_service:
            return False
        return self.interactive_alert_service.try_handle_response(user_input)

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
            self._contexts[session_id] = ConversationContext()
        return self._contexts[session_id]
    
    def end_session_context(self, session_id: str):
        if session_id in self._contexts:
            del self._contexts[session_id]