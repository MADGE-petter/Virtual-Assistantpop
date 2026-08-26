"""Analytics Service - Background service for collecting analytics data"""

import re
import threading
import time
from datetime import datetime
from typing import Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    psutil = None

from model.usage_tracker import get_tracker


class AnalyticsService:
    """Service chạy nền để thu thập dữ liệu phân tích"""
    
    def __init__(self, user_name: str = "user"):
        self.user_name = user_name
        self.tracker = get_tracker()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._snapshot_interval = 300  # 5 phút
    
    def start(self):
        """Bắt đầu thu thập dữ liệu"""
        if self._running:
            return
        
        self._running = True
        self.tracker.start_session(self.user_name)
        self._thread = threading.Thread(target=self._collect_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Dừng thu thập dữ liệu"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self.tracker.end_session(self.user_name)
    
    def _collect_loop(self):
        """Vòng lặp thu thập dữ liệu"""
        while self._running:
            try:
                # Thu thập health snapshot
                self._collect_health_snapshot()
                time.sleep(self._snapshot_interval)
            except Exception:
                time.sleep(60)
    
    def _collect_health_snapshot(self):
        """Thu thập health snapshot"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # RAM
            ram = psutil.virtual_memory()
            ram_percent = ram.percent
            
            # Disk
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Temperature (nếu có)
            temp = None
            try:
                from model.temperature_monitor import get_cpu_temperature_auto
                result = get_cpu_temperature_auto()
                # Parse từ kết quả
                match = re.search(r'(\d+\.?\d*)°C', result)
                if match:
                    temp = float(match.group(1))
            except:
                pass
            
            # Lưu snapshot
            self.tracker.log_health_snapshot(
                cpu=cpu_percent,
                ram=ram_percent,
                disk=disk_percent,
                temp=temp,
                user_name=self.user_name
            )
        except Exception:
            pass
    
    def log_app_opened(self, app_name: str):
        """Log ứng dụng được mở"""
        self.tracker.log_app_opened(app_name, self.user_name)

    def set_user_name(self, user_name: str):
        """Switch the active analytics user context."""
        if not user_name:
            return

        if self.user_name == user_name:
            return

        if self._running:
            try:
                self.tracker.end_session(self.user_name)
            except Exception:
                pass
            self.user_name = user_name
            self.tracker.start_session(self.user_name)
        else:
            self.user_name = user_name
    
    def get_dashboard_data(self) -> dict:
        """Lấy dữ liệu cho dashboard"""
        return {
            'daily_usage': self.tracker.get_daily_usage(days=7, user_name=self.user_name),
            'top_apps': self.tracker.get_top_apps(days=7, user_name=self.user_name),
            'health_trends': self.tracker.get_health_trends(days=7, user_name=self.user_name),
            'total_hours': self.tracker.get_total_usage_hours(days=30, user_name=self.user_name),
            'weekly_report': self.tracker.get_weekly_report(user_name=self.user_name)
        }


# Singleton
_analytics_service: Optional[AnalyticsService] = None

def get_analytics_service(user_name: str = "user") -> AnalyticsService:
    """Get or create analytics service singleton"""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService(user_name)
    elif user_name and _analytics_service.user_name != user_name:
        _analytics_service.set_user_name(user_name)
    return _analytics_service
