"""Usage Tracker - Theo dõi thời gian sử dụng và ứng dụng"""
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from database.db_manager import get_db_manager
from utils.logger import get_logger
from utils.paths import get_database_path

logger = get_logger(__name__)


class UsageTracker:
    """Theo dõi thời gian sử dụng và ứng dụng được mở"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path if db_path is not None else get_database_path()
        self.db_manager = get_db_manager(self.db_path)
        self.session_start: Optional[datetime] = None
        self.current_session_id: Optional[int] = None
        self._init_db()

    def _init_db(self):
        """Khởi tạo các bảng dùng trong usage tracking nếu chưa tồn tại."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usage_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    duration_seconds INTEGER,
                    tenNguoiDung TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    timestamp TEXT,
                    app_name TEXT,
                    action TEXT,
                    tenNguoiDung TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    maNguoiDung INTEGER DEFAULT 1,
                    tenUngDung TEXT,
                    thoiGianMo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ngay TEXT
                )
            ''')

            cursor.execute('''
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
            ''')

            conn.commit()

    def start_session(self, user_name: str = "user"):
        """Bắt đầu một phiên sử dụng mới và ghi vào `usage_sessions`."""
        self.session_start = datetime.now()
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO usage_sessions (date, start_time, tenNguoiDung)
                VALUES (?, ?, ?)
            ''', (
                self.session_start.strftime('%Y-%m-%d'),
                self.session_start.strftime('%H:%M:%S'),
                user_name,
            ))
            self.current_session_id = cursor.lastrowid
            conn.commit()

    def end_session(self, user_name: str = "user"):
        """Kết thúc phiên hiện tại và cập nhật `usage_sessions`."""
        if self.session_start is None or self.current_session_id is None:
            return

        end_time = datetime.now()
        duration = int((end_time - self.session_start).total_seconds())

        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE usage_sessions
                SET end_time = ?, duration_seconds = ?
                WHERE id = ?
            ''', (end_time.strftime('%H:%M:%S'), duration, self.current_session_id))
            conn.commit()

        self.session_start = None
        self.current_session_id = None

    def log_app_opened(self, app_name: str, user_name: str = "user"):
        now = datetime.now()
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO app_usage (date, timestamp, app_name, action, tenNguoiDung)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                now.strftime('%Y-%m-%d'),
                now.strftime('%H:%M:%S'),
                app_name,
                'opened',
                user_name,
            ))
            conn.commit()

    def log_health_snapshot(self, cpu: float, ram: float, disk: float, temp: Optional[float], user_name: str = "user"):
        now = datetime.now()
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO health_snapshots (date, timestamp, cpu_percent, ram_percent, disk_percent, temperature, tenNguoiDung)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                now.strftime('%Y-%m-%d'),
                now.strftime('%H:%M:%S'),
                cpu,
                ram,
                disk,
                temp,
                user_name,
            ))
            conn.commit()

    def get_daily_usage(self, days: int = 7, user_name: str = "user") -> List[Dict]:
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        query = '''
                SELECT date, SUM(duration_seconds) as total_seconds, COUNT(*) as session_count
                FROM usage_sessions
                WHERE date >= ?
            '''
        params = [start_date]

        if user_name:
            query += ' AND tenNguoiDung = ?'
            params.append(user_name)

        query += ' GROUP BY date ORDER BY date DESC'

        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

        return [
            {'date': row[0], 'hours': round(row[1] / 3600, 2) if row[1] else 0, 'sessions': row[2]}
            for row in rows
        ]

    def get_top_apps(self, days: int = 7, user_name: str = "user", limit: int = 10) -> List[Tuple[str, int, str]]:
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        query = '''
                SELECT app_name,
                       COUNT(*) as open_count,
                       MAX(date || ' ' || timestamp) as last_opened
                FROM app_usage
                WHERE date >= ?
            '''
        params = [start_date]

        if user_name:
            query += ' AND tenNguoiDung = ?'
            params.append(user_name)

        query += '''
                GROUP BY app_name
                ORDER BY open_count DESC
                LIMIT ?
            '''
        params.append(limit)

        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
        return rows

    def get_top_apps_duration(self, days: int = 7, user_name: str = "user", limit: int = 10) -> List[Dict[str, object]]:
        """Estimate app usage duration from open events."""
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        query = '''
                SELECT date, timestamp, app_name
                FROM app_usage
                WHERE date >= ?
            '''
        params = [start_date]

        if user_name:
            query += ' AND tenNguoiDung = ?'
            params.append(user_name)

        query += ' ORDER BY date ASC, timestamp ASC'

        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

        events = []
        for row in rows:
            try:
                dt = datetime.strptime(f"{row['date']} {row['timestamp']}", '%Y-%m-%d %H:%M:%S')
                events.append({'dt': dt, 'app_name': row['app_name']})
            except Exception:
                continue

        app_totals = {}
        for index, event in enumerate(events):
            current_app = event['app_name']
            next_dt = None
            if index + 1 < len(events):
                next_dt = events[index + 1]['dt']

            if next_dt:
                duration = int((next_dt - event['dt']).total_seconds() / 60)
                if duration <= 0:
                    duration = 1
                elif duration > 120:
                    duration = 15
            else:
                duration = 10

            if current_app not in app_totals:
                app_totals[current_app] = {
                    'app_name': current_app,
                    'open_count': 0,
                    'estimated_minutes': 0,
                    'last_opened': event['dt'].strftime('%Y-%m-%d %H:%M:%S')
                }

            app_totals[current_app]['open_count'] += 1
            app_totals[current_app]['estimated_minutes'] += duration
            app_totals[current_app]['last_opened'] = max(
                app_totals[current_app]['last_opened'],
                event['dt'].strftime('%Y-%m-%d %H:%M:%S')
            )

        sorted_apps = sorted(
            app_totals.values(),
            key=lambda item: item['open_count'],
            reverse=True
        )
        return sorted_apps[:limit]

    def get_health_trends(self, days: int = 7, user_name: str = "user") -> Dict:
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        query = '''
                SELECT AVG(cpu_percent), AVG(ram_percent), AVG(disk_percent), AVG(temperature),
                       MAX(cpu_percent), MAX(ram_percent), MAX(disk_percent), MAX(temperature), COUNT(*)
                FROM health_snapshots
                WHERE date >= ?
            '''
        params = [start_date]

        if user_name:
            query += ' AND tenNguoiDung = ?'
            params.append(user_name)

        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            row = cursor.fetchone()

        if row and row[8] > 0:
            return {
                'avg_cpu': row[0] or 0,
                'avg_ram': row[1] or 0,
                'avg_disk': row[2] or 0,
                'avg_temp': row[3] if row[3] and row[3] > 0 else None,
                'max_cpu': row[4] or 0,
                'max_ram': row[5] or 0,
                'max_disk': row[6] or 0,
                'max_temp': row[7] if row[7] and row[7] > 0 else None,
            }
        return {}

    def get_latest_health(self, user_name: str = "user") -> Dict:
        query = '''
                SELECT cpu_percent, ram_percent, disk_percent, temperature, timestamp
                FROM health_snapshots
                '''
        params = []

        if user_name:
            query += 'WHERE tenNguoiDung = ? '
            params.append(user_name)

        query += 'ORDER BY timestamp DESC LIMIT 1'

        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            row = cursor.fetchone()

        if row:
            return {'cpu_percent': row[0] or 0, 'ram_percent': row[1] or 0, 'disk_percent': row[2] or 0, 'temperature': row[3] or 0, 'timestamp': row[4]}
        return {}

    def get_top_apps_range(self, start_date=None, end_date=None, user_name: str = "user", limit: int = 10):
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if isinstance(start_date, datetime):
            start_date = start_date.strftime('%Y-%m-%d')
        if isinstance(end_date, datetime):
            end_date = end_date.strftime('%Y-%m-%d')

        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    SELECT tenUngDung, COUNT(*) as soLanMo, MAX(thoiGianMo) as lanMoCuoi
                    FROM app_usage_logs
                    WHERE date(thoiGianMo) BETWEEN ? AND ?
                    GROUP BY tenUngDung
                    ORDER BY soLanMo DESC
                    LIMIT ?
                ''', (start_date, end_date, limit))
                rows = cursor.fetchall()
                return rows
            except Exception as e:
                logger.error("[UsageTracker] get_top_apps_range error: %s", e, exc_info=True)
                return []

    def get_total_usage_hours(self, days: int = 30, user_name: str = "user") -> float:
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        query = '''
                SELECT SUM(duration_seconds)
                FROM usage_sessions
                WHERE date >= ?
            '''
        params = [start_date]

        if user_name:
            query += ' AND tenNguoiDung = ?'
            params.append(user_name)

        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            result = cursor.fetchone()

        if result and result[0]:
            return round(result[0] / 3600, 2)
        return 0.0

    def get_weekly_report(self, user_name: str = "user") -> Dict:
        this_week = self.get_daily_usage(days=7, user_name=user_name)
        total_hours = sum(d['hours'] for d in this_week)
        total_sessions = sum(d['sessions'] for d in this_week)
        top_apps = self.get_top_apps(days=7, user_name=user_name, limit=5)
        health = self.get_health_trends(days=7, user_name=user_name)

        suggestions = []
        if health.get('avg_ram', 0) > 80:
            suggestions.append("RAM trung bình cao ({}%). Hãy đóng các ứng dụng không cần thiết.".format(health['avg_ram']))
        if health.get('avg_cpu', 0) > 70:
            suggestions.append("CPU thường xuyên cao ({}%). Kiểm tra các process nặng.".format(health['avg_cpu']))
        if health.get('avg_temp', 0) and health['avg_temp'] > 75:
            suggestions.append("Nhiệt độ trung bình cao ({}°C). Kiểm tra quạt tản nhiệt.".format(health['avg_temp']))
        if total_hours > 40:
            suggestions.append("Bạn dùng máy {} giờ/tuần. Hãy nghỉ ngơi đúng giờ!".format(total_hours))

        return {
            'total_hours': total_hours,
            'total_sessions': total_sessions,
            'daily_breakdown': this_week,
            'top_apps': top_apps,
            'health': health,
            'suggestions': suggestions,
        }


# Singleton instance
_tracker = UsageTracker()


def get_tracker() -> UsageTracker:
    """Get singleton usage tracker instance"""
    return _tracker
