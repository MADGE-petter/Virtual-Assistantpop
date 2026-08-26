"""Conversation Controller - Thin wrapper for ConversationService (backward compatibility)."""

from typing import Callable, Optional

from controller.interfaces import (
    IActionHandler,
    IAudioService,
    ISqlService,
    IUserController,
)
from service.conversation_service import ConversationService


class ConversationController:
    """Thin wrapper - delegates to ConversationService."""
    
    def __init__(
        self,
        audio_service: IAudioService,
        sql_service: ISqlService,
        action_handler: IActionHandler,
        user_controller: IUserController,
        interactive_alert_service=None,
    ):
        self.service = ConversationService(
            audio_service,
            sql_service,
            action_handler,
            user_controller,
            interactive_alert_service,
        )

    def init_intent_service(self):
        self.service.init_intent_service()

    def start_session(self) -> None:
        self.service.start_session()

    def end_session(self) -> None:
        self.service.end_session()

    def run_main_loop(
        self,
        get_input_callback: Callable[[], Optional[str]],
        on_idle_callback: Optional[Callable] = None,
        idle_timeout: int = 15,
    ) -> None:
        self.service.run_main_loop(
            get_input_callback=get_input_callback,
            on_idle_callback=on_idle_callback,
            idle_timeout=idle_timeout,
        )

    def run_first_interaction(
        self,
        get_input_callback: Callable[[], Optional[str]],
        speak_callback: Optional[Callable] = None,
        from_wake_up: bool = False,
    ) -> None:
        self.service.run_first_interaction(
            get_input_callback=get_input_callback,
            speak_callback=speak_callback,
            from_wake_up=from_wake_up,
        )

    def stop(self) -> None:
        self.service.stop()

    def set_assistant_active(self, active: bool) -> None:
        self.service.set_assistant_active(active)
    
    # ============ MVC PUBLIC API ============
    
    def handle_user_message(self, text: str):
        """Handle user message from View (text input)."""
        # Run in background thread to avoid blocking UI
        import threading
        threading.Thread(
            target=self._process_user_message,
            args=(text,),
            daemon=True
        ).start()
    
    def _process_user_message(self, text: str):
        """Process user message in background."""
        try:
            self.service.process_exchange(
                user_input=text,
                speak_callback=self.service.audio.speak,
                user_name=getattr(self.service.user, 'display_name', 'bạn') or 'bạn',
                session_id=self.service._session_id or "default"
            )
        except Exception as e:
            print(f"[ConversationController] Error processing message: {e}")
            import traceback
            traceback.print_exc()
    
    def stop_generation(self):
        """Stop current generation."""
        self.service.stop()
    
    def start_new_conversation(self):
        """Start a new conversation session."""
        self.service.end_session()
        self.service.start_session()
