"""
Alert Repository - Data Access Layer
Chịu trách nhiệm truy xuất database, không chứa business logic
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from database.base_repository import BaseRepository


class AlertRepository(BaseRepository):
    """Repository for alert data access - SQL only, no business logic"""
    
    def __init__(self, db_path: str):
        super().__init__(db_path)
    
    def _init_tables(self):
        """Initialize alert tables"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alert_logs (
                        id TEXT PRIMARY KEY,
                        metric TEXT NOT NULL,
                        level TEXT NOT NULL,
                        value REAL NOT NULL,
                        message TEXT NOT NULL,
                        timestamp REAL NOT NULL,
                        acknowledged BOOLEAN DEFAULT FALSE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"[AlertRepository] Error initializing tables: {e}")
    
    def save_alert(self, alert_id: str, metric: str, level: str, value: float, 
                   message: str, timestamp: float, acknowledged: bool = False) -> bool:
        """Save alert to database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO alert_logs
                    (id, metric, level, value, message, timestamp, acknowledged)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (alert_id, metric, level, value, message, timestamp, acknowledged))
                conn.commit()
                return True
        except Exception as e:
            print(f"[AlertRepository] Error saving alert: {e}")
            return False
    
    def load_alerts(self, limit: int = 100) -> List[Dict]:
        """Load alerts from database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, metric, level, value, message, timestamp, acknowledged
                    FROM alert_logs
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
                
                alerts = []
                for row in cursor.fetchall():
                    alerts.append({
                        'id': row['id'],
                        'metric': row['metric'],
                        'level': row['level'],
                        'value': row['value'],
                        'message': row['message'],
                        'timestamp': row['timestamp'],
                        'acknowledged': bool(row['acknowledged'])
                    })
                return alerts
        except Exception as e:
            print(f"[AlertRepository] Error loading alerts: {e}")
            return []
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Update alert acknowledgment status"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE alert_logs
                    SET acknowledged = 1
                    WHERE id = ?
                """, (alert_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"[AlertRepository] Error acknowledging alert: {e}")
            return False
    
    def delete_all_alerts(self) -> bool:
        """Delete all alerts and vacuum"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM alert_logs")
                cursor.execute("VACUUM")
                conn.commit()
                return True
        except Exception as e:
            print(f"[AlertRepository] Error deleting alerts: {e}")
            return False
    
    def cleanup_old_alerts(self, days_to_keep: int = 30, max_rows: int = 5000) -> Dict:
        """Clean old alerts by time and row count"""
        import time
        result = {'time_deleted': 0, 'row_deleted': 0}
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get current row count
                cursor.execute("SELECT COUNT(*) FROM alert_logs")
                total_rows = cursor.fetchone()[0]
                
                # Cleanup by time
                cutoff_time = time.time() - (days_to_keep * 24 * 3600)
                cursor.execute("DELETE FROM alert_logs WHERE timestamp < ?", (cutoff_time,))
                result['time_deleted'] = cursor.rowcount
                
                # Cleanup by row count
                if total_rows > max_rows:
                    cursor.execute("""
                        SELECT timestamp FROM alert_logs 
                        ORDER BY timestamp DESC 
                        LIMIT 1 OFFSET ?
                    """, (max_rows,))
                    row = cursor.fetchone()
                    
                    if row:
                        cursor.execute("DELETE FROM alert_logs WHERE timestamp < ?", (row[0],))
                        result['row_deleted'] = cursor.rowcount
                
                # Vacuum if deleted anything
                if result['time_deleted'] > 0 or result['row_deleted'] > 0:
                    cursor.execute("VACUUM")
                
                conn.commit()
                return result
        except Exception as e:
            print(f"[AlertRepository] Error cleaning up alerts: {e}")
            return result
    
    def get_alert_count(self) -> int:
        """Get total alert count"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM alert_logs")
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"[AlertRepository] Error getting count: {e}")
            return 0
