"""
Alert Checkers - Các bộ giám sát CPU, RAM, Disk, Temperature, Battery
"""

import re
from abc import ABC, abstractmethod
from typing import Optional, Tuple

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    psutil = None

from .types import Alert, AlertLevel, AlertThreshold


class BaseMonitor(ABC):
    """Base class cho tất cả monitors"""
    
    def __init__(self, threshold: AlertThreshold):
        self.threshold = threshold
        self._alert_state: Optional[AlertLevel] = None
    
    @abstractmethod
    def check(self) -> Tuple[Optional[Alert], bool]:
        """
        Kiểm tra và trả về:
        - Alert nếu có cảnh báo mới
        - bool: True nếu có recovery (đã phục hồi)
        """
        pass
    
    def _should_recovery(self, current_value: float) -> bool:
        """Kiểm tra xem có nên thông báo recovery không"""
        return self._alert_state is not None and current_value < self.threshold.warning * 0.8
    
    def _create_alert(self, level: AlertLevel, message: str, value: float) -> Alert:
        """Tạo Alert object - giảm code lặp"""
        return Alert(
            id=f"{self.threshold.metric}_{datetime.now().timestamp()}",
            level=level,
            metric=self.threshold.metric,
            message=message,
            value=value,
            timestamp=datetime.now()
        )
    
    def _check_level(self, value: float, warning_msg: str, critical_msg: str, 
                     danger_msg: str = None) -> Tuple[Optional[Alert], bool]:
        """Kiểm tra level và trả về Alert hoặc recovery - giảm code lặp"""
        # Check danger level
        if self.threshold.danger and value >= self.threshold.danger:
            if self._alert_state != AlertLevel.DANGER:
                self._alert_state = AlertLevel.DANGER
                return self._create_alert(AlertLevel.DANGER, danger_msg, value), False
            return None, False
        
        # Check critical level
        if value >= self.threshold.critical:
            if self._alert_state != AlertLevel.CRITICAL:
                self._alert_state = AlertLevel.CRITICAL
                return self._create_alert(AlertLevel.CRITICAL, critical_msg, value), False
            return None, False
        
        # Check warning level
        if value >= self.threshold.warning:
            if self._alert_state != AlertLevel.WARNING:
                self._alert_state = AlertLevel.WARNING
                return self._create_alert(AlertLevel.WARNING, warning_msg, value), False
            return None, False
        
        # Recovery
        if self._should_recovery(value):
            self._alert_state = None
            return None, True
        
        return None, False


class CPUMonitor(BaseMonitor):
    """Giám sát CPU"""
    
    def check(self) -> Tuple[Optional[Alert], bool]:
        if not psutil:
            return None, False
        cpu_percent = psutil.cpu_percent(interval=None)
        return self._check_level(
            cpu_percent,
            f"CPU đang cao {cpu_percent:.1f}%. Hãy kiểm tra các ứng dụng đang chạy.",
            f"CPU đang ở mức nguy hiểm {cpu_percent:.1f}%. Vui lòng đóng ứng dụng không cần thiết!"
        )


class RAMMonitor(BaseMonitor):
    """Giám sát RAM"""
    
    def check(self) -> Tuple[Optional[Alert], bool]:
        if not psutil:
            return None, False
        ram = psutil.virtual_memory()
        
        # Lấy top processes nếu RAM cao
        top_processes = []
        if ram.percent >= self.threshold.warning:
            from service.system_monitoring_service import (
                format_process_list,
                get_top_ram_processes,
            )
            top_processes = get_top_ram_processes(5)
        
        # Tạo message với thông tin processes
        if top_processes:
            process_info = format_process_list(top_processes, 'ram')
            warning_msg = f"RAM đang cao {ram.percent:.1f}%. Top apps dùng RAM:\n{process_info}"
            critical_msg = f"RAM gần hết {ram.percent:.1f}%. Top apps dùng RAM:\n{process_info}"
            danger_msg = f"RAM đang rất cao {ram.percent:.1f}% và có thể gây chậm máy!"
        else:
            warning_msg = f"RAM đang cao {ram.percent:.1f}%. Nên đóng tab không dùng."
            critical_msg = f"RAM gần hết {ram.percent:.1f}%. Hệ thống có thể bị chậm!"
            danger_msg = f"RAM đang rất cao {ram.percent:.1f}% và có thể gây chậm máy!"
        
        return self._check_level(
            ram.percent,
            warning_msg,
            critical_msg,
            danger_msg
        )


class DiskMonitor(BaseMonitor):
    """Giám sát Disk"""
    
    def check(self) -> Tuple[Optional[Alert], bool]:
        if not psutil:
            return None, False
        disk_info = {}
        
        # Collect disk usage info safely
        for p in psutil.disk_partitions(all=False):
            try:
                disk_info[p.mountpoint] = psutil.disk_usage(p.mountpoint).percent
            except Exception as e:
                print(f"[DiskMonitor] Error checking {p.mountpoint}: {e}")
                continue
        
        # Find partition with highest usage
        max_usage = 0
        max_partition = ""
        
        for mountpoint, usage_percent in disk_info.items():
            if usage_percent > max_usage:
                max_usage = usage_percent
                max_partition = mountpoint
        
        return self._check_level(
            max_usage,
            f"Ổ đĩa {max_partition} đang đầy {max_usage:.1f}%.",
            f"Ổ đĩa {max_partition} đã đầy {max_usage:.1f}%. Nên xóa file rác.",
            f"Ổ đĩa {max_partition} gần đầy {max_usage:.1f}%! Cần dọn dẹp ngay!"
        )


class TempMonitor(BaseMonitor):
    """Giám sát nhiệt độ CPU/Hardware"""
    
    def check(self) -> Tuple[Optional[Alert], bool]:
        try:
            from model.temperature_monitor import get_cpu_temperature_auto
            temp_result = get_cpu_temperature_auto()
            
            match = re.search(r"(\d+\.?\d*)°C", temp_result)
            if not match:
                return None, False
                
            max_temp = float(match.group(1))
            
            # Xác định tên sensor
            sensor = "CPU"
            if "GPU" in temp_result:
                sensor = "GPU"
            elif "Core" in temp_result:
                sensor = "Core"
            
            # Lấy top CPU processes nếu nhiệt độ cao
            top_processes = []
            if max_temp >= self.threshold.warning:
                from service.system_monitoring_service import (
                    format_process_list,
                    get_top_cpu_processes,
                )
                top_processes = get_top_cpu_processes(5)
            
            # Tạo message với thông tin processes
            if top_processes:
                process_info = format_process_list(top_processes, 'cpu')
                warning_msg = f"Nhiệt độ {sensor}: {max_temp:.0f}°C - Đang nóng. Top apps dùng CPU:\n{process_info}"
                critical_msg = f"Nhiệt độ {sensor} cao: {max_temp:.0f}°C! Top apps dùng CPU:\n{process_info}"
                danger_msg = f"Nhiệt độ {sensor} rất cao: {max_temp:.0f}°C! Máy có thể bị nóng quá mức!"
            else:
                warning_msg = f"Nhiệt độ {sensor}: {max_temp:.0f}°C - Đang nóng, nên kiểm tra quạt tản nhiệt."
                critical_msg = f"Nhiệt độ {sensor} cao: {max_temp:.0f}°C! Cần làm mát ngay!"
                danger_msg = f"Nhiệt độ {sensor} rất cao: {max_temp:.0f}°C! Máy có thể bị nóng quá mức!"
            
            return self._check_level(
                max_temp,
                warning_msg,
                critical_msg,
                danger_msg
            )
        except Exception as e:
            print(f"[Monitor] Error checking {self.__class__.__name__}: {e}")
            return None, False
            
        return None, False


class BatteryMonitor(BaseMonitor):
    """Giám sát Pin - logic ngược: % thấp = cảnh báo"""
    
    def check(self) -> Tuple[Optional[Alert], bool]:
        try:
            battery = psutil.sensors_battery()
            if not battery or battery.power_plugged:
                return None, False  # Không có pin hoặc đang sạc
                
            percent = battery.percent
            
            if percent <= self.threshold.critical:
                self._alert_state = AlertLevel.CRITICAL
                return self._create_alert(
                    AlertLevel.CRITICAL,
                    f"Pin yếu còn {percent:.0f}%. Cần cắm sạc ngay!",
                    percent
                ), False
                
            elif percent <= self.threshold.warning:
                self._alert_state = AlertLevel.WARNING
                return self._create_alert(
                    AlertLevel.WARNING,
                    f"Pin yếu còn {percent:.0f}%. Nên cắm sạc.",
                    percent
                ), False
                
            elif self._alert_state and percent > self.threshold.warning * 2:
                self._alert_state = None  # Recovery khi pin đã sạc đủ
                return None, True
                
        except Exception as e:
            print(f"[Monitor] Error checking {self.__class__.__name__}: {e}")
            return None, False
            
        return None, False


# Import datetime here to avoid circular import issues
from datetime import datetime
