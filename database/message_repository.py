"""Message Repository module - Quản lý tin nhắn chat, lịch sử hội thoại và thống kê."""

from datetime import datetime
from typing import List, Optional, Tuple

from utils.logger import get_logger
from .base_repository import BaseRepository

logger = get_logger(__name__)


class MessageRepository(BaseRepository):
    """Repository quản lý tin nhắn (chat_messages), hội thoại (conversations) và thống kê."""

    def add_chat_message(self, session_id: int, sender: str, text: str, timestamp: Optional[str] = None) -> int:
        """Add a single message (user or bot) to chat_messages."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            if not timestamp:
                timestamp = datetime.now().strftime("%I:%M %p")
            cursor.execute("""
                INSERT INTO chat_messages (session_id, sender, text, timestamp, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, sender, text, timestamp, datetime.now()))
            msg_id = cursor.lastrowid
            conn.commit()
            conn.close()
            if msg_id is None:
                return -1
            return msg_id
        except Exception as e:
            logger.error("Error adding chat message: %s", e, exc_info=True)
            return -1

    def get_session_chat_messages(self, session_id: int) -> list:
        """Fetch all messages for a session in chronological order."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, sender, text, timestamp, created_at
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY id ASC
            """, (session_id,))
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                # Check legacy conversations table as fallback
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_message, bot_response, created_at
                    FROM conversations
                    WHERE session_id = ?
                    ORDER BY id ASC
                """, (session_id,))
                legacy = cursor.fetchall()
                conn.close()
                converted = []
                for u_msg, b_msg, c_at in legacy:
                    time_str = str(c_at)[11:16] if c_at and len(str(c_at)) >= 16 else ""
                    if u_msg:
                        converted.append((0, 'user', u_msg, time_str, c_at))
                    if b_msg:
                        converted.append((0, 'bot', b_msg, time_str, c_at))
                return converted
            return rows
        except Exception as e:
            logger.error("Error getting session chat messages: %s", e, exc_info=True)
            return []

    def save_conversation(self, user_id, session_id, user_message: str, bot_response: str, intent_type: Optional[str] = None):
        """Save a conversation to database"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            logger.debug(
                "Saving conversation: user=%s (type=%s), session=%s (type=%s)",
                user_id, type(user_id).__name__, session_id, type(session_id).__name__
            )

            cursor.execute("""
                INSERT INTO conversations (user_id, session_id, user_message, bot_response, intent_type)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, session_id, user_message, bot_response, intent_type))

            conn.commit()
            last_id = cursor.lastrowid
            conn.close()
            logger.info("Saved conversation, rowid=%s", last_id)

        except Exception as e:
            logger.error("Error saving conversation: %s", e, exc_info=True)

    def get_conversations(self, user_id: Optional[int] = None, limit: int = 50) -> list:
        """Get conversations from database"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if user_id:
                cursor.execute("""
                    SELECT c.*, u.username 
                    FROM conversations c
                    JOIN users u ON c.user_id = u.id
                    WHERE c.user_id = ?
                    ORDER BY c.created_at DESC
                    LIMIT ?
                """, (user_id, limit))
            else:
                cursor.execute("""
                    SELECT c.*, u.username 
                    FROM conversations c
                    JOIN users u ON c.user_id = u.id
                    ORDER BY c.created_at DESC
                    LIMIT ?
                """, (limit,))

            result = cursor.fetchall()
            conn.close()

            return result

        except Exception as e:
            logger.error("Error getting conversations: %s", e, exc_info=True)
            return []

    def get_session_conversations(self, session_id: int, username: Optional[str] = None) -> list:
        """Get conversations for a session"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if username:
                cursor.execute("""
                    SELECT c.user_message, c.bot_response, c.created_at
                    FROM conversations c
                    JOIN sessions s ON c.session_id = s.id
                    JOIN users u ON s.user_id = u.id
                    WHERE c.session_id = ? AND u.username = ?
                    ORDER BY c.created_at ASC
                """, (session_id, username))
            else:
                cursor.execute("""
                    SELECT user_message, bot_response, created_at
                    FROM conversations 
                    WHERE session_id = ?
                    ORDER BY created_at ASC
                """, (session_id,))

            result = cursor.fetchall()
            conn.close()

            return result

        except Exception as e:
            logger.error("Error getting session conversations: %s", e, exc_info=True)
            return []

    def delete_old_conversations(self, days: int = 30):
        """Delete conversations older than specified days"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM conversations 
                WHERE created_at < datetime('now', '-{} days')
            """.format(days))

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            logger.info("Deleted %s old conversations", deleted_count)

        except Exception as e:
            logger.error("Error deleting old conversations: %s", e, exc_info=True)

    def clear_history(self, username: Optional[str] = None) -> bool:
        """Clear conversation history (messages, conversations, sessions).
        
        If username is provided, clears only history for that user.
        If username is None, clears all conversation history.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if username:
                cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username.lower(),))
                user_row = cursor.fetchone()
                if not user_row:
                    conn.close()
                    logger.info("User %s not found when clearing history", username)
                    return True
                user_id = user_row[0]

                cursor.execute("""
                    DELETE FROM chat_messages 
                    WHERE session_id IN (SELECT id FROM sessions WHERE user_id = ?)
                """, (user_id,))
                cursor.execute("""
                    DELETE FROM conversations 
                    WHERE user_id = ? OR session_id IN (SELECT id FROM sessions WHERE user_id = ?)
                """, (user_id, user_id))
                cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            else:
                cursor.execute("DELETE FROM chat_messages")
                cursor.execute("DELETE FROM conversations")
                cursor.execute("DELETE FROM sessions")

            conn.commit()
            conn.close()
            logger.info("Cleared conversation history for user: %s", username if username else "all users")
            return True
        except Exception as e:
            logger.error("Error clearing conversation history: %s", e, exc_info=True)
            return False

    def get_statistics(self, user_id: int) -> Tuple[int, int, int]:
        """Get statistics for a user (total_conversations, total_days, total_sessions)"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) as total_conversations,
                       COUNT(DISTINCT DATE(created_at)) as total_days,
                       COUNT(DISTINCT session_id) as total_sessions
                FROM conversations 
                WHERE user_id = ?
            """, (user_id,))

            result = cursor.fetchone()
            conn.close()

            return result if result else (0, 0, 0)

        except Exception as e:
            logger.error("Error getting statistics: %s", e, exc_info=True)
            return (0, 0, 0)

    def get_daily_statistics(self, user_id: int, limit: int = 30) -> list:
        """Get daily statistics for a user"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DATE(created_at) as date,
                       COUNT(*) as conversation_count,
                       COUNT(DISTINCT session_id) as session_count
                FROM conversations 
                WHERE user_id = ?
                GROUP BY DATE(created_at)
                ORDER BY date DESC
                LIMIT ?
            """, (user_id, limit))

            result = cursor.fetchall()
            conn.close()

            return result

        except Exception as e:
            logger.error("Error getting daily statistics: %s", e, exc_info=True)
            return []
