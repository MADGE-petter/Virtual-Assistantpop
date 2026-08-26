"""Base Handler - Abstract base class for all handlers."""

import time
from abc import ABC, abstractmethod


class BaseHandler(ABC):
  
    def __init__(self, audio_service=None, view=None):
        self.audio_service = audio_service
        self.view = view
        self.user_name = "bạn"
        self.login_username = None
    
    def set_audio_service(self, audio_service):
        """Set audio service."""
        self.audio_service = audio_service
    
    def set_view(self, view):
        """Set view reference."""
        self.view = view
    
    def set_user_name(self, name):
        """Set user name."""
        self.user_name = name

    def set_login_name(self, name):
        """Set login username for user-specific logging."""
        self.login_username = name
    
    @abstractmethod
    def handle(self, text): 
        pass
    
    def speak(self, text, wait=0):
        
        if self.audio_service:
            result = self.audio_service.speak(text)
            if wait > 0:
                time.sleep(wait)
            return result
        return None
    
    def speak_and_return(self, text, wait=0):
        self.speak(text, wait)
        return text
