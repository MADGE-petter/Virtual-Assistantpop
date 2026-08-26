"""
Alert Types - Định nghĩa Enums và Dataclasses

Bao gồm:
1. Basic Alert System - Hard thresholds
2. Intelligent Alert System - Personalized thresholds
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

# ============================================================================
# BASIC ALERT SYSTEM (Có sẵn)
# ============================================================================

class AlertLevel(Enum):
    """Mức độ cảnh báo"""
    WARNING = "warning"      # Vàng
    CRITICAL = "critical"    # Đỏ
    DANGER = "danger"        # Đỏ đậm
    INFO = "info"           # Xanh


@dataclass
class AlertThreshold:
    """Ngưỡng cảnh báo"""
    metric: str           # cpu, ram, disk, battery
    warning: float        # Ngưỡng warning
    critical: float       # Ngưỡng critical
    danger: Optional[float] = None  # Ngưỡng danger (optional)


@dataclass
class Alert:
    """Đối tượng cảnh báo"""
    id: str
    level: AlertLevel
    metric: str
    message: str
    value: float
    timestamp: datetime
    acknowledged: bool = False


# ============================================================================
# INTELLIGENT ALERT SYSTEM (Mới)
# ============================================================================

class AlertType(Enum):
    """Types of alerts supported by the system"""
    
    # Health Metrics
    CPU_HIGH = "cpu_high"
    RAM_FULL = "ram_full"
    DISK_FULL = "disk_full"
    TEMPERATURE_HIGH = "temperature_high"
    BATTERY_LOW = "battery_low"
    
    # Behavioral
    LATE_NIGHT = "late_night"
    LONG_SESSION = "long_session"
    SMART_SLEEP = "smart_sleep"
    
    # Anomaly Detection
    UNUSUAL_APP_TIME = "unusual_app_time"
    BEHAVIOR_DRIFT = "behavior_drift"
    ANOMALOUS_PATTERN = "anomalous_pattern"
    
    # System
    SYSTEM_ERROR = "system_error"
    DATABASE_FULL = "database_full"


class AlertSeverity(Enum):
    """Alert severity levels"""
    
    INFO = 1      # ℹ️ Informational
    WARNING = 2   # ⚠️ Warning  
    ELEVATED = 3  # 🔶 Elevated concern
    CRITICAL = 4  # 🚨 Critical issue
    
    @property
    def label(self) -> str:
        """Get emoji label for severity"""
        labels = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️", 
            AlertSeverity.ELEVATED: "🔶",
            AlertSeverity.CRITICAL: "🚨"
        }
        return labels.get(self, "❓")
    
    @property
    def color(self) -> str:
        """Get color code for UI"""
        colors = {
            AlertSeverity.INFO: "#3498db",      # Blue
            AlertSeverity.WARNING: "#f39c12",    # Orange
            AlertSeverity.ELEVATED: "#e67e22",   # Dark Orange
            AlertSeverity.CRITICAL: "#e74c3c"     # Red
        }
        return colors.get(self, "#95a5a6")  # Gray default


class AlertContext(Enum):
    """Context for health metric alerts"""
    
    GAMING = "gaming"
    CODING = "coding"
    BROWSING = "browsing"
    IDLE = "idle"
    WORK = "work"
    ENTERTAINMENT = "entertainment"
    GLOBAL = "global"
