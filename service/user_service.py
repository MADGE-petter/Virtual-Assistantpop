"""User Service - Xử lý user name operations (merged with UserController)."""

import os
import sys


class UserService:  
    def __init__(self, sql_service):
        self.sql_service = sql_service
        self.login_name = "bạn"
        self.display_name = None
        self._current_session_id = None
    
    def set_login_username(self, username):
        """Thiết lập username đăng nhập (from UserController)."""
        self.login_name = username
        if username:
            self.display_name = self.get_display_name_by_login(username)
            print(f"[UserService] Loaded user: login={username}, display={self.display_name}")
    
    def get_login_name(self):
        """Lấy tên đăng nhập (from UserController)."""
        return self.login_name
    
    def load_user_name(self):
       
        try:
            # Thử load tên gần nhất từ database
            recent_user = self.sql_service.get_most_recent_user()
            if recent_user and recent_user != "bạn":
                self.login_name = recent_user
                self.display_name = self.get_display_name_by_login(self.login_name)
                print(f"[DB] Loaded user name: {self.login_name} - {self.display_name}")
            else:
                self.login_name = "bạn"
                self.display_name = None
                print("[DB] No user name found, using default 'bạn'")
        except Exception as e:
            self.login_name = "bạn"
            self.display_name = None
            print(f"[DB] Error loading user name: {e}")
        
        return self.login_name
    
    def get_display_name_by_login(self, login_name):
        
        try:
            conn = self.sql_service.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT username 
                FROM users 
                WHERE username = ?
            """, (login_name,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0] if result[0] else None
            return None
        except Exception as e:
            print(f"Error getting display name: {e}")
            return None
    
    def update_display_name_by_login(self, login_name, display_name):
        
        try:
            conn = self.sql_service.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET username = ?
                WHERE username = ?
            """, (display_name, login_name))
            
            conn.commit()
            conn.close()
            print(f"Updated display name for {login_name} to: {display_name}")
            return True
        except Exception as e:
            print(f"Error updating display name: {e}")
            return False
    
    def update_user_name(self, new_name, current_session=None):
        
        if not new_name or new_name == "bạn" or new_name == "...":
            return None, None
        
        old_name = self.display_name if self.display_name else "bạn"
        
        # Cập nhật display name trong database (cột hoTen)
        if self.login_name and self.login_name != "bạn":
            success = self.update_display_name_by_login(self.login_name, new_name)
            if success:
                self.display_name = new_name
                print(f"[UserService] Updated display name: {old_name} -> {new_name}")
                return old_name, new_name       
        return old_name, None   
        
    def get_user_name(self):       
        return self.display_name if self.display_name else "bạn"
    
    def get_display_name(self):
        """Lấy tên hiển thị (from UserController)."""
        return self.get_user_name()
    
    def is_name_known(self):
        return self.display_name is not None and self.display_name.strip()
