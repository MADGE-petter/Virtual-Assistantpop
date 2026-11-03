import threading
import time

from controller.handlers import (
    AppHandler,
    FileHandler,
    GreetingHandler,
    HabitHandler,
    SearchHandler,
    SystemHandler,
    TimeHandler,
    WeatherHandler,
)

# Import ActionResult for wrapping responses
from service.conversation_service import ActionResult


class ActionHandler:
    
    def __init__(self, audio_service=None, view=None, controller=None):
        self.audio_service = audio_service
        self.view = view
        self.controller = controller
        self.user_name = "bạn"
        self._handlers = []
        
        # Initialize all handlers
        self._init_handlers(audio_service, view)
    
    def _init_handlers(self, audio_service, view):
        """Khởi tạo tất cả handlers."""
        self.time_handler = TimeHandler(audio_service, view)
        self.weather_handler = WeatherHandler(audio_service, view)
        self.system_handler = SystemHandler(audio_service, view)
        self.search_handler = SearchHandler(audio_service, view)
        self.app_handler = AppHandler(audio_service, view)
        self.file_handler = FileHandler(audio_service, view)
        self.greeting_handler = GreetingHandler(audio_service, view)
        self.habit_handler = HabitHandler()
        
        self._handlers = [
            self.time_handler, self.weather_handler, self.system_handler,
            self.search_handler, self.app_handler, self.greeting_handler,
            self.file_handler, self.habit_handler
        ]
    
    def _update_handlers(self, method, value):
        """Helper để cập nhật tất cả handlers."""
        for handler in self._handlers:
            func = getattr(handler, method, None)
            if callable(func):
                func(value)
    
    def set_audio_service(self, audio_service):
        """Set audio service cho tất cả handlers."""
        self.audio_service = audio_service
        self._update_handlers('set_audio_service', audio_service)
    
    def set_view(self, view):
        """Set view reference cho tất cả handlers."""
        self.view = view
        self._update_handlers('set_view', view)
    
    def set_user_name(self, name):
        """Set user name cho tất cả handlers."""
        self.user_name = name
        self._update_handlers('set_user_name', name)
    
    def set_login_name(self, name):
        """Set login username cho tất cả handlers."""
        self._update_handlers('set_login_name', name)
    
    def set_controller(self, controller):
        """Set controller reference."""
        self.controller = controller
        self._update_handlers('set_controller', controller)
    
    def handle(self, intent, text, user_name=None, context=None, execute=False):
        if user_name:
            self.set_user_name(user_name)
            
        sensitive_intents = {
            "open_website": "Mở trang web",
            "open_app": "Mở ứng dụng",
            "system_control": "Điều khiển hệ thống",
            "open_file": "Mở tệp"
        }
        
        # Ngăn chặn thực thi ngay nếu là lệnh nhạy cảm và chưa được confirm
        if intent in sensitive_intents and not execute:
            summary = f"{sensitive_intents[intent]}: '{text}'"
            return ActionResult(
                text="Vui lòng xác nhận hành động.",
                needs_permission=True,
                tool_name=intent,
                tool_args={"text": text},
                summary_text=summary,
                confirmation_title="Xác nhận hành động"
            )
        
        # Intent to handler mapping
        handlers = {
            "greeting": self.greeting_handler.handle_greeting,
            "help": self.greeting_handler.handle_help,
            "name": self.greeting_handler.handle_name,
            "time": self.time_handler.handle,
            "weather": self.weather_handler.handle,
            "search": self.search_handler.handle,
            "open_website": self.app_handler.handle_website,
            "open_app": self.app_handler.handle_app,
            "open_file": self.file_handler.handle_open_file,
            "system_control": self.system_handler.handle,
            "sleep": self.greeting_handler.handle_sleep,
            "goodbye": self.greeting_handler.handle_goodbye,
            "habit_query": self.habit_handler.handle,
            "exit_app": self.handle_exit_app,
            "unknown": self.greeting_handler.handle_unknown
        }
        if intent == "weather":
            result = self.weather_handler.handle(text, context)
            return result  # ActionResult from handler
        
        handler = handlers.get(intent, self.greeting_handler.handle_unknown)
        result = handler(text)
        
        # Wrap string results in ActionResult for consistency
        if not isinstance(result, ActionResult):
            result = ActionResult(text=str(result))
        
        return result

    def handle_exit_app(self, text=""):
        """Xử lý lệnh tắt ứng dụng Pop (tự hủy đi / tắt đi / tắt app)."""
        text_lower = text.lower() if text else ""
        if "tự hủy" in text_lower:
            reply = "Đã kích hoạt chế độ tự hủy. Đang tắt ứng dụng, tạm biệt bạn!"
        else:
            reply = "Đang tắt ứng dụng. Tạm biệt bạn!"
            
        def _delayed_exit():
            try:
                # Đợi TTS phát âm xong trước khi đóng app
                if self.audio_service and hasattr(self.audio_service, "wait_until_speaking_done"):
                    time.sleep(0.5)
                    self.audio_service.wait_until_speaking_done()
                else:
                    time.sleep(2.0)
            except Exception:
                time.sleep(2.0)
                
            # Đóng ứng dụng qua controller hoặc view
            if self.controller and hasattr(self.controller, "exit_app"):
                self.controller.exit_app()
            elif self.view and hasattr(self.view, "close"):
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(0, self.view.close)
            else:
                from PyQt6.QtWidgets import QApplication
                app = QApplication.instance()
                if app:
                    app.quit()
        
        threading.Thread(target=_delayed_exit, name="PopExitAppThread", daemon=True).start()
        return reply
