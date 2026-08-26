"""
Alert Notifier - Xử lý thông báo cảnh báo
"""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Callable, Dict, Optional

if TYPE_CHECKING:
    from .types import Alert


class AlertNotifier:
    """Xử lý phát âm thanh và hiển thị cảnh báo"""
    
    def __init__(self, audio_service=None, ui_callback: Optional[Callable] = None):
        self.audio_service = audio_service
        self.ui_callback = ui_callback
        self._recovery_cooldown: Dict[str, datetime] = {}
    
    def speak_alert(self, alert: 'Alert'):
        """Phát âm thanh cảnh báo"""
        if not self.audio_service:
            return
            
        try:
            prefix = ""
            if alert.level.value == "danger":
                prefix = "Cảnh báo nguy hiểm! "
            elif alert.level.value == "critical":
                prefix = "Cảnh báo! "
            elif alert.level.value == "warning":
                prefix = "Lưu ý: "
            
            self.audio_service.speak(prefix + alert.message)
        except Exception as e:
            print(f"[AlertNotifier] Error speaking alert: {e}")
    
    def speak_recovery(self, metric: str, message: str):
        """Thông báo khi hệ thống phục hồi"""
        # Kiểm tra cooldown (5 phút)
        now = datetime.now()
        if metric in self._recovery_cooldown:
            if now - self._recovery_cooldown[metric] < timedelta(minutes=5):
                return
        
        self._recovery_cooldown[metric] = now
        
        if self.audio_service:
            try:
                self.audio_service.speak(f"✓ {message}")
            except Exception:
                pass
    
    def show_ui(self, alert: 'Alert'):
        """Hiển thị cảnh báo lên UI"""
        if self.ui_callback:
            try:
                # Convert Alert object to dict for UI
                alert_data = {
                    'id': alert.id,
                    'level': alert.level.value,
                    'metric': alert.metric,
                    'message': alert.message,
                    'value': alert.value,
                    'timestamp': alert.timestamp.strftime('%H:%M:%S %d/%m/%Y') if hasattr(alert.timestamp, 'strftime') else str(alert.timestamp),
                    'acknowledged': alert.acknowledged
                }
                self.ui_callback(alert_data)
            except Exception as e:
                print(f"[AlertNotifier] Error calling UI callback: {e}")
    
    def notify(self, alert: 'Alert'):
        """Thông báo đầy đủ (voice + UI)"""
        self.speak_alert(alert)
        self.show_ui(alert)
