"""Conversation Package - Modular components for dialogue handling."""

from service.conversation.action_result import ActionResult
from service.conversation.context import ContextManager, ConversationContext
from service.conversation.exchange_processor import ExchangeProcessor
from service.conversation.llm_fallback_handler import LLMFallbackHandler

__all__ = [
    "ActionResult",
    "ConversationContext",
    "ContextManager",
    "ExchangeProcessor",
    "LLMFallbackHandler",
]
