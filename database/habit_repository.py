"""
Habit Repository - Data Access Layer

Chịu trách nhiệm truy xuất database, không chứa business logic
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from database.base_repository import BaseRepository


class HabitRepository(BaseRepository):
    """Repository for habit data access - SQL only, no business logic"""
    
    def __init__(self, db_path: str):
        super().__init__(db_path)
    
    # ========== App Usage Logs ==========
    
    def insert_app_usage_log(self, user_id: int, app_name: str, timestamp: datetime) -> int:
        """Insert new app usage log"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO app_usage_logs (maNguoiDung, tenUngDung, thoiGianMo)
                    VALUES (?, ?, ?)
                """, (user_id, app_name, timestamp))
                conn.commit()
                return cursor.lastrowid
        except Exception:
            return 0
    
    def get_recent_app_usage(self, user_id: int, days: int = 7) -> List[Tuple]:
        """Get app usage in last N days"""
        try:
            # Validate days parameter to prevent SQL injection
            days = int(days) if days is not None else 7
            if days < 1 or days > 365:
                days = 7  # Default to 7 if invalid

            modifier = f'-{days} days'
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT tenUngDung, COUNT(*) as count, MAX(thoiGianMo) as last_opened
                    FROM app_usage_logs
                    WHERE maNguoiDung = ? AND DATE(thoiGianMo) >= DATE('now', ?)
                    GROUP BY tenUngDung
                    ORDER BY count DESC, last_opened DESC
                """, (user_id, modifier))
                return cursor.fetchall()
        except Exception:
            return []

    def get_today_app_count(self, user_id: int, app_name: str) -> int:
        """Đếm số lần mở 1 app trong ngày hôm nay."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                today_str = datetime.now().strftime('%Y-%m-%d')
                cursor.execute("""
                    SELECT COUNT(*) FROM app_usage_logs
                    WHERE maNguoiDung = ? AND tenUngDung = ?
                      AND (ngay = ? OR DATE(thoiGianMo) = ?)
                """, (user_id, app_name, today_str, today_str))
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception:
            return 0

    def get_recent_app_usage_by_day(self, user_id: int, days: int = 7) -> List[Tuple]:
        """Get app usage per day in the last N days."""
        try:
            days = int(days) if days is not None else 7
            if days < 1 or days > 365:
                days = 7

            modifier = f'-{days} days'
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT tenUngDung, DATE(thoiGianMo) as day, COUNT(*) as count,
                           MAX(thoiGianMo) as last_opened
                    FROM app_usage_logs
                    WHERE maNguoiDung = ? AND DATE(thoiGianMo) >= DATE('now', ?)
                    GROUP BY tenUngDung, DATE(thoiGianMo)
                """, (user_id, modifier))
                return cursor.fetchall()
        except Exception:
            return []

    def find_habit(self, user_id: int, habit_type: str, target: str, 
                   time_bucket: int, day_type: str) -> Optional[Tuple]:
        """Find existing habit by composite key"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, tanSuat, doTinCay, lanQuanSatCuoi
                    FROM user_habits
                    WHERE maNguoiDung = ? AND loaiThoiQuen = ? AND tenMucTieu = ?
                      AND gioTrongNgay = ? AND ngayTrongTuan = ?
                """, (user_id, habit_type, target, time_bucket, day_type))
                return cursor.fetchone()
        except Exception:
            return None
    
    def update_habit(self, habit_id: int, frequency: int, confidence: float, 
                     last_observed: datetime) -> None:
        """Update existing habit"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_habits
                    SET tanSuat = ?, doTinCay = ?, lanQuanSatCuoi = ?
                    WHERE id = ?
                """, (frequency, confidence, last_observed, habit_id))
                conn.commit()
        except Exception:
            pass
    
    def insert_habit(self, user_id: int, habit_type: str, target: str,
                     time_bucket: int, day_type: str, frequency: int = 1,
                     confidence: float = 0.1) -> int:
        """Insert new habit"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO user_habits
                    (maNguoiDung, loaiThoiQuen, tenMucTieu, gioTrongNgay, 
                     ngayTrongTuan, tanSuat, doTinCay, lanQuanSatCuoi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, habit_type, target, time_bucket, day_type, 
                      frequency, confidence, datetime.now()))
                conn.commit()
                return cursor.lastrowid
        except Exception:
            return 0
    
    def get_user_habits_raw(self, user_id: int, min_confidence: float = 0.0) -> List[Tuple]:
        """Get all habits for user"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT tenMucTieu, loaiThoiQuen, tanSuat, doTinCay, lanQuanSatCuoi
                    FROM user_habits
                    WHERE maNguoiDung = ? AND doTinCay >= ?
                    ORDER BY doTinCay DESC
                """, (user_id, min_confidence))
                return cursor.fetchall()
        except Exception:
            return []
    
    # ========== App Sequences ==========
    
    def find_sequence(self, user_id: int, app_before: str, app_after: str) -> Optional[Tuple]:
        """Find existing sequence"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, soLanGap, doTinCay, thoiGianTrungBinh, lanCapNhatCuoi
                    FROM app_sequences
                    WHERE maNguoiDung = ? AND appTruoc = ? AND appSau = ?
                """, (user_id, app_before, app_after))
                return cursor.fetchone()
        except Exception:
            return None
    
    def update_sequence(self, seq_id: int, frequency: int, confidence: float,
                       avg_time_between: int, last_updated: datetime) -> None:
        """Update existing sequence"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE app_sequences
                    SET soLanGap = ?, doTinCay = ?, thoiGianTrungBinh = ?, lanCapNhatCuoi = ?
                    WHERE id = ?
                """, (frequency, confidence, avg_time_between, last_updated, seq_id))
                conn.commit()
        except Exception:
            pass
    
    def insert_sequence(self, user_id: int, app_before: str, app_after: str,
                       time_between: int) -> int:
        """Insert new sequence"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO app_sequences
                    (maNguoiDung, appTruoc, appSau, thoiGianTrungBinh, soLanGap, doTinCay, lanCapNhatCuoi)
                    VALUES (?, ?, ?, ?, 1, 0.1, ?)
                """, (user_id, app_before, app_after, time_between, datetime.now()))
                conn.commit()
                return cursor.lastrowid
        except Exception:
            return 0
    
    def get_sequences_from_app(self, user_id: int, app_name: str, min_confidence: float) -> List[Tuple]:
        """Get sequences starting from specific app"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT appSau, thoiGianTrungBinh, soLanGap, doTinCay
                    FROM app_sequences
                    WHERE maNguoiDung = ? AND appTruoc = ? AND doTinCay >= ?
                    ORDER BY soLanGap DESC
                """, (user_id, app_name, min_confidence))
                return cursor.fetchall()
        except Exception:
            return []
    
    # ========== Workflows ==========
    
    def find_workflow(self, user_id: int, app_chain: str) -> Optional[Tuple]:
        """Find existing workflow by app chain"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, soLanThucHien, doTinCay, lanThucHienCuoi
                    FROM workflows
                    WHERE maNguoiDung = ? AND appChain = ?
                """, (user_id, app_chain))
                return cursor.fetchone()
        except Exception:
            return None
    
    def update_workflow(self, wf_id: int, frequency: int, confidence: float, last_executed: datetime) -> None:
        """Update existing workflow"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE workflows
                    SET soLanThucHien = ?, doTinCay = ?, lanThucHienCuoi = ?
                    WHERE id = ?
                """, (frequency, confidence, last_executed, wf_id))
                conn.commit()
        except Exception:
            pass
    
    def insert_workflow(self, user_id: int, name: str, app_chain: str) -> int:
        """Insert new workflow"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO workflows
                    (maNguoiDung, tenWorkflow, appChain, soLanThucHien, doTinCay, lanThucHienCuoi)
                    VALUES (?, ?, ?, 1, 0.1, ?)
                """, (user_id, name, app_chain, datetime.now()))
                conn.commit()
                return cursor.lastrowid
        except Exception:
            return 0
    
    def get_workflows(self, user_id: int, min_confidence: float, limit: int) -> List[Tuple]:
        """Get workflows for user"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT tenWorkflow, appChain, soLanThucHien, doTinCay
                    FROM workflows
                    WHERE maNguoiDung = ? AND doTinCay >= ?
                    ORDER BY soLanThucHien DESC
                    LIMIT ?
                """, (user_id, min_confidence, limit))
                return cursor.fetchall()
        except Exception:
            return []
    
    # ========== Session Context ==========
    
    def get_session_context(self, user_id: int) -> Optional[Tuple]:
        """Get session context for user"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT app_cuoi_cung, thoiGianMoCuoi, chuoi_app_hien_tai
                    FROM session_context
                    WHERE maNguoiDung = ?
                """, (user_id,))
                return cursor.fetchone()
        except Exception:
            return None
    
    def update_session_context(self, user_id: int, app_chain: str, last_app: str,
                            last_time: datetime, session_start: datetime) -> None:
        """Update or create session context"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO session_context
                    (maNguoiDung, app_cuoi_cung, thoiGianMoCuoi, chuoi_app_hien_tai, thoiGianBatDauSession)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, app_chain, last_app, last_time, session_start))
                conn.commit()
        except Exception:
            pass
    
    def reset_session_context(self, user_id: int) -> None:
        """Delete session context"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM session_context
                    WHERE maNguoiDung = ?
                """, (user_id,))
                conn.commit()
        except Exception:
            pass
    
    # ========== Table Stats ==========
    
    def get_table_counts(self) -> Dict:
        """Get counts of all tables"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Count rows in app_usage_logs
                cursor.execute("SELECT COUNT(*) FROM app_usage_logs")
                stats['app_usage_logs_count'] = cursor.fetchone()[0]
                
                # Count rows in user_habits
                cursor.execute("SELECT COUNT(*) FROM user_habits")
                stats['user_habits_count'] = cursor.fetchone()[0]
                
                # Count unique users
                cursor.execute("SELECT COUNT(DISTINCT maNguoiDung) FROM app_usage_logs")
                stats['unique_users_logs'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT maNguoiDung) FROM user_habits")
                stats['unique_users_habits'] = cursor.fetchone()[0]
                
                # Count unique apps
                cursor.execute("SELECT COUNT(DISTINCT tenUngDung) FROM app_usage_logs")
                stats['unique_apps'] = cursor.fetchone()[0]
                
                # Date range
                cursor.execute("SELECT MIN(thoiGianMo), MAX(thoiGianMo) FROM app_usage_logs")
                date_range = cursor.fetchone()
                stats['oldest_log'] = date_range[0] if date_range else None
                stats['newest_log'] = date_range[1] if date_range else None
                
                return stats
        except Exception:
            return {}
