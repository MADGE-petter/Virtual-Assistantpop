"""
Alert Manager - Orchestrator chính
"""

import threading
import time
from typing import Callable, Dict, List, Optional

from database.alert_repository import AlertRepository

from .checker import BatteryMonitor, CPUMonitor, DiskMonitor, RAMMonitor, TempMonitor
from .interactive import InteractiveAlertHandler
from .notifier import AlertNotifier
from .types import Alert, AlertLevel, AlertThreshold


class AlertManager:
    """Quản lý và điều phối hệ thống cảnh báo"""
    
    # Memory management
    MAX_ALERT_HISTORY = 100  # Giới hạn số lượng alert trong memory
    
    # Ngưỡng mặc định
    DEFAULT_THRESHOLDS = {
        'cpu': AlertThreshold('cpu', warning=80.0, critical=95.0),
        'ram': AlertThreshold('ram', warning=80.0, critical=90.0, danger=95.0),  # Interactive at >=80%
        'disk': AlertThreshold('disk', warning=85.0, critical=90.0, danger=95.0),
        'battery': AlertThreshold('battery', warning=20.0, critical=10.0),
        'temperature': AlertThreshold('temperature', warning=70.0, critical=80.0, danger=90.0)  # Interactive at >=80%
    }
    
    WELLNESS_SETTINGS = {
        'night_start_hour': 23,
        'night_end_hour': 2,
        'rest_suggestions': [
            "Bạn đã làm việc khuya rồi đấy. Nên nghỉ ngơi để giữ sức khỏe nhé!",
            "Khuya rồi! Hãy để mắt và cơ thể nghỉ ngơi nhé.",
            "Bạn có thấy mệt không? Nên ngủ sớm để mai còn làm việc.",
        ]
    }
    
    def __init__(self, audio_service=None, ui_callback: Optional[Callable] = None, 
                 check_interval: int = 60, user_name: str = "bạn", db_path: str = None,
                 interactive_callback: Optional[Callable] = None):
        self.audio_service = audio_service
        self.ui_callback = ui_callback
        self.interactive_callback = interactive_callback
        self.user_name = user_name
        
        # Database for alert persistence
        if db_path is None:
            import os
            self.db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'conversations.db')
        else:
            self.db_path = db_path
        
        # Initialize repository (Data Access Layer)
        self._alert_repo = AlertRepository(self.db_path)
        self._alert_repo._init_tables()
        
        # Thread safety - use RLock for reentrant locking
        self._lock = threading.RLock()
        
        # Cấu hình
        self.thresholds = dict(self.DEFAULT_THRESHOLDS)
        self.check_interval = check_interval
        self._wellness_enabled = True
        self._is_sleeping = False
        
        # Interactive alert helper
        self.interactive_handler = InteractiveAlertHandler(interactive_callback)
        
        # Initialize alert persistence
        self._init_alert_persistence()
        
        # Trạng thái
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._alerts: List[Alert] = []
        self._last_alert_time: dict = {}
        self._last_wellness_alert: Optional[float] = None
        
        # Load alerts from database on startup
        self._load_alerts_from_memory()
        
        # Cleanup old alerts to prevent database bloat
        self.cleanup_old_alerts()
        
        # Khởi tạo notifier và monitors
        self.notifier = AlertNotifier(audio_service, ui_callback)
        self.monitors = [
            CPUMonitor(self.thresholds['cpu']),
            RAMMonitor(self.thresholds['ram']),
            DiskMonitor(self.thresholds['disk']),
            TempMonitor(self.thresholds['temperature']),
            BatteryMonitor(self.thresholds['battery'])
        ]
    
    def start(self):
        """Bắt đầu giám sát"""
        if not self._running:
            self._running = True
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()
            print(f"[AlertManager] Started monitoring with {len(self.monitors)} monitors")
    
    def stop(self):
        """Dừng giám sát"""
        if self._running:
            self._running = False
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=5)
            print("[AlertManager] Stopped monitoring")
    
    def _monitor_loop(self):
        """Vòng lặp giám sát chính"""
        while self._running:
            try:
                # Kiểm tra từng monitor
                for monitor in self.monitors:
                    alert, is_recovery = monitor.check()
                    
                    if alert:
                        if self.interactive_handler.is_interactive_alert(alert):
                            self.interactive_handler.handle_alert(alert)
                        elif self._should_alert(alert):
                            with self._lock:
                                self._alerts.append(alert)
                                self._record_alert(alert)
                                self._manage_alert_memory()
                                self._save_alert_to_db(alert)
                            self.notifier.notify(alert)
                    
                    elif is_recovery:
                        metric = monitor.threshold.metric
                        self.interactive_handler.clear_alert(metric)
                        from datetime import datetime
                        self.notifier.speak_recovery(metric, f"{metric.upper()} đã trở lại bình thường")
                
                self.interactive_handler.check_reminders()
                self._check_wellness()
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                print(f"[AlertManager] Monitor loop error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(self.check_interval)
    
    def _should_alert(self, alert) -> bool:
        """Kiểm tra cooldown 10 phút giữa các cảnh báo cùng metric và level"""
        key = f"{alert.metric}_{alert.level.value}"
        
        with self._lock:
            if key not in self._last_alert_time:
                return True
            
            cooldown = 600  # 10 phút
            return time.time() - self._last_alert_time[key] > cooldown
    
    def _record_alert(self, alert):
        """Ghi lại thời gian cảnh báo theo metric và level"""
        key = f"{alert.metric}_{alert.level.value}"
        with self._lock:
            self._last_alert_time[key] = time.time()
    
    def _manage_alert_memory(self):
        """Quản lý memory - xóa alert cũ nếu cần"""
        while len(self._alerts) > self.MAX_ALERT_HISTORY:
            self._alerts.pop(0)
    
    def get_memory_stats(self) -> dict:
        """Lấy thống kê memory usage"""
        with self._lock:
            return {
                'total_alerts': len(self._alerts),
                'max_history': self.MAX_ALERT_HISTORY,
                'memory_usage_percent': round(len(self._alerts) / self.MAX_ALERT_HISTORY * 100, 1),
                'cooldown_keys': len(self._last_alert_time),
                'oldest_alert_age': (time.time() - (self._alerts[0].timestamp.timestamp() if hasattr(self._alerts[0].timestamp, 'timestamp') else self._alerts[0].timestamp)) if self._alerts else 0
            }
    
    def _init_alert_persistence(self):
        """Khởi tạo alert persistence - delegated to repository"""
        # Tables are initialized in __init__ via self._alert_repo._init_tables()
        pass
    
    def _save_alert_to_db(self, alert: Alert):
        """Lưu alert vào database"""
        self._alert_repo.save_alert(
            alert.id,
            alert.metric,
            alert.level.value,
            alert.value,
            alert.message,
            alert.timestamp.timestamp() if hasattr(alert.timestamp, 'timestamp') else alert.timestamp,
            alert.acknowledged
        )
    
    def _load_alerts_from_db(self, limit: int = 100) -> List[Alert]:
        """Tải alerts từ database"""
        rows = self._alert_repo.load_alerts(limit)
        alerts = []
        for row in rows:
            from datetime import datetime
            alert = Alert(
                id=row['id'],
                metric=row['metric'],
                level=AlertLevel(row['level']),
                value=row['value'],
                message=row['message'],
                timestamp=datetime.fromtimestamp(row['timestamp'])
            )
            alert.acknowledged = row['acknowledged']
            alerts.append(alert)
        return alerts
    
    def _load_alerts_from_memory(self):
        """Tải alerts từ database vào memory khi khởi động"""
        try:
            alerts = self._load_alerts_from_db(self.MAX_ALERT_HISTORY)
            with self._lock:
                self._alerts = alerts
            print(f"[AlertManager] Loaded {len(alerts)} alerts from database")
        except Exception as e:
            print(f"[AlertManager] Error loading alerts from memory: {e}")
            with self._lock:
                self._alerts = []
    
    def _check_wellness(self):
        """Nhắc nghỉ ngơi khi khuya"""
        if not self._wellness_enabled or self._is_sleeping:
            return
            
        from datetime import datetime
        current_hour = datetime.now().hour
        settings = self.WELLNESS_SETTINGS
        
        if settings['night_start_hour'] <= current_hour or current_hour < settings['night_end_hour']:
            # Kiểm tra đã nhắc trong 30 phút chưa
            if self._last_wellness_alert:
                if time.time() - self._last_wellness_alert < 1800:
                    return
            
            import random
            msg = random.choice(settings['rest_suggestions'])
            self._last_wellness_alert = time.time()
            
            if self.audio_service:
                try:
                    self.audio_service.speak(msg)
                except:
                    pass
    
    # Public API
    def set_sleep_mode(self, enabled: bool):
        self._is_sleeping = enabled
    
    def reset_wellness_timers(self):
        pass
    
    def enable_wellness(self, enabled: bool = True):
        self._wellness_enabled = enabled
    
    def get_active_alerts(self) -> List[Alert]:
        with self._lock:
            return [a for a in self._alerts if not a.acknowledged]
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge alert and sync to database"""
        # Update in RAM
        alert_found = False
        with self._lock:
            for alert in self._alerts:
                if alert.id == alert_id:
                    alert.acknowledged = True
                    alert_found = True
                    break
        
        # Update in database via repository
        if alert_found:
            if self._alert_repo.acknowledge_alert(alert_id):
                print(f"[AlertManager] Alert {alert_id} acknowledged and synced to database")
        else:
            print(f"[AlertManager] Alert {alert_id} not found for acknowledgment")
    
    def get_system_status(self) -> dict:
        import psutil
        try:
            battery = psutil.sensors_battery()
            battery_info = {
                'percent': battery.percent if battery else None,
                'plugged': battery.power_plugged if battery else None
            }
        except:
            battery_info = {'percent': None, 'plugged': None}
        
        return {
            'cpu': psutil.cpu_percent(interval=0.5),
            'ram': psutil.virtual_memory().percent,
            'disk': {p.mountpoint: psutil.disk_usage(p.mountpoint).percent 
                    for p in psutil.disk_partitions(all=False) 
                    if psutil.disk_usage(p.mountpoint)},
            'battery': battery_info,
            'active_alerts': len(self.get_active_alerts())
        }
    
    def cleanup_old_alerts(self, days_to_keep: int = 30, max_rows: int = 5000):
        """Clean old alerts from database to prevent unlimited growth
        
        Args:
            days_to_keep: Keep alerts newer than this many days
            max_rows: Keep maximum this many rows total
        """
        result = self._alert_repo.cleanup_old_alerts(days_to_keep, max_rows)
        if result['time_deleted'] > 0 or result['row_deleted'] > 0:
            print(f"[AlertManager] Database cleanup completed: {result['time_deleted']} by time, {result['row_deleted']} by count")
        else:
            total = self._alert_repo.get_alert_count()
            print(f"[AlertManager] No cleanup needed (total: {total} rows)")
    
    def clear_all_alerts(self):
        """Clear all alerts from both RAM and database"""
        # Clear RAM
        with self._lock:
            self._alerts.clear()
            self._last_alert_time.clear()
        
        # Clear database via repository
        if self._alert_repo.delete_all_alerts():
            print(f"[AlertManager] Cleared all alerts from database and vacuumed")

    def handle_interactive_response(self, metric: str, response: str, context: dict = None):
        self.interactive_handler.handle_response(metric, response, context)

    def get_interactive_context(self, metric: str) -> dict:
        return self.interactive_handler.get_context(metric)

    def get_active_interactive_metrics(self) -> list:
        return list(self.interactive_handler._interactive_alerts.keys())


# Singleton
_alert_manager: Optional[AlertManager] = None

def get_alert_manager(audio_service=None, ui_callback=None) -> AlertManager:
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager(audio_service, ui_callback)
    return _alert_manager
