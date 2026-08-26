# -*- coding: utf-8 -*-
"""
Database Migration Script

"""

import os
import sqlite3


def migrate_database():
    # Backup database
    if os.path.exists('conversations.db'):
        if os.path.exists('conversations_backup.db'):
            os.remove('conversations_backup.db')
        os.rename('conversations.db', 'conversations_backup.db')
    try:
        conn = sqlite3.connect('conversations.db')
        cursor = conn.cursor()
        
        # 1. Tao bang users (tiếng Việt)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Tao bang sessions (tiếng Việt)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                maPhien TEXT PRIMARY KEY,
                maNguoiDung INTEGER,
                thoiGianBatDau TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                thoiGianKetThuc TIMESTAMP,
                FOREIGN KEY (maNguoiDung) REFERENCES users(maNguoiDung) ON DELETE SET NULL
            )
        """)
        
        # 4. Tao bang conversations (tiếng Việt)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                maCuocTroChuyen INTEGER PRIMARY KEY AUTOINCREMENT,
                maPhien TEXT NOT NULL,
                maNguoiDung INTEGER,
                tinNhanCuaKhach TEXT NOT NULL,
                tinNhanCuaBot TEXT NOT NULL,
                thoiGianTao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                loaiYDo TEXT,
                FOREIGN KEY (maPhien) REFERENCES sessions(maPhien) ON DELETE CASCADE,
                FOREIGN KEY (maNguoiDung) REFERENCES users(maNguoiDung) ON DELETE SET NULL
            )
        """)
        
        # 5. Tao bang user_settings (tiếng Việt)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                maCaiDat INTEGER PRIMARY KEY AUTOINCREMENT,
                maNguoiDung INTEGER NOT NULL,
                khoaCaiDat TEXT NOT NULL,
                giaTriCaiDat TEXT,
                thoiGianTao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (maNguoiDung) REFERENCES users(maNguoiDung) ON DELETE CASCADE,
                UNIQUE(maNguoiDung, khoaCaiDat)
            )
        """)
        
        # 6. Tao bang usage_sessions (thoi gian su dung)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                start_time TEXT,
                end_time TEXT,
                duration_seconds INTEGER,
                tenNguoiDung TEXT
            )
        """)
        
        # 7. Tao bang app_usage (ung dung mo)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                timestamp TEXT,
                app_name TEXT,
                action TEXT,
                tenNguoiDung TEXT
            )
        """)
        
        # 8. Tao bang health_snapshots (suc khoe may)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                timestamp TEXT,
                cpu_percent REAL,
                ram_percent REAL,
                disk_percent REAL,
                temperature REAL,
                tenNguoiDung TEXT
            )
        """)
        
        # 9. Tao indexes cho performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_maNguoiDung ON conversations(maNguoiDung)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_maPhien ON conversations(maPhien)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_thoiGianTao ON conversations(thoiGianTao)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_maNguoiDung ON sessions(maNguoiDung)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_thoiGianBatDau ON sessions(thoiGianBatDau)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_tenNguoiDung ON users(tenNguoiDung)")
        
        # Indexes cho bang analytics
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_sessions_date ON usage_sessions(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_sessions_user ON usage_sessions(tenNguoiDung)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_usage_date ON app_usage(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_usage_user ON app_usage(tenNguoiDung)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_health_snapshots_date ON health_snapshots(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_health_snapshots_user ON health_snapshots(tenNguoiDung)")
        
        # 10. Tao trigger tu dong cap nhat thoiGianCapNhat
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
            AFTER UPDATE ON users
            BEGIN
                UPDATE users SET thoiGianCapNhat = CURRENT_TIMESTAMP WHERE maNguoiDung = NEW.maNguoiDung;
            END
        """)
        
        conn.commit()
        print("Da tao database structure moi!")
        
        conn.close()
        print("Migration hoan tat!")
        
    except Exception as e:
        print(f"Loi migration: {e}")
        if os.path.exists('conversations.db'):
            os.remove('conversations.db')
        if os.path.exists('conversations_backup.db'):
            os.rename('conversations_backup.db', 'conversations.db')
        print("Da rollback database cu")

def import_from_backup(cursor, conn):
    """Import du lieu tu database cu"""
    try:
        backup_conn = sqlite3.connect('conversations_backup.db')
        backup_cursor = backup_conn.cursor()
        
        # Import users
        try:
            backup_cursor.execute("SELECT tenKhachHang FROM users")
            users = backup_cursor.fetchall()
            
            for user in users:
                username = user[0]
                if username and username != 'bạn':
                    cursor.execute("""
                        INSERT OR IGNORE INTO users (username)
                        VALUES (?)
                    """, (username,))
        except Exception as e:
            print(f"Khong the import users tu backup: {e}")
        
        # Import sessions
        backup_cursor.execute("SELECT maPhien, tenKhachHang, thoiGianBatDau, thoiGianKetThuc FROM sessions")
        sessions = backup_cursor.fetchall()
        
        for session in sessions:
            session_id, username, start_time, end_time = session
            
            # Lay user_id
            cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            user_result = cursor.fetchone()
            user_id = user_result[0] if user_result else None
            
            cursor.execute("""
                INSERT OR IGNORE INTO sessions (session_id, user_id, started_at, ended_at)
                VALUES (?, ?, ?, ?)
            """, (session_id, user_id, start_time, end_time))
        
        # Import conversations
        backup_cursor.execute("""
            SELECT maCuocTroChuyen, maPhien, tenKhachHang, tinNhanCuaKhach, tinNhanCuaBot, thoiGianTao 
            FROM conversations
        """)
        conversations = backup_cursor.fetchall()
        
        for conv in conversations:
            conv_id, session_id, username, user_msg, bot_msg, timestamp = conv
            
            # Lay user_id
            cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            user_result = cursor.fetchone()
            user_id = user_result[0] if user_result else None
            
            cursor.execute("""
                INSERT OR IGNORE INTO conversations 
                (conversation_id, session_id, user_id, user_message, bot_response, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (conv_id, session_id, user_id, user_msg, bot_msg, timestamp))
        
        backup_conn.close()
        print("Da import du lieu thanh cong!")
        
    except Exception as e:
        print(f"Loi import: {e}")

if __name__ == "__main__":
    migrate_database()
