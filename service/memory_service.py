"""Memory Service - Quản lý lưu trữ hội thoại."""
from typing import Optional

from controller.interfaces import ISqlService


class MemoryService:
    def __init__(self, sql_service: ISqlService):
        self.sql = sql_service
    
    def save_exchange(self, user_name: str, user_msg: str, 
                      bot_response: str, session_id: Optional[int] = None) -> None:
        """Lưu 1 lượt hội thoại (user + bot)."""
        try:
            self.sql.save_conversation(user_name, user_msg, bot_response, session_id)
            print(f"[MemoryService] Saved: '{user_msg[:30]}...' -> '{bot_response[:30]}...'")
        except Exception as e:
            print(f"[MemoryService] Error saving: {e}")
    
    def get_session_history(self, session_id: int) -> list:
        """Lấy history của 1 session."""
        return self.sql.get_session_conversations(session_id)
