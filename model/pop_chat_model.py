"""
POP Chat Model - Data models for messages and conversation sessions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import uuid


@dataclass
class ChatMessage:
    """Represents a single chat message in POP Assistant."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = "user"  # "user" or "bot" / "pop"
    text: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M"))
    status: str = "sent"  # "sent", "thinking", "generating", "done", "error"
    actions: List[str] = field(default_factory=lambda: ["copy", "like", "dislike", "retry"])
    avatar: Optional[str] = None


@dataclass
class ConversationSession:
    """Represents a conversation history session."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Cuộc trò chuyện mới"
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M"))
    category: str = "Hôm nay"  # "Hôm nay", "Hôm qua", "7 ngày trước"
    created_at: datetime = field(default_factory=datetime.now)
    messages: List[ChatMessage] = field(default_factory=list)


class PopChatModel:
    """Model managing chat conversations and active message thread."""

    def __init__(self):
        self.sessions: List[ConversationSession] = []
        self.active_session_id: Optional[str] = None
        self.model_name: str = "LFM2.5 2.6B (Local)"
        self.available_models: List[str] = [
            "LFM2.5 2.6B (Local)",
            "LFM2.5 7B (Local)",
            "GPT-4o Mini (Cloud)",
            "Claude 3.5 Sonnet (Cloud)"
        ]
        self._init_empty_session()

    def _init_empty_session(self):
        """Start with a clean initial conversation session."""
        initial_session = ConversationSession(
            id=str(uuid.uuid4()),
            title="Cuộc trò chuyện mới",
            timestamp=datetime.now().strftime("%H:%M"),
            category="Hôm nay",
            messages=[
                ChatMessage(
                    sender="bot",
                    text="Xin chào! Tôi là POP AI Assistant. Tôi có thể giúp gì cho bạn hôm nay?",
                    timestamp=datetime.now().strftime("%I:%M %p")
                )
            ]
        )
        self.sessions = [initial_session]
        self.active_session_id = initial_session.id

    def get_active_session(self) -> Optional[ConversationSession]:
        for s in self.sessions:
            if s.id == self.active_session_id:
                return s
        return None

    def get_categorized_sessions(self) -> dict:
        categorized = {}
        for s in self.sessions:
            cat = getattr(s, 'category', "Hôm nay") or "Hôm nay"
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(s)
        return categorized

    def create_new_session(self, title: str = "Cuộc trò chuyện mới") -> ConversationSession:
        new_session = ConversationSession(
            title=title,
            timestamp=datetime.now().strftime("%H:%M"),
            category="Hôm nay"
        )
        self.sessions.insert(0, new_session)
        self.active_session_id = new_session.id
        return new_session

    def set_active_session(self, session_id: str):
        for s in self.sessions:
            if s.id == session_id:
                s.is_active = True
                self.active_session_id = session_id
            else:
                s.is_active = False

    def delete_session(self, session_id: str):
        self.sessions = [s for s in self.sessions if s.id != session_id]
        if self.active_session_id == session_id:
            self.active_session_id = self.sessions[0].id if self.sessions else None

    def add_user_message(self, text: str) -> ChatMessage:
        session = self.get_active_session()
        if not session:
            session = self.create_new_session(title=text[:25])
        msg = ChatMessage(sender="user", text=text, timestamp=datetime.now().strftime("%I:%M %p"))
        session.messages.append(msg)
        return msg

    def add_bot_message(self, text: str) -> ChatMessage:
        session = self.get_active_session()
        if not session:
            session = self.create_new_session()
        msg = ChatMessage(sender="bot", text=text, timestamp=datetime.now().strftime("%I:%M %p"))
        session.messages.append(msg)
        return msg
