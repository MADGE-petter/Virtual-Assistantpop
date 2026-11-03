"""Database Manager - Utility for database operations to reduce code duplication.

Provides centralized database connection management and common query patterns.
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, Tuple

from utils.paths import get_database_path


class DatabaseManager:
    """Centralized database connection manager.
    
    Reduces code duplication by providing:
    - Context manager for connections
    - Common query patterns
    - Consistent error handling
    """
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            self.db_path = get_database_path()
        else:
            self.db_path = db_path
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections.
        
        Usage:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(...)
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: Tuple = (), fetch_one: bool = False) -> Any:
        """Execute a query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters (tuple)
            fetch_one: If True, fetch one row, else fetch all
            
        Returns:
            Query results or None on error
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchone() if fetch_one else cursor.fetchall()
        except Exception as e:
            print(f"[DatabaseManager] Query error: {e}")
            return None
    
    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """Execute an update/insert/delete query.
        
        Args:
            query: SQL query string
            params: Query parameters (tuple)
            
        Returns:
            Number of rows affected, or -1 on error
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            print(f"[DatabaseManager] Update error: {e}")
            return -1
    
    def get_count(self, table: str, where: str = "", params: Tuple = ()) -> int:
        """Get count of rows in a table.
        
        Args:
            table: Table name
            where: WHERE clause (without 'WHERE')
            params: Parameters for WHERE clause
            
        Returns:
            Count of rows, or 0 on error
        """
        query = f"SELECT COUNT(*) FROM {table}"
        if where:
            query += f" WHERE {where}"
        
        result = self.execute_query(query, params, fetch_one=True)
        return result[0] if result else 0


# Global instance for convenience
def get_db_manager(db_path: Optional[str] = None) -> DatabaseManager:
    """Get database manager instance."""
    return DatabaseManager(db_path)
