"""Action module - Xử lý các hành động theo ý định (Refactored - Modular)."""
import os
import sys

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
    
    def __init__(self, audio_service=None, view=None):
        self.audio_service = audio_service
        self.view = view
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
            getattr(handler, method)(value)
    
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
    
    def handle(self, intent, text, user_name=None, context=None):
        if user_name:
            self.set_user_name(user_name)
        
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
            "unknown": self.greeting_handler.handle_unknown
        }
        if intent == "weather":
            result = self.weather_handler.handle(text, context)
            return result  # ActionResult from handler
        
        # Global last_intent removed - use context-based approach in ConversationService
        
        handler = handlers.get(intent, self.greeting_handler.handle_unknown)
        result = handler(text)
        
        # Wrap string results in ActionResult for consistency
        if not isinstance(result, ActionResult):
            result = ActionResult(text=str(result))
        
        return result
