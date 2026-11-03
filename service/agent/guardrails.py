"""
Zero-Guessing Guardrails - Strict non-guessing policy and human-in-the-loop confirmation generator.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class ToolRequirement:
    tool_name: str
    required_slots: List[str]
    slot_labels: Dict[str, str] = field(default_factory=dict)


class ZeroGuessingGuardrail:
    """Enforces zero-guessing policy for OpenClaw-style Agentic tool execution."""

    TOOL_REQUIREMENTS = {
        "zalo_send": ToolRequirement(
            tool_name="zalo_send",
            required_slots=["recipient", "message"],
            slot_labels={"recipient": "người nhận", "message": "nội dung tin nhắn"}
        ),
        "facebook_send": ToolRequirement(
            tool_name="facebook_send",
            required_slots=["recipient", "message"],
            slot_labels={"recipient": "người nhận", "message": "nội dung tin nhắn"}
        ),
        "web_search": ToolRequirement(
            tool_name="web_search",
            required_slots=["query"],
            slot_labels={"query": "từ khóa hoặc địa chỉ trang web"}
        ),
        "file_search": ToolRequirement(
            tool_name="file_search",
            required_slots=["query"],
            slot_labels={"query": "tên tệp hoặc nội dung cần tìm"}
        ),
        "file_action": ToolRequirement(
            tool_name="file_action",
            required_slots=["file_path", "action"],
            slot_labels={"file_path": "đường dẫn tệp", "action": "hành động (Mở/Copy/Gửi)"}
        )
    }

    @classmethod
    def check_missing_slots(cls, tool_name: str, slots: Dict[str, Any]) -> List[str]:
        """Check if any required parameters are missing for a tool."""
        req = cls.TOOL_REQUIREMENTS.get(tool_name)
        if not req:
            return []

        missing = []
        for slot in req.required_slots:
            val = slots.get(slot)
            if not val or str(val).strip() in ["", "None", "unknown", "mơ hồ"]:
                missing.append(req.slot_labels.get(slot, slot))
        return missing

    @classmethod
    def generate_clarification_question(cls, tool_name: str, missing_slots: List[str]) -> str:
        """Generate clarification question asking user for missing parameters."""
        missing_str = ", ".join(missing_slots)
        if tool_name == "zalo_send":
            return f"Bạn muốn gửi tin nhắn Zalo cho ai và với nội dung gì? (Còn thiếu: {missing_str})"
        elif tool_name == "facebook_send":
            return f"Bạn muốn gửi tin nhắn Facebook cho ai và với nội dung gì? (Còn thiếu: {missing_str})"
        elif tool_name == "file_search":
            return f"Bạn muốn tìm tệp nào hoặc tệp có chứa nội dung gì? (Còn thiếu: {missing_str})"
        elif tool_name == "web_search":
            return f"Bạn muốn tìm kiếm thông tin gì trên Web? (Còn thiếu: {missing_str})"
        else:
            return f"Vui lòng cung cấp thêm thông tin về: {missing_str}."
