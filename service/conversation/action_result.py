"""Action Result - Data structure representing result of an action/exchange."""

from typing import Any, Dict, Optional


class ActionResult:
    """Represents the outcome of a handled intent, tool call, or LLM exchange."""

    def __init__(
        self,
        text: str,
        needs_slot: Optional[str] = None,
        intent: Optional[str] = None,
        needs_permission: bool = False,
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None,
        summary_text: Optional[str] = None,
        confirmation_title: Optional[str] = None,
    ):
        self.text = text
        self.needs_slot = needs_slot
        self.intent = intent
        self.needs_permission = needs_permission
        self.tool_name = tool_name
        self.tool_args = tool_args or {}
        self.summary_text = summary_text
        self.confirmation_title = confirmation_title

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"ActionResult(text={self.text!r}, needs_permission={self.needs_permission})"
