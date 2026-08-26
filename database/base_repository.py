"""
Base Repository
Cung cấp kết nối SQLite chung cho các repository.
"""
import sqlite3
from typing import Optional


class BaseRepository:
    """Repository cơ sở cho các lớp truy xuất dữ liệu SQLite."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Tạo và trả về kết nối SQLite với row_factory được cấu hình."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
