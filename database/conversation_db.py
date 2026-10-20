import os
import sqlite3
from datetime import datetime

from utils.logger import get_logger
from utils.paths import get_database_path

from .base_repository import BaseRepository

logger = get_logger(__name__)

class ConversationDB(BaseRepository):
    """Database operations for conversations"""

    def __init__(self, db_path: str = None):
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
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            self._create_default_schema(cursor)
            conn.commit()
            logger.info("Checked conversation DB schema for %s", self.db_path)
            
            conn.close()
        except Exception as e:
            logger.error("Database initialization error: %s", e, exc_info=True)
            raise

    def _create_default_schema(self, cursor):
        """Create the default schema required for the conversation database."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                is_active BOOLEAN DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                user_id INTEGER,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                intent_type TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                setting_key TEXT NOT NULL,
                setting_value TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, setting_key)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                start_time TEXT,
                end_time TEXT,
                duration_seconds INTEGER,
                username TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                timestamp TEXT,
                app_name TEXT,
                action TEXT,
                username TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                timestamp TEXT,
                cpu_percent REAL,
                ram_percent REAL,
                disk_percent REAL,
                temperature REAL,
                username TEXT
            )
        """)

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_usage_sessions_date ON usage_sessions(date)",
            "CREATE INDEX IF NOT EXISTS idx_usage_sessions_user ON usage_sessions(username)",
            "CREATE INDEX IF NOT EXISTS idx_app_usage_date ON app_usage(date)",
            "CREATE INDEX IF NOT EXISTS idx_app_usage_user ON app_usage(username)",
            "CREATE INDEX IF NOT EXISTS idx_health_snapshots_date ON health_snapshots(date)",
        ]
        for idx_sql in indexes:
            try:
                cursor.execute(idx_sql)
            except Exception:
                pass
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_health_snapshots_user ON health_snapshots(username)")

        # Check and add title column to sessions if not present
        try:
            cursor.execute("PRAGMA table_info(sessions)")
            cols = [col[1] for col in cursor.fetchall()]
            if 'title' not in cols:
                cursor.execute("ALTER TABLE sessions ADD COLUMN title TEXT DEFAULT 'Cuộc trò chuyện mới'")
        except Exception as e:
            logger.warning("Could not add title column to sessions: %s", e)

        # Create chat_messages table for storing individual user and bot messages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                sender TEXT NOT NULL,
                text TEXT NOT NULL,
                timestamp TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'sent',
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at)")

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
            AFTER UPDATE ON users
            BEGIN
                UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        """)

    def create_chat_session(self, user_id: int, title: str = "Cuộc trò chuyện mới") -> int:
        """Create a new chat session with a title and return its session ID."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            import uuid
            session_token = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO sessions (user_id, session_token, title, created_at, is_active)
                VALUES (?, ?, ?, ?, 1)
            """, (user_id, session_token, title, datetime.now()))
            session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return session_id
        except Exception as e:
            logger.error("Error creating chat session: %s", e, exc_info=True)
            return 1

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

    def add_chat_message(self, session_id: int, sender: str, text: str, timestamp: str = None) -> int:
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

    def get_user_chat_sessions(self, username: str, limit: int = 50) -> list:
        """Get all sessions for a user with title and created_at that have messages."""
        try:
            user_id = self.get_or_create_user(username)
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

    def cleanup_empty_sessions(self, user_id: int = None):
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
    
    def save_conversation(self, user_id, session_id, user_message, bot_response, intent_type=None):
        """Save a conversation to database"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Debug: Log what we're saving
            logger.debug("Saving conversation: user=%s (type=%s), session=%s (type=%s)", user_id, type(user_id).__name__, session_id, type(session_id).__name__)
            
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
    
    def get_conversations(self, user_id=None, limit=50):
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
    
    def get_user_by_username(self, username):
        """Get user by username"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            conn.close()
            
            return result
            
        except Exception as e:
            logger.error("Error getting user: %s", e, exc_info=True)
            return None
    
    def create_user(self, username, email=None):
        """Create a new user"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO users (username, password)
                VALUES (?, '')
            """, (username,))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return user_id
            
        except Exception as e:
            logger.error("Error creating user: %s", e, exc_info=True)
            return None
    
    def get_or_create_user(self, username):
        """Get existing user or create new one"""
        user = self.get_user_by_username(username)
        if user:
            return user[0]  # user_id
        else:
            return self.create_user(username)
    
    def start_session(self, user_id: int = None) -> int:
        """Bắt đầu session mới và trả về session ID (integer)."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Nếu user_id là string, convert sang int nếu có thể
            if isinstance(user_id, str) and user_id.isdigit():
                user_id = int(user_id)
            elif user_id is None or (isinstance(user_id, str) and not user_id.isdigit()):
                # Guest user - lấy user đầu tiên hoặc tạo guest
                user_id = 1  # Default to first user
            
            import uuid
            session_token = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO sessions (user_id, session_token, created_at)
                VALUES (?, ?, ?)
            """, (user_id, session_token, datetime.now()))
            
            session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return session_id
            
        except Exception as e:
            logger.error("Error starting session: %s", e, exc_info=True)
            return 1  # Return default session ID on error
    
    def end_session(self, session_id):
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
    
    def get_user_sessions(self, user_id, limit=20):
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
    
    def get_session_conversations(self, session_id, username=None):
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
    
    def get_all_sessions(self, username, limit=30):
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
    
    def get_statistics(self, user_id):
        """Get statistics for a user"""
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
    
    def get_daily_statistics(self, user_id, limit=30):
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
    
    def delete_old_conversations(self, days=30):
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
    
    def get_display_name(self, user_id):
        """Lấy họ tên (tên hiển thị) của user"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()

            return result[0] if result and result[0] else None
        except Exception as e:
            logger.error("Error getting display name: %s", e, exc_info=True)
            return None
    
    def update_display_name(self, user_id, display_name):
        """Cập nhật họ tên (tên hiển thị) cho user"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE users 
                SET username = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (display_name, user_id))

            conn.commit()
            conn.close()
            logger.info("Updated display name for user %s to: %s", user_id, display_name)
            return True
        except Exception as e:
            logger.error("Error updating display name: %s", e, exc_info=True)
            return False
