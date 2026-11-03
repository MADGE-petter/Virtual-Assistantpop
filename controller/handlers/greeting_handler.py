"""Greeting Handler - Xử lý chào hỏi, tên, help, goodbye, sleep."""

import re
import time


class GreetingHandler:
    """Handler for greeting, name, help, and control intents."""
    
    def __init__(self, audio_service=None, view=None):
        self.audio_service = audio_service
        self.view = view
        self.user_name = "bạn"
    
    def set_audio_service(self, audio_service):
        self.audio_service = audio_service
    
    def set_view(self, view):
        self.view = view
    
    def set_user_name(self, name):
        self.user_name = name
    
    def handle_greeting(self, text):
        """Xử lý chào hỏi."""
        if self.user_name == "bạn":
            return f"Chào bạn! Tôi là Pop. Bạn cần giúp gì?"
        else:
            return f"Chào {self.user_name}, tôi là Pop. Bạn cần tôi giúp gì?"
    
    def handle_name(self, text):
        """Xử lý khi người dùng nói tên."""
        # Trích xuất tên từ văn bản
        name_patterns = [
            r'tôi tên là\s+(\w+)',
            r'tên tôi là\s+(\w+)',
            r'gọi tôi là\s+(\w+)',
            r'kêu tôi là\s+(\w+)',
            r'tôi là\s+(\w+)',
            r'tên là\s+(\w+)',
            r'tôi\s+(\w+)',
        ]
        
        extracted_name = None
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_name = match.group(1).capitalize()
                break
        
        if extracted_name:
            return f"NAME:{extracted_name}"
        else:
            return "Xin lỗi, tôi không hiểu tên của bạn."
    
    def handle_help(self, text):
        """Xử lý yêu cầu trợ giúp."""
        help_text = """Tôi có thể giúp bạn:
- Thời gian: "mấy giờ", "hôm nay ngày mấy"
- Thời tiết: "thời tiết hà nội", "nhiệt độ"
- Điều khiển hệ thống: "âm lượng", "mức sử dụng cpu", "đặt độ sáng"
- Mở ứng dụng: "mở chrome", "mở zalo"
- Tìm kiếm: "tìm kiếm python", "tra cứu thông tin"
- Mở website: "mở google", "mở youtube"
- Tạm biệt: "tạm biệt", "kết thúc"""
        return help_text.strip()
    
    def handle_sleep(self, text):
        """Xử lý lệnh vào sleep mode."""
        return "sleep_intent_detected"
    
    def handle_goodbye(self, text):
        """Xử lý tạm biệt."""
        return "goodbye_intent_detected"
    
    def handle_unknown(self, text):
        """Xử lý ý định không xác định."""
        time.sleep(3)
        return "Xin lỗi, tôi không hiểu lệnh của bạn. Bạn có thể nói rõ hơn không?"
