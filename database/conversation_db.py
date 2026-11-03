"""ConversationDB module.

Tập hợp các repository (User, Session, Message) vào một giao diện thống nhất,
đảm bảo tương thích hoàn toàn 100% với toàn bộ mã nguồn hiện tại.
"""

from typing import Optional

from utils.logger import get_logger
from utils.paths import get_database_path

from .base_repository import BaseRepository
from .schema import init_default_schema
from .user_repository import UserRepository
from .session_repository import SessionRepository
from .message_repository import MessageRepository

logger = get_logger(__name__)


class ConversationDB(UserRepository, SessionRepository, MessageRepository, BaseRepository):
    """Database operations for conversations and unified user/session/message access."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            resolved = db_path
        else:
            resolved = get_database_path()
        super().__init__(resolved)
        self.init_database()

    def init_database(self):
        """Initialize database tables if they don't exist"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            self._create_default_schema(cursor)
            conn.commit()
            logger.info("Checked conversation DB schema for %s", self.db_path)

            conn.close()
        except Exception as e:
            logger.error("Database initialization error: %s", e, exc_info=True)
            raise

    def _create_default_schema(self, cursor):
        """Create the default schema required for the conversation database."""
        init_default_schema(cursor)
