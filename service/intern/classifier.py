"""Intent classification module - Phân loại ý định người dùng."""

import re


class IntentClassifier:
    """Phân loại ý định từ văn bản đầu vào của người dùng."""
    
    # Time/Date intents
    TIME_KEYWORDS = [
        "mấy giờ", "mấy giời", "bao nhiêu giờ", "bây giờ là mấy giờ",
        "nay là ngày mấy", "hôm nay ngày", "thứ mấy", "hiện tại là ngày",
        "mấy ngày", "giờ mấy rồi"
    ]
    # System control intents
    SYSTEM_KEYWORDS = [
        "âm lượng", "đặt âm lượng", "chỉnh âm lượng", "mấy phần trăm âm lượng",
        "âm lượng bây giờ", "âm lượng bao nhiêu", "tắt tiếng", "bật tiếng",
        "im lặng", "tắt máy", "khởi động lại máy", "khóa máy", "mức sử dụng cpu",
        "cpu bao nhiêu", "xem cpu", "kiểm tra cpu", "mức sử dụng ram",
        "ram bao nhiêu", "xem ram", "kiểm tra ram", "dung lượng ổ đĩa",
        "ổ đĩa bao nhiêu", "xem ổ đĩa", "kiểm tra ổ đĩa", "đặt độ sáng",
        "chỉnh độ sáng", "độ sáng màn hình", "mấy phần trăm độ sáng",
        "tăng sáng", "giảm sáng", "sáng hơn", "tối hơn", "bật wifi",
        "tắt wifi", "wifi", "bật bluetooth", "tắt bluetooth", "bluetooth",
        "trạng thái hệ thống", "system status", "hiện trạng máy",
        "tình trạng máy", "tình trạng hệ thống",
        "nhiệt độ máy", "kiểm tra nhiệt độ","hệ thống"
    ]
    
    # Weather intents
    WEATHER_KEYWORDS = [
        "thời tiết", "thoi tiet", "nhiệt độ", "trời", "mưa", "nắng",
    ]
    
    # Name intents
    NAME_KEYWORDS = [
        "tôi là", "tên tôi là", "gọi tôi là", "tôi tên là",
        "tên là"
    ]
    
    # Greeting intents
    GREETING_KEYWORDS = [
        "xin chào", "chào bạn", "hello", "hi", "chào"
    ]
    
    # Search intents
    SEARCH_KEYWORDS = [
        "tìm kiếm", "tra cứu", "tìm trên google", "search google",
        "tìm kiếm trên google", "tìm", "search"
    ]
    
    # Open website intents
    WEBSITE_KEYWORDS = [
       "truy cập", "mở trang web", "google", "youtube", "facebook"
    ]
    
    # Open app intents
    APP_KEYWORDS = [
        "mở app", "mở ứng dụng", "chạy app",
        "khởi động app", "mở lại app",
    ]
    
    # Help intents
    HELP_KEYWORDS = [
        "hiệu lệnh", "lệnh", "giúp đỡ", "hướng dẫn", "tôi có thể làm gì",
        "các lệnh", "help", "định nghĩa"
    ]
    
    # Goodbye intents
    GOODBYE_KEYWORDS = [
        "tạm biệt",  "bye", "thôi", "tắt","tắt hệ thống", "kết thúc", "thoát", "exit", "quit"
    ]
    
    # Open file intents
    FILE_KEYWORDS = [
        "mở file", "mở tệp", "file vừa tải", "tệp vừa tải",
        "mở app vừa tải", "mở ứng dụng vừa tải", "mở file mới tải",
        "mở file download", "mở download"
    ]
    # Sleep mode intents
    SLEEP_KEYWORDS = [
      "ngủ đi", "sleep", "rest", "nghỉ ngơi","dừng",
        
    ]
    
    # Habit learning intents - Hỏi về thói quen
    HABIT_KEYWORDS = [
        "thói quen",  "gợi ý", "suggest", "recommend", "nên mở gì", "hôm nay nên", "lúc này thường"
    ]
    @classmethod
    def classify(cls, text):
        if not text:
            return "unknown"
            
        text_lower = text.lower()
        if cls._check_keywords(text_lower, cls.TIME_KEYWORDS):
            print(f"[INTERN] Detected: time | Text: '{text}'")
            return "time"
            
        if cls._check_keywords(text_lower, cls.NAME_KEYWORDS):
            print(f"[INTERN] Detected: name | Text: '{text}'")
            return "name"
            
        if cls._check_keywords(text_lower, cls.SYSTEM_KEYWORDS):
            print(f"[INTERN] Detected: system_control | Text: '{text}'")
            return "system_control"
            
        if cls._check_keywords(text_lower, cls.WEATHER_KEYWORDS):
            print(f"[INTERN] Detected: weather | Text: '{text}'")
            return "weather"
            
        if cls._check_keywords(text_lower, cls.GREETING_KEYWORDS):
            print(f"[INTERN] Detected: greeting | Text: '{text}'")
            return "greeting"
            
        if cls._check_keywords(text_lower, cls.SEARCH_KEYWORDS):
            print(f"[INTERN] Detected: search | Text: '{text}'")
            return "search"
            
        # FILE detection first (highest priority)
        if cls._check_keywords(text_lower, cls.FILE_KEYWORDS):
            print(f"[INTERN] Detected: open_file | Text: '{text}'")
            return "open_file"

        # WEBSITE detection second (medium priority)
        if cls._check_keywords(text_lower, cls.WEBSITE_KEYWORDS):
            print(f"[INTERN] Detected: open_website | Text: '{text}'")
            return "open_website"

        # APP detection last (lowest priority - fallback)
        app_match = cls._detect_open_app(text_lower)
        if app_match:
            print(f"[INTERN] Detected: open_app | App: {app_match}")
            return "open_app"
        
        if cls._check_keywords(text_lower, cls.HELP_KEYWORDS):
            print(f"[INTERN] Detected: help | Text: '{text}'")
            return "help"
            
        if cls._check_keywords(text_lower, cls.GOODBYE_KEYWORDS):
            print(f"[INTERN] Detected: goodbye | Text: '{text}'")
            return "goodbye"
            
        if cls._check_keywords(text_lower, cls.SLEEP_KEYWORDS):
            print(f"[INTERN] Detected: sleep | Text: '{text}'")
            return "sleep"
        
        if cls._check_keywords(text_lower, cls.HABIT_KEYWORDS):
            print(f"[INTERN] Detected: habit_query | Text: '{text}'")
            return "habit_query"
        
        print(f"[INTERN] Unknown intent | Text: '{text}'")
        return "unknown"
    
    @classmethod
    def _detect_open_app(cls, text):
        """Detect app name using regex patterns with blacklist filtering"""
        patterns = [
            r"mở (.+)",
            r"chạy (.+)",
            r"khởi động (.+)",
            r"run (.+)",
            r"start (.+)",
            r"launch (.+)"
        ]
        
        # Blacklist to avoid detecting websites as apps
        blacklist = [
            "google",
            "youtube", 
            "facebook",
            "website",
            "web",
            "http",
            "https",
            ".com",
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                app_name = match.group(1).strip()
                
                # Check if app_name contains blacklisted terms
                for blocked in blacklist:
                    if blocked.lower() in app_name.lower():
                        return None
                
                # Additional validation - app name should be reasonable length
                if len(app_name) > 0 and len(app_name) <= 50:
                    return app_name
        
        return None
    
    @classmethod
    def _check_keywords(cls, text, keywords):
        for keyword in keywords:
            if keyword in text:
                return True
        return False
