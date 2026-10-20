"""
POP Chat Model - Data models for messages and conversation sessions with SQLite persistence.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional
import uuid

from database.conversation_db import ConversationDB
from utils.logger import get_logger

logger = get_logger(__name__)


def parse_datetime(val) -> datetime:
    """Parse sqlite datetime string or return datetime object."""
    if isinstance(val, datetime):
        return val
    if not val:
        return datetime.now()
    val_str = str(val).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(val_str, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(val_str.replace("Z", ""))
    except Exception:
        return datetime.now()


def categorize_date(dt: datetime) -> str:
    """Return friendly category for session date: 'Hôm nay', 'Hôm qua', '7 ngày trước', 'Cũ hơn'."""
    now = datetime.now()
    today = now.date()
    msg_date = dt.date() if isinstance(dt, datetime) else dt
    diff_days = (today - msg_date).days

    if diff_days <= 0:
        return "Hôm nay"
    elif diff_days == 1:
        return "Hôm qua"
    elif diff_days <= 7:
        return "7 ngày trước"
    else:
        return "Cũ hơn"


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
    category: str = "Hôm nay"  # "Hôm nay", "Hôm qua", "7 ngày trước", "Cũ hơn"
    created_at: datetime = field(default_factory=datetime.now)
    messages: List[ChatMessage] = field(default_factory=list)
    is_active: bool = False


class PopChatModel:
    """Model managing chat conversations and active message thread with SQLite storage."""

    def __init__(self, username: Optional[str] = None):
        self.username: str = username or "user"
        self.sessions: List[ConversationSession] = []
        self.active_session_id: Optional[str] = None
        self.model_name: str = "LFM2.5 2.6B (Local)"
        self.available_models: List[str] = [
            "LFM2.5 2.6B (Local)",
            "LFM2.5 7B (Local)",
            "GPT-4o Mini (Cloud)",
            "Claude 3.5 Sonnet (Cloud)"
        ]
        self.db = ConversationDB()

        if username:
            self.load_user_sessions(username)
        else:
            self._init_empty_session()

    def _get_current_user_id(self) -> int:
        """Get or create user ID from DB, falling back to 1 if None."""
        user_id = self.db.get_or_create_user(self.username or "user")
        return user_id if user_id is not None else 1

    def _init_empty_session(self):
        """Start with a clean initial conversation session."""
        try:
            user_id = self._get_current_user_id()
            s_id = self.db.create_chat_session(user_id, title="Cuộc trò chuyện mới")
            session_id_str = str(s_id)
        except Exception:
            session_id_str = "1"

        initial_session = ConversationSession(
            id=session_id_str,
            title="Cuộc trò chuyện mới",
            timestamp=datetime.now().strftime("%H:%M"),
            category="Hôm nay",
            created_at=datetime.now(),
            messages=[],
            is_active=True
        )
        self.sessions = [initial_session]
        self.active_session_id = initial_session.id

    def load_user_sessions(self, username: str):
        """Load conversation history from SQLite for the specified username."""
        self.username = username or self.username or "user"
        try:
            # Clean up ghost empty sessions
            self.db.cleanup_empty_sessions()

            rows = self.db.get_user_chat_sessions(self.username)
            if not rows:
                self._init_empty_session()
                return

            loaded_sessions: List[ConversationSession] = []
            for s_id, title, created_at in rows:
                dt = parse_datetime(created_at)
                cat = categorize_date(dt)
                time_str = dt.strftime("%H:%M") if cat == "Hôm nay" else dt.strftime("%d/%m")

                msg_rows = self.db.get_session_chat_messages(s_id)
                msgs = [
                    ChatMessage(
                        id=str(r[0]),
                        sender=r[1],
                        text=r[2],
                        timestamp=r[3] or dt.strftime("%H:%M")
                    )
                    for r in msg_rows
                ]

                session = ConversationSession(
                    id=str(s_id),
                    title=title or "Cuộc trò chuyện mới",
                    timestamp=time_str,
                    category=cat,
                    created_at=dt,
                    messages=msgs,
                    is_active=False
                )
                loaded_sessions.append(session)

            if loaded_sessions:
                self.sessions = loaded_sessions
                self.active_session_id = self.sessions[0].id
                self.sessions[0].is_active = True
            else:
                self._init_empty_session()

        except Exception as e:
            logger.error("Failed to load user sessions from DB: %s", e, exc_info=True)
            self._init_empty_session()

    def get_active_session(self) -> Optional[ConversationSession]:
        for s in self.sessions:
            if s.id == self.active_session_id:
                return s
        if self.sessions:
            self.active_session_id = self.sessions[0].id
            self.sessions[0].is_active = True
            return self.sessions[0]
        return None

    def get_categorized_sessions(self) -> dict:
        order = ["Hôm nay", "Hôm qua", "7 ngày trước", "Cũ hơn"]
        categorized = {k: [] for k in order}
        for s in self.sessions:
            cat = getattr(s, 'category', "Hôm nay") or "Hôm nay"
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(s)
        return {k: v for k, v in categorized.items() if v}

    def create_new_session(self, title: str = "Cuộc trò chuyện mới") -> ConversationSession:
        """Create a new session or reuse existing empty active session."""
        active = self.get_active_session()
        if active and len(active.messages) == 0:
            active.title = title
            self.set_active_session(active.id)
            return active

        try:
            user_id = self._get_current_user_id()
            s_id = self.db.create_chat_session(user_id, title=title)
            session_id_str = str(s_id)
        except Exception as e:
            logger.error("Failed to create chat session in DB: %s", e)
            session_id_str = str(uuid.uuid4())

        new_session = ConversationSession(
            id=session_id_str,
            title=title,
            timestamp=datetime.now().strftime("%H:%M"),
            category="Hôm nay",
            created_at=datetime.now(),
            messages=[],
            is_active=True
        )
        self.sessions.insert(0, new_session)
        self.set_active_session(new_session.id)
        return new_session

    def set_active_session(self, session_id: str):
        for s in self.sessions:
            if s.id == session_id:
                s.is_active = True
                self.active_session_id = session_id
            else:
                s.is_active = False

    def delete_session(self, session_id: str):
        try:
            if session_id.isdigit():
                self.db.delete_session(int(session_id))
        except Exception as e:
            logger.error("Error deleting session %s: %s", session_id, e)

        self.sessions = [s for s in self.sessions if s.id != session_id]
        if self.active_session_id == session_id:
            if self.sessions:
                self.active_session_id = self.sessions[0].id
                self.sessions[0].is_active = True
            else:
                self.active_session_id = None

    def _ensure_persisted_session(self, session: ConversationSession) -> int:
        """Ensure session has a real integer database ID."""
        if not session.id.isdigit():
            user_id = self._get_current_user_id()
            real_id = self.db.create_chat_session(user_id, title=session.title)
            session.id = str(real_id)
            self.active_session_id = session.id
            return real_id
        return int(session.id)

    def add_user_message(self, text: str) -> ChatMessage:
        session = self.get_active_session()
        if not session:
            session = self.create_new_session(title=text.strip().replace("\n", " ")[:30] or "Cuộc trò chuyện mới")

        # Auto-update session title if it is default
        if session.title in ("Cuộc trò chuyện mới", "New Chat", ""):
            clean_title = text.strip().replace("\n", " ")[:30]
            if clean_title:
                session.title = clean_title
                if session.id.isdigit():
                    try:
                        self.db.update_session_title(int(session.id), session.title)
                    except Exception as e:
                        logger.error("Error updating title in DB: %s", e)

        # Ensure session exists in DB
        s_id = self._ensure_persisted_session(session)

        timestamp_str = datetime.now().strftime("%I:%M %p")
        msg = ChatMessage(sender="user", text=text, timestamp=timestamp_str)
        session.messages.append(msg)

        # Persist message to DB
        try:
            self.db.add_chat_message(s_id, "user", text, timestamp_str)
        except Exception as e:
            logger.error("Error persisting user message: %s", e)

        return msg

    def add_bot_message(self, text: str) -> ChatMessage:
        session = self.get_active_session()
        if not session:
            session = self.create_new_session()

        s_id = self._ensure_persisted_session(session)

        timestamp_str = datetime.now().strftime("%I:%M %p")
        msg = ChatMessage(sender="bot", text=text, timestamp=timestamp_str)
        session.messages.append(msg)

        # Persist message to DB
        try:
            self.db.add_chat_message(s_id, "bot", text, timestamp_str)

            # Also save exchange to conversations table for stats/analytics
            user_msg = ""
            for m in reversed(session.messages[:-1]):
                if m.sender == "user":
                    user_msg = m.text
                    break
            if user_msg:
                user_id = self._get_current_user_id()
                self.db.save_conversation(user_id, s_id, user_msg, text)
        except Exception as e:
            logger.error("Error persisting bot message: %s", e)

        return msg
