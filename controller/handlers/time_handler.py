"""Time Handler - Xử lý thời gian."""

import datetime

from controller.handlers.base_handler import BaseHandler


class TimeHandler(BaseHandler):
    """Handler for time-related queries."""
    
    def handle(self, text):
        """Xử lý yêu cầu thời gian."""
        try:
            now = datetime.datetime.now()
            content = f"""Bây giờ là {now.hour} giờ {now.minute} phút
Hôm nay là ngày {now.day} tháng {now.month} năm {now.year}
Thứ hôm nay là {now.strftime('%A')}"""
            return self.speak_and_return(content, wait=5)
        except Exception:
            return "Xin lỗi, tôi không thể lấy thông tin thời gian ngay bây giờ."
