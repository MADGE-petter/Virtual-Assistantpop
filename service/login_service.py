"""Login Service - Xử lý đăng nhập và xác thực người dùng (Model Layer)."""

import hashlib
import json
import os
import sqlite3

from database.db_manager import get_db_manager
from utils.paths import get_database_path, get_writeable_path


class LoginService:
    def __init__(self, db_path=None, users_file=None, settings_file=None):
        if db_path is None:
            self.db_path = get_database_path()
        else:
            self.db_path = db_path
            
        self.users_file = users_file if users_file is not None else get_writeable_path("users.json")
        self.settings_file = settings_file if settings_file is not None else get_writeable_path("user_settings.json")
        self.db_manager = get_db_manager(self.db_path)
        self._ensure_users_table()
        self._ensure_sessions_table()
    
    def _ensure_users_table(self):
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        email TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"[LoginService] Lỗi tạo bảng users: {e}")
    
    def _ensure_sessions_table(self):
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
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
                conn.commit()
        except Exception as e:
            print(f"[LoginService] Lỗi tạo bảng sessions: {e}")
    
    def hash_password(self, password, salt=None):
        import os
        import hashlib
        import binascii
        
        if salt is None:
            salt = os.urandom(16)
        elif isinstance(salt, str):
            salt = binascii.unhexlify(salt)
            
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        return f"{binascii.hexlify(salt).decode('utf-8')}${binascii.hexlify(hash_bytes).decode('utf-8')}"
    
    def get_user_password_hash(self, username):
       
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT password FROM users WHERE username = ?', 
                    (username,)
                )
                result = cursor.fetchone()

            return result[0] if result else None
                
        except Exception as e:
            print(f"[LoginService] Lỗi đọc database: {e}")
            return None
    
    def save_new_user(self, username, password):
       
        try:
            password_hash = self.hash_password(password)
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, password)
                    VALUES (?, ?)
                ''', (username, password_hash))
                conn.commit()
            print(f"[LoginService] User {username} registered successfully!")
            return True
            
        except sqlite3.IntegrityError:
            print(f"[LoginService] User {username} already exists!")
            return False
        except Exception as e:
            print(f"[LoginService] Lỗi đăng ký user: {e}")
            return False
    
    def authenticate_user(self, username, password):
       
        if not username or not password:
            return False
            
        stored_hash = self.get_user_password_hash(username)
        
        if not stored_hash or '$' not in stored_hash:
            return False
            
        salt_hex = stored_hash.split('$')[0]
        input_hash = self.hash_password(password, salt=salt_hex)
        return stored_hash == input_hash
    
    def user_exists(self, username):
     
        return self.get_user_password_hash(username) is not None
    
    def load_settings(self):
       
        default_settings = {
            "auto_start_assistant": True,
            "assistant_delay": 1000,
            "speech_recognition": True,
            "text_to_speech": True,
            "volume": 80,
            "speech_rate": 1.0
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge với default để đảm bảo có tất cả keys
                    return {**default_settings, **loaded}
            return default_settings
        except Exception as e:
            print(f"[LoginService] Lỗi tải settings: {e}")
            return default_settings
    
    def save_settings(self, settings):
      
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[LoginService] Lỗi lưu settings: {e}")
            return False
    
    def load_users_json(self):
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"[LoginService] Lỗi tải users JSON: {e}")
            return {}
    
    def save_users_json(self, users):
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[LoginService] Lỗi lưu users JSON: {e}")
            return False

    def _get_auto_login_file(self):
        import os
        from pathlib import Path
        project_root = Path(__file__).resolve().parent.parent
        db_dir = project_root / "database"
        return db_dir / "auto_login.json"
        
    def save_auto_login(self, username, password=None):
        import json
        file_path = self._get_auto_login_file()
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"username": username, "password": password}, f)
        except Exception as e:
            print(f"[LoginService] Lỗi lưu auto_login: {e}")
            
    def get_auto_login(self):
        import json
        file_path = self._get_auto_login_file()
        try:
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data
        except Exception:
            pass
        return None
        
    def clear_auto_login(self):
        file_path = self._get_auto_login_file()
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass
