"""Weather Handler - Xử lý thời tiết."""

import datetime
import re

import requests

from controller.handlers.base_handler import BaseHandler
from service.conversation_service import ActionResult


class WeatherHandler(BaseHandler):
    """Handler for weather-related queries."""
    
    def handle(self, text, context=None):
        """Xử lý yêu cầu thời tiết.
        
        Args:
            text: User input text
            context: Optional ConversationContext with slots (e.g., location from follow-up)
        """
        try:
            # Handle None or empty text
            if not text or text == "None" or text.strip().lower() == "none":
                text = ""
            
            # 1. Extract from text first (user's explicit input takes priority)
            city = None
            # Pattern 1: "thời tiết ở/tại [city]" - MUST have ở or tại
            city_match = re.search(r"thời tiết\s+(?:ở|tại)\s+(\S.+)", text, re.IGNORECASE)
            if city_match:
                city = city_match.group(1).strip()
                # Remove time words that might be captured
                city = re.sub(r'\s*(hôm nay|ngày mai|tuần này|tháng này)\s*$', '', city, flags=re.IGNORECASE).strip()
            
            # 2. Fallback to context slot if no city in text (follow-up response)
            if not city and context:
                city = context.get_slot('location')
            
            # 3. Still no city → return ActionResult asking for location
            if not city:
                return ActionResult(
                    text='Bạn muốn xem thời tiết ở đâu ạ!',
                    needs_slot='location',
                    intent='weather'
                )
            
            # 4. Call weather API
            api_key = "fe8d8c65cf345889139d8e545f57819a"
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            data = requests.get(url).json()
            
            if data.get("cod") != "404":
                main = data["main"]
                sys = data["sys"]
                sun_rise = datetime.datetime.fromtimestamp(sys["sunrise"])
                sun_set = datetime.datetime.fromtimestamp(sys["sunset"])
                now = datetime.datetime.now()
                
                content = f"""Hôm nay là ngày {now.day} tháng {now.month} năm {now.year}
Mặt trời mọc vào {sun_rise.hour} giờ {sun_rise.minute} phút
Mặt trời lặn vào {sun_set.hour} giờ {sun_set.minute} phút
Nhiệt độ trung bình là {main['temp']} độ C
Áp suất không khí là {main['pressure']} hPa
Độ ẩm là {main['humidity']}%
Trời hôm nay {data['weather'][0]['description']}."""
                
                return ActionResult(text=content)
            return ActionResult(text='Không tìm thấy thành phố!')
                
        except Exception:
            return ActionResult(text='Xin lỗi, tôi không thể lấy thông tin thời tiết ngay bây giờ.')
