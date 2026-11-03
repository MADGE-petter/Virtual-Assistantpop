"""Schema definition and initialization for the conversation database."""

import sqlite3
from utils.logger import get_logger

logger = get_logger(__name__)


def init_default_schema(cursor: sqlite3.Cursor):
    """Create the default tables, indexes, triggers and migrations for conversation DB."""
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
