"""Conversation Service - Unified conversation handling orchestrator.

Merges Session management, Main loop, First interaction greeting, and delegates
exchange processing, LLM fallback, and context management to modular components.
"""
from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

# Export ActionResult and ConversationContext early to avoid circular import issues
from service.conversation.action_result import ActionResult
from service.conversation.context import ContextManager, ConversationContext
from service.conversation.exchange_processor import ExchangeProcessor
from utils.logger import get_logger

if TYPE_CHECKING:
    from controller.interfaces import (
        IActionHandler,
        IAudioService,
        ISqlService,
        IUserController,
    )

logger = get_logger(__name__)


class ConversationService:
    """Unified conversation service orchestrator - coordinates session, loop, and exchange flow."""

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

        # Modular context & state
        self._context_manager = ContextManager()
        self._contexts: Dict[str, ConversationContext] = self._context_manager.contexts

        # Lazy services
        self._intent_service = None
        self._memory_service = None
        self._llm_service = None

        # Delegated exchange processor
        self._exchange_processor = ExchangeProcessor(
            action_handler=self.actions,
            audio_service=self.audio,
            user_controller=self.user,
            context_manager=self._context_manager,
            generation_cancel_event=self._generation_cancel_event,
            get_intent_service_fn=self._get_intent_service,
            get_llm_service_fn=self._get_llm_service,
            get_memory_service_fn=lambda: self._memory_service,
        )

    # ==================== SESSION MANAGEMENT ====================

    def start_session(self) -> None:
        user_name = self.user.get_display_name() or "guest"
        self._session_id = self.sql.start_session(user_name)
        print(f"[ConversationService] Session started: {self._session_id}")

    def end_session(self) -> None:
        if self._session_id:
            self.sql.end_session(self._session_id)
            print(f"[ConversationService] Session ended: {self._session_id}")
            if str(self._session_id) in self._contexts:
                del self._contexts[str(self._session_id)]
            self._session_id = None

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
        if hasattr(self.audio, "stop_speaking"):
            self.audio.stop_speaking()

    def init_intent_service(self):
        """Eager init IntentService at startup."""
        return self._get_intent_service()

    def init_memory_service(self, memory_service):
        """Inject MemoryService."""
        self._memory_service = memory_service

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
            if hasattr(llm, "switch_model"):
                llm.switch_model(model_name)
                logger.info(f"[ConversationService] Forwarded set_model('{model_name}') to LLMService.")
        except Exception as e:
            logger.error(f"[ConversationService] Failed to set model: {e}")

    # ==================== EXCHANGE PROCESSING ====================

    def _process_exchange(
        self,
        user_input: str,
        speak_callback: Optional[Callable] = None,
    ) -> ActionResult:
        # Check pending habit suggestion
        if self._pending_habit_app:
            res, pending = self._exchange_processor.handle_habit_confirmation(
                user_input=user_input,
                pending_habit_app=self._pending_habit_app,
                speak_callback=speak_callback,
            )
            self._pending_habit_app = pending
            if res is not None:
                return res

        return self.process_exchange(user_input, speak_callback)

    def process_exchange(
        self,
        user_input: str,
        speak_callback: Optional[Callable] = None,
        user_name: str = "bạn",
        session_id: str = "default",
    ) -> ActionResult:
        """Process a single user-bot exchange and return ActionResult."""
        return self._exchange_processor.process(
            user_input=user_input,
            speak_callback=speak_callback,
            user_name=user_name,
            session_id=session_id,
        )

    def _should_exit(self, user_input: str) -> bool:
        exit_words = ["goodbye", "tạm biệt", "bye", "thôi"]
        return any(word in user_input.lower() for word in exit_words)

    # ==================== CONTEXT MANAGEMENT ====================

    def get_or_create_context(self, session_id: str) -> ConversationContext:
        return self._context_manager.get_or_create(session_id, self._memory_service)

    def save_context(self, session_id: str) -> None:
        self._context_manager.save(session_id, self._memory_service)

    def end_session_context(self, session_id: str) -> None:
        self._context_manager.end_session(session_id, self._memory_service)

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