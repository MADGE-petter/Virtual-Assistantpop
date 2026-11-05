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
        """Tạo và trả về kết nối SQLite tối ưu hóa hiệu năng cao với WAL mode, mmap, và timeout chống lock."""
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA busy_timeout = 10000;")
        conn.execute("PRAGMA mmap_size = 268435456;")
        conn.execute("PRAGMA cache_size = -32000;")
        return conn
