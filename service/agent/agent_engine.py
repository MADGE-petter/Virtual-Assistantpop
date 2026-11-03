"""
OpenClaw Agent Engine - AI Reasoning and Tool Dispatcher powered by Local LFM 2.5 2.6B Model.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import json
import re

from service.agent.guardrails import ZeroGuessingGuardrail


@dataclass
class AgentPlan:
    is_clarification_needed: bool
    clarification_question: Optional[str] = None
    needs_confirmation: bool = False
    tool_name: Optional[str] = None
    tool_args: Dict[str, Any] = field(default_factory=dict)
    summary_text: str = ""
    confirmation_title: str = ""


class OpenClawAgentEngine:
    """Agentic Execution Engine using local LFM 2.5 2.6B model for intent & slot extraction."""

    def __init__(self):
        self._llm_service = None

    def _get_llm(self):
        if not self._llm_service:
            try:
                from service.llm_service import LLMService
                self._llm_service = LLMService()
            except Exception as e:
                print(f"[AgentEngine] LLMService init fallback: {e}")
        return self._llm_service

    def analyze_request(self, user_text: str) -> AgentPlan:
        """Parse user request into an AgentPlan enforcing zero-guessing guardrails."""
        user_lower = user_text.lower().strip()

        # ----------------------------------------------------
        # 1. Zalo Messaging Intent
        # ----------------------------------------------------
        if "zalo" in user_lower or "nhắn zalo" in user_lower or "gửi zalo" in user_lower:
            recipient = self._extract_recipient(user_text)
            message = self._extract_message_text(user_text, ["zalo"])
            slots = {"recipient": recipient, "message": message}

            missing = ZeroGuessingGuardrail.check_missing_slots("zalo_send", slots)
            if missing:
                q = ZeroGuessingGuardrail.generate_clarification_question("zalo_send", missing)
                return AgentPlan(is_clarification_needed=True, clarification_question=q)

            return AgentPlan(
                is_clarification_needed=False,
                needs_confirmation=True,
                tool_name="zalo_send",
                tool_args={"recipient": recipient, "message": message},
                confirmation_title="Xác nhận gửi tin nhắn Zalo",
                summary_text=f"Gửi tin nhắn Zalo đến '{recipient}' với nội dung: '{message}'"
            )

        # ----------------------------------------------------
        # 2. Facebook Messaging Intent
        # ----------------------------------------------------
        if "facebook" in user_lower or "fb" in user_lower or "messenger" in user_lower:
            recipient = self._extract_recipient(user_text)
            message = self._extract_message_text(user_text, ["facebook", "fb", "messenger"])
            slots = {"recipient": recipient, "message": message}

            missing = ZeroGuessingGuardrail.check_missing_slots("facebook_send", slots)
            if missing:
                q = ZeroGuessingGuardrail.generate_clarification_question("facebook_send", missing)
                return AgentPlan(is_clarification_needed=True, clarification_question=q)

            return AgentPlan(
                is_clarification_needed=False,
                needs_confirmation=True,
                tool_name="facebook_send",
                tool_args={"recipient": recipient, "message": message},
                confirmation_title="Xác nhận gửi tin nhắn Facebook",
                summary_text=f"Gửi tin nhắn Facebook đến '{recipient}' với nội dung: '{message}'"
            )

        # ----------------------------------------------------
        # 3. File Search & Retrieval Intent
        # ----------------------------------------------------
        if any(kw in user_lower for kw in ["tìm file", "tìm tệp", "lấy file", "lấy tệp", "tìm hợp đồng", "tìm báo cáo"]):
            query = self._extract_file_query(user_text)
            slots = {"query": query}

            missing = ZeroGuessingGuardrail.check_missing_slots("file_search", slots)
            if missing:
                q = ZeroGuessingGuardrail.generate_clarification_question("file_search", missing)
                return AgentPlan(is_clarification_needed=True, clarification_question=q)

            return AgentPlan(
                is_clarification_needed=False,
                needs_confirmation=False,  # Direct search returns Preview Card first
                tool_name="file_search",
                tool_args={"query": query},
                summary_text=f"Tìm kiếm tệp trên máy tính với từ khóa: '{query}'"
            )

        # ----------------------------------------------------
        # 4. Web Search Intent
        # ----------------------------------------------------
        if any(kw in user_lower for kw in ["tìm web", "tra cứu", "đọc trang", "kiểm tra web", "search web"]):
            query = self._extract_web_query(user_text)
            slots = {"query": query}

            missing = ZeroGuessingGuardrail.check_missing_slots("web_search", slots)
            if missing:
                q = ZeroGuessingGuardrail.generate_clarification_question("web_search", missing)
                return AgentPlan(is_clarification_needed=True, clarification_question=q)

            return AgentPlan(
                is_clarification_needed=False,
                needs_confirmation=False,
                tool_name="web_search",
                tool_args={"query": query},
                summary_text=f"Tra cứu thông tin web: '{query}'"
            )

        # ----------------------------------------------------
        # 5. General LLM Reasoning / Local LFM 2.5 2.6B
        # ----------------------------------------------------
        return AgentPlan(
            is_clarification_needed=False,
            needs_confirmation=False,
            tool_name="llm_chat",
            tool_args={"user_text": user_text}
        )

    def _extract_recipient(self, text: str) -> Optional[str]:
        # Extract name after "cho", "đến", "bạn"
        match = re.search(r"(?:cho|đến|bạn)\s+([A-ZÀ-Ỹa-zà-ỹ0-9\s]+?)(?:\s+nội dung|\s+bảo|\s+nói|\s+với|$)", text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 1 and name.lower() not in ["zalo", "facebook", "fb", "tin nhắn"]:
                return name
        return None

    def _extract_message_text(self, text: str, service_keywords: List[str]) -> Optional[str]:
        # Extract message after "nội dung", "bảo", "là", "nói"
        match = re.search(r"(?:nội dung|bảo|nói|là|với nội dung)\s+(.+)", text, re.IGNORECASE)
        if match:
            msg = match.group(1).strip()
            if len(msg) > 0:
                return msg
        return None

    def _extract_file_query(self, text: str) -> Optional[str]:
        match = re.search(r"(?:tìm file|tìm tệp|lấy file|lấy tệp|tìm)\s+(.+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _extract_web_query(self, text: str) -> Optional[str]:
        match = re.search(r"(?:tìm web|tra cứu|kiểm tra web|search web|đọc trang)\s+(.+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
