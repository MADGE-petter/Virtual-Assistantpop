"""Session Repository module - Quản lý phiên trò chuyện và vòng đời sessions."""

import uuid
from datetime import datetime
from typing import List, Optional

from utils.logger import get_logger
from .base_repository import BaseRepository

logger = get_logger(__name__)


class SessionRepository(BaseRepository):
    """Repository quản lý các phiên làm việc và phiên trò chuyện (sessions)."""

    def create_chat_session(self, user_id: Optional[int] = None, title: str = "Cuộc trò chuyện mới") -> int:
        """Create a new chat session with a title and return its session ID."""
        try:
            if user_id is None:
                user_id = 1
            conn = self._get_connection()
            cursor = conn.cursor()
            session_token = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO sessions (user_id, session_token, title, created_at, is_active)
                VALUES (?, ?, ?, ?, 1)
            """, (user_id, session_token, title, datetime.now()))
            session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            if session_id is None:
                return 1
            return session_id
        except Exception as e:
            logger.error("Error creating chat session: %s", e, exc_info=True)
            return 1

    def session_exists(self, session_id: int) -> bool:
        """Kiểm tra session có tồn tại trong database hay không."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM sessions WHERE id = ?", (session_id,))
            exists = cursor.fetchone() is not None
            conn.close()
            return exists
        except Exception:
            return False

    def update_session_title(self, session_id: int, title: str):
        """Update session title."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE sessions SET title = ? WHERE id = ?", (title, session_id))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Error updating session title: %s", e, exc_info=True)

    def get_user_chat_sessions(self, username: str, limit: int = 50) -> list:
        """Get all sessions for a user with title and created_at that have messages."""
        try:
            if hasattr(self, 'get_or_create_user'):
                user_id = self.get_or_create_user(username)
            else:
                conn_tmp = self._get_connection()
                cur_tmp = conn_tmp.cursor()
                cur_tmp.execute("SELECT id FROM users WHERE username = ?", (username,))
                row = cur_tmp.fetchone()
                user_id = row[0] if row else 1
                conn_tmp.close()

            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.id, COALESCE(s.title, 'Cuộc trò chuyện mới') as title, s.created_at
                FROM sessions s
                WHERE s.user_id = ?
                  AND (
                    EXISTS (SELECT 1 FROM chat_messages cm WHERE cm.session_id = s.id)
                    OR EXISTS (SELECT 1 FROM conversations c WHERE c.session_id = s.id)
                  )
                ORDER BY s.id DESC
                LIMIT ?
            """, (user_id, limit))
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            logger.error("Error getting user chat sessions: %s", e, exc_info=True)
            return []

    def delete_session(self, session_id: int):
        """Delete session and all its messages."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()
            conn.close()
            logger.info("Deleted session %s and associated messages", session_id)
        except Exception as e:
            logger.error("Error deleting session: %s", e, exc_info=True)

    def cleanup_empty_sessions(self, user_id: Optional[int] = None):
        """Clean up sessions that have 0 messages in both chat_messages and conversations."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            if user_id:
                cursor.execute("""
                    DELETE FROM sessions
                    WHERE user_id = ?
                      AND id NOT IN (SELECT DISTINCT session_id FROM chat_messages)
                      AND id NOT IN (SELECT DISTINCT session_id FROM conversations)
                """, (user_id,))
            else:
                cursor.execute("""
                    DELETE FROM sessions
                    WHERE id NOT IN (SELECT DISTINCT session_id FROM chat_messages)
                      AND id NOT IN (SELECT DISTINCT session_id FROM conversations)
                """)
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            if deleted > 0:
                logger.info("Cleaned up %s empty sessions", deleted)
        except Exception as e:
            logger.error("Error cleaning up empty sessions: %s", e)

    def start_session(self, user_id: Optional[int] = None) -> int:
        """Bắt đầu session mới và trả về session ID (integer)."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Nếu user_id là string, convert sang int nếu có thể
            if isinstance(user_id, str) and user_id.isdigit():
                user_id = int(user_id)
            elif user_id is None or (isinstance(user_id, str) and not user_id.isdigit()):
                user_id = 1  # Default to first user

            session_token = str(uuid.uuid4())

            cursor.execute("""
                INSERT INTO sessions (user_id, session_token, created_at)
                VALUES (?, ?, ?)
            """, (user_id, session_token, datetime.now()))

            session_id = cursor.lastrowid
            conn.commit()
            conn.close()

            if session_id is None:
                return 1
            return session_id

        except Exception as e:
            logger.error("Error starting session: %s", e, exc_info=True)
            return 1  # Return default session ID on error

    def end_session(self, session_id: int):
        """End a session"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE sessions 
                SET expires_at = ?
                WHERE id = ?
            """, (datetime.now(), session_id))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error("Error ending session: %s", e, exc_info=True)

    def get_user_sessions(self, user_id: int, limit: int = 20) -> list:
        """Get sessions for a user"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM sessions 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))

            result = cursor.fetchall()
            conn.close()

            return result

        except Exception as e:
            logger.error("Error getting sessions: %s", e, exc_info=True)
            return []

    def get_all_sessions(self, username: str, limit: int = 30) -> list:
        """Get all sessions for a username"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT s.id, s.created_at, s.expires_at
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE u.username = ?
                ORDER BY s.created_at DESC
                LIMIT ?
            """, (username, limit))

            result = cursor.fetchall()
            conn.close()

            return result

        except Exception as e:
            logger.error("Error getting all sessions: %s", e, exc_info=True)
            return []
