"""Conversation Context and Context Manager."""

from typing import Any, Dict, List, Optional


class ConversationContext:
    """Manages slot tracking, pending intents, and conversation memory for a session."""

    def __init__(self):
        self.pending_intent: Optional[str] = None
        self.slots: Dict[str, Any] = {}
        self.slot_history: Dict[str, List[Any]] = {}
        self.long_term_summary: Optional[dict] = None
        self.last_summarized_count: int = 0

    def set_pending(self, intent: Optional[str], **slots) -> None:
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

    def clear_pending(self) -> None:
        self.pending_intent = None
        self.slots.clear()
        self.slot_history.clear()

    def is_pending(self, intent: str) -> bool:
        return self.pending_intent == intent

    def get_slot(self, key: str, default: Any = None) -> Any:
        return self.slots.get(key, default)


class ContextManager:
    """Manages in-memory contexts keyed by session ID and persistence with MemoryService."""

    def __init__(self):
        self.contexts: Dict[str, ConversationContext] = {}

    def get_or_create(self, session_id: str, memory_service: Any = None) -> ConversationContext:
        if session_id not in self.contexts:
            ctx = ConversationContext()
            if memory_service:
                saved = memory_service.load_context(session_id)
                if saved:
                    ctx.pending_intent = saved.get("pending_intent")
                    ctx.slots = saved.get("slots", {})
                    ctx.slot_history = saved.get("slot_history", {})
                    ctx.long_term_summary = saved.get("long_term_summary")
                    ctx.last_summarized_count = saved.get("last_summarized_count", 0)
            self.contexts[session_id] = ctx
        return self.contexts[session_id]

    def save(self, session_id: str, memory_service: Any = None) -> None:
        if memory_service and session_id in self.contexts:
            ctx = self.contexts[session_id]
            data = {
                "pending_intent": ctx.pending_intent,
                "slots": ctx.slots,
                "slot_history": ctx.slot_history,
                "long_term_summary": getattr(ctx, "long_term_summary", None),
                "last_summarized_count": getattr(ctx, "last_summarized_count", 0),
            }
            memory_service.save_context(session_id, data)

    def end_session(self, session_id: str, memory_service: Any = None) -> None:
        if session_id in self.contexts:
            self.save(session_id, memory_service)
            del self.contexts[session_id]
