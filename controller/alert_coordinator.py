"""Alert Coordinator - Handles interactive alert logic (extracted from PopController)."""
from typing import Optional, Callable, Dict, Any

from service.alert.types import Alert


class AlertCoordinator:
    """Handles interactive alert responses and user conversations."""
    
    def __init__(self, audio_service, view=None):
        self.audio = audio_service
        self.view = view
        self._interactive_context: Optional[Dict] = None
    
    def handle_interactive_alert(self, alert: Alert, action: str, context: Optional[Dict] = None):
        """Process interactive alert actions."""
        try:
            if action == 'ask_details':
                message = f"{alert.message}. Bạn có muốn xem tiến trình chi tiết không?"
                self.audio.speak(message)
                
            elif action == 'remind':
                message = f"Nhắc nhở: {alert.message}. Bạn có muốn xem tiến trình chi tiết không?"
                self.audio.speak(message)
                
            elif action == 'show_details':
                self._handle_show_details(alert)
                
            elif action == 'ask_close_app':
                message = "Bạn muốn đóng ứng dụng nào? Hãy nói tên ứng dụng hoặc số thứ tự (1, 2, 3...)"
                self.audio.speak(message)
                
            elif action == 'close_success':
                self._handle_close_success(context)
                
            elif action == 'close_failed':
                self._handle_close_failed(context)
                
        except Exception as e:
            print(f"[AlertCoordinator] Error: {e}")
            import traceback
            traceback.print_exc()
    
    def _handle_show_details(self, alert: Alert):
        """Show top processes for the alert metric."""
        from service.system_monitoring_service import (
            format_process_list,
            get_top_cpu_processes,
            get_top_ram_processes,
        )
        
        if alert.metric == 'ram':
            processes = get_top_ram_processes(5)
            process_list = format_process_list(processes, 'ram')
            message = f"Top 5 ứng dụng dùng RAM nhiều nhất:\n{process_list}\n\nBạn có muốn đóng ứng dụng nào không?"
        else:  # temperature
            processes = get_top_cpu_processes(5)
            process_list = format_process_list(processes, 'cpu')
            message = f"Top 5 ứng dụng dùng CPU nhiều nhất:\n{process_list}\n\nBạn có muốn đóng ứng dụng nào không?"
        
        # Store context for parsing user selection
        self._interactive_context = {
            'metric': alert.metric,
            'top_processes': processes
        }
        
        self.audio.speak(message)
    
    def _handle_close_success(self, context: Optional[Dict]):
        """Handle successful app closure."""
        if not context:
            return
            
        closed_apps = context.get('closed_apps')
        failed_apps = context.get('failed_apps')
        
        if closed_apps:
            app_names = ', '.join([app.get('name', 'ứng dụng') for app in closed_apps])
            if failed_apps:
                failed_names = ', '.join([app.get('name', 'ứng dụng') for app in failed_apps])
                message = f"Đã đóng {app_names} thành công. Không thể đóng {failed_names}."
            else:
                message = f"Đã đóng {app_names} thành công."
        else:
            closed_app = context.get('closed_app', {})
            app_name = closed_app.get('name', 'ứng dụng')
            message = f"Đã đóng {app_name} thành công."
        
        self.audio.speak(message)
    
    def _handle_close_failed(self, context: Optional[Dict]):
        """Handle failed app closure."""
        if not context:
            return
            
        failed_apps = context.get('failed_apps')
        
        if failed_apps:
            failed_names = ', '.join([app.get('name', 'ứng dụng') for app in failed_apps])
            message = f"Không thể đóng {failed_names}. Vui lòng thử lại hoặc đóng thủ công."
        else:
            failed_app = context.get('failed_app', {})
            app_name = failed_app.get('name', 'ứng dụng')
            message = f"Không thể đóng {app_name}. Vui lòng thử lại hoặc đóng thủ công."
        
        self.audio.speak(message)
    
    def get_interactive_context(self) -> Optional[Dict]:
        """Get stored interactive context."""
        return self._interactive_context
    
    def clear_interactive_context(self):
        """Clear interactive context."""
        self._interactive_context = None