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

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
            AFTER UPDATE ON users
            BEGIN
                UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        """)
    
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
