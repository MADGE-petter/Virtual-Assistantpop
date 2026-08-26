"""Interactive alert service - phối hợp alert manager với voice và UI."""
from typing import Callable, Optional

from service.alert import AlertManager
from service.alert.interactive import InteractiveAlertHandler


class InteractiveAlertService:
    def __init__(
        self,
        audio_service,
        view=None,
        alert_manager: Optional[AlertManager] = None,
    ):
        self.audio = audio_service
        self.view = view
        self.alert_manager = alert_manager

    def set_alert_manager(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager

    def on_alert(self, alert_data: dict):
        if self.view:
            try:
                self.view.show_alert_notification(alert_data)
            except Exception:
                pass

    def on_interactive_alert(self, alert, action, context=None):
        try:
            message = self._get_message_for_action(alert, action, context)
            if message:
                self.audio.speak(message)
        except Exception as e:
            print(f"[InteractiveAlertService] Error handling interactive alert: {e}")
            import traceback

            traceback.print_exc()

    def try_handle_response(self, user_input: str) -> bool:
        if not self.alert_manager:
            return False

        if not user_input or user_input in ["...", "", None, 0]:
            return False

        user_input_lower = user_input.lower()
        interactive_keywords = [
            "có",
            "không",
            "yes",
            "no",
            "ok",
            "ừ",
            "vâng",
            "thôi",
            "bỏ qua",
            "app",
            "số",
            "đóng",
            "xóa",
            "1",
            "2",
            "3",
            "4",
            "5",
        ]

        for keyword in interactive_keywords:
            if keyword in user_input_lower:
                for metric in self.alert_manager.get_active_interactive_metrics():
                    context = self.alert_manager.get_interactive_context(metric)
                    self.alert_manager.handle_interactive_response(metric, user_input, context)
                return True

        return False

    def _get_message_for_action(self, alert, action: str, context=None) -> Optional[str]:
        if action == 'ask_details':
            return f"{alert.message}. Bạn có muốn xem tiến trình chi tiết không?"

        if action == 'remind':
            return f"Nhắc nhở: {alert.message}. Bạn có muốn xem tiến trình chi tiết không?"

        if action == 'show_details':
            from service.system_monitoring_service import (
                format_process_list,
                get_top_cpu_processes,
                get_top_ram_processes,
            )

            if alert.metric == 'ram':
                processes = get_top_ram_processes(5)
                process_list = format_process_list(processes, 'ram')
                return f"Top 5 ứng dụng dùng RAM nhiều nhất:\n{process_list}\n\nBạn có muốn đóng ứng dụng nào không?"
            else:
                processes = get_top_cpu_processes(5)
                process_list = format_process_list(processes, 'cpu')
                return f"Top 5 ứng dụng dùng CPU nhiều nhất:\n{process_list}\n\nBạn có muốn đóng ứng dụng nào không?"

        if action == 'ask_close_app':
            return "Bạn muốn đóng ứng dụng nào trong Top 5? Hãy nói tên ứng dụng hoặc số thứ tự (1, 2, 3, 4, 5)."

        if action == 'close_success':
            closed_apps = context.get('closed_apps') if context else None
            failed_apps = context.get('failed_apps') if context else None
            if closed_apps:
                app_names = ', '.join([app.get('name', 'ứng dụng') for app in closed_apps])
                if failed_apps:
                    failed_names = ', '.join([app.get('name', 'ứng dụng') for app in failed_apps])
                    return f"Đã đóng {app_names} thành công. Không thể đóng {failed_names}."
                return f"Đã đóng {app_names} thành công."
            closed_app = context.get('closed_app', {}) if context else {}
            app_name = closed_app.get('name', 'ứng dụng')
            return f"Đã đóng {app_name} thành công."

        if action == 'close_failed':
            failed_apps = context.get('failed_apps') if context else None
            if failed_apps:
                failed_names = ', '.join([app.get('name', 'ứng dụng') for app in failed_apps])
                return f"Không thể đóng {failed_names}. Vui lòng thử lại hoặc đóng thủ công."
            failed_app = context.get('failed_app', {}) if context else {}
            app_name = failed_app.get('name', 'ứng dụng')
            return f"Không thể đóng {app_name}. Vui lòng thử lại hoặc đóng thủ công."

        return None
