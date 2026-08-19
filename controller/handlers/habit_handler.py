#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Habit Handler - Xử lý thói quen và gợi ý cho user
"""

from datetime import datetime
from typing import Dict, List


class HabitHandler:
    """Handler cho các query liên quan đến thói quen"""
    
    def __init__(self, user_id: int = 1):
        self.user_id = user_id
        self.habit_tracker = None
        self._init_tracker()
    
    def _init_tracker(self):
        """Khởi tạo habit tracker - dùng singleton để tránh khởi tạo lại"""
        try:
            from controller.habit_tracker import get_habit_tracker
            self.habit_tracker = get_habit_tracker()
        except Exception as e:
            print(f"[HabitHandler] Error init tracker: {e}")
    
    def handle(self, text: str) -> str:
        """Xử lý câu hỏi về thói quen"""
        text_lower = text.lower()
        
        # Check xem user muốn biết thói quen cụ thể hay gợi ý
        if any(k in text_lower for k in ["gợi ý", "suggest", "nên", "recommend"]):
            return self._suggest_now()
        
        if any(k in text_lower for k in ["thói quen", "hay mở", "thường mở"]):
            return self._show_habits()
        
        # Default: gợi ý dựa trên thời gian hiện tại
        return self._suggest_now()
    
    def _suggest_now(self) -> str:
        """Gợi ý dựa trên thói quen và giờ hiện tại"""
        if not self.habit_tracker:
            return "Chưa có dữ liệu thói quen để gợi ý."
        
        suggestions = self.habit_tracker.get_suggestions(self.user_id)
        
        if not suggestions:
            current_hour = datetime.now().hour
            return f"Hiện tại là {current_hour}:00. Chưa có thói quen nào được ghi nhận vào giờ này."
        
        # Format gợi ý
        response = f"Dựa trên thói quen của bạn:\n"
        for sugg in suggestions[:3]:  # Tối đa 3 gợi ý
            response += f"• {sugg['message']}\n"
        
        # Hỏi user có muốn mở không
        top_sugg = suggestions[0]
        response += f"\nBạn có muốn mở {top_sugg['target']} không?"
        
        return response
    
    def _show_habits(self) -> str:
        """Hiển thị thống kê thói quen"""
        if not self.habit_tracker:
            return "Chưa có dữ liệu thói quen."
        
        stats = self.habit_tracker.get_habit_stats(self.user_id)
        
        if not stats or stats.get('total_patterns', 0) == 0:
            return "Chưa có thói quen nào được ghi nhận. Hãy tiếp tục sử dụng để tôi học!"
        
        response = f"📊 Thống kê thói quen của bạn:\n\n"
        response += f"• Tổng số patterns đã học: {stats.get('total_patterns', 0)}\n"
        response += f"• Số workflow đã học: {stats.get('total_workflows', 0)}\n"
        response += f"• Độ chính xác trung bình: {stats.get('avg_confidence', 0)*100:.0f}%\n"
        response += f"• Số lần tương tác: {stats.get('total_interactions', 0)}"
        
        return response
    
    def on_app_opened(self, app_name: str):
        """Gọi khi user mở app - để học thói quen"""
        if self.habit_tracker:
            self.habit_tracker.log_app_opened(self.user_id, app_name)
    
    def set_user_name(self, name: str):
        """Set user name - không làm gì với habit handler"""
        pass  # HabitHandler không cần username


# Test
if __name__ == "__main__":
    handler = HabitHandler(1)
    print(handler._show_habits())
