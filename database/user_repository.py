"""User Repository module - Quản lý thông tin và tài khoản người dùng."""

from typing import Optional

from utils.logger import get_logger
from .base_repository import BaseRepository

logger = get_logger(__name__)


class UserRepository(BaseRepository):
    """Repository quản lý dữ liệu người dùng (users, profile display name)."""

    def get_user_by_username(self, username: str):
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

    def create_user(self, username: str, email: Optional[str] = None):
        """Create a new user"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO users (username, password, email)
                VALUES (?, '', ?)
            """, (username, email))

            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return user_id

        except Exception as e:
            logger.error("Error creating user: %s", e, exc_info=True)
            return None

    def get_or_create_user(self, username: str):
        """Get existing user or create new one"""
        user = self.get_user_by_username(username)
        if user:
            return user[0]  # user_id
        else:
            return self.create_user(username)

    def get_display_name(self, user_id: int):
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

    def update_display_name(self, user_id: int, display_name: str) -> bool:
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
