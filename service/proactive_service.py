#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proactive Service - Chủ động gợi ý dựa trên thói quen
Chạy nền, kiểm tra mỗi phút để tìm thói quen phù hợp với thời gian hiện tại
"""

import random
import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Optional


class ProactiveService:
    """
    Service chạy nền để chủ động gợi ý user dựa trên thói quen
    """
    
    def __init__(self, user_id: int = 1, suggestion_callback: Optional[Callable] = None):
        self.user_id = user_id
        self.suggestion_callback = suggestion_callback  # Hàm để phát âm thanh gợi ý
        self.habit_tracker = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.check_interval = 60  # Kiểm tra mỗi 60 giây
        
        # Tránh gợi ý trùng lặp trong 30 phút
        self.last_suggested = {}  # {habit_id: last_suggested_time}
        self.cooldown_minutes = 30
        
        self._init_tracker()
    
    def _init_tracker(self):
        """Khởi tạo habit tracker"""
        try:
            from controller.habit_tracker import get_habit_tracker
            self.habit_tracker = get_habit_tracker()
        except Exception as e:
            print(f"[ProactiveService] Error init tracker: {e}")
    
    def start(self):
        """Bắt đầu service chạy nền"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
            print("[ProactiveService] Started - monitoring habits every 60s")
    
    def stop(self):
        """Dừng service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("[ProactiveService] Stopped")
    
    def _monitor_loop(self):
        """Vòng lặp kiểm tra định kỳ"""
        while self.running:
            try:
                self._check_and_suggest()
            except Exception as e:
                print(f"[ProactiveService] Error in monitor loop: {e}")
            
            # Ngủ 60 giây
            time.sleep(self.check_interval)
    
    def _check_and_suggest(self):
        """Kiểm tra và gợi ý nếu phù hợp"""
        if not self.habit_tracker or not self.suggestion_callback:
            return
        
        now = datetime.now()
        gioHienTai = now.hour
        phutHienTai = now.minute
        ngayHienTai = now.weekday()
        
        # Lấy thói quen có độ tin cậy cao (>0.6)
        habits = self.habit_tracker.get_user_habits(self.user_id, doTinCayToiThieu=0.6)
        
        for habit in habits:
            loaiThoiQuen, tenMucTieu, gio, ngay, tanSuat, doTinCay = habit
            
            # Bỏ qua nếu đang cooldown
            khoaThoiQuen = f"{loaiThoiQuen}_{tenMucTieu}_{gio}_{ngay}"
            if self._is_in_cooldown(khoaThoiQuen):
                continue
            
            # Kiểm tra khung giờ (±5 phút)
            if ngay == ngayHienTai and self._is_time_match(gio, gioHienTai, phutHienTai):
                # Tạo gợi ý
                noiDungGoiY = self._tao_noi_dung_goi_y(tenMucTieu, gio, doTinCay)
                
                # Gọi callback để phát âm thanh
                if self.suggestion_callback:
                    self.suggestion_callback(noiDungGoiY)
                    
                # Ghi lại thời gian gợi ý
                self.last_suggested[khoaThoiQuen] = now
                
                print(f"[ProactiveService] Đã gợi ý: {tenMucTieu} lúc {now.strftime('%H:%M')}")
                
                # Chỉ gợi ý 1 thói quen mỗi lần check
                break
    
    def _is_time_match(self, habit_hour: int, current_hour: int, current_minute: int) -> bool:
        """Kiểm tra xem có đúng giờ không (±5 phút)"""
        # Chuyển về phút từ 00:00
        habit_time = habit_hour * 60
        current_time = current_hour * 60 + current_minute
        
        # Cho phép sai lệch ±5 phút
        diff = abs(habit_time - current_time)
        return diff <= 5
    
    def _is_in_cooldown(self, habit_key: str) -> bool:
        """Kiểm tra xem thói quen này đã được gợi ý gần đây chưa"""
        if habit_key not in self.last_suggested:
            return False
        
        last_time = self.last_suggested[habit_key]
        now = datetime.now()
        
        cooldown_passed = (now - last_time) > timedelta(minutes=self.cooldown_minutes)
        return not cooldown_passed
    
    def _create_suggestion(self, target: str, hour: int, confidence: float) -> str:
        """Tạo câu gợi ý tự nhiên"""
        # Mẫu câu gợi ý
        templates = [
            f"Chào bạn! Giờ này thường bạn hay mở {target}. Có muốn mở không?",
            f"Gợi ý nhẹ: {hour}:00 rồi, thường giờ này bạn dùng {target} đúng không?",
            f"Thói quen hàng ngày: Đã đến giờ mở {target}. Bạn có muốn mở luôn không?",
            f"Nhắc nhẹ: Đã {hour}:00, thường bạn làm việc với {target} lúc này.",
        ]
        
        # Chọn mẫu ngẫu nhiên hoặc theo confidence
        if confidence > 0.8:
            return templates[0]  # Chắc chắn cao -> gợi ý trực tiếp
        else:
            return random.choice(templates[1:])  # Confidence thấp hơn -> ngẫu nhiên
    
    def set_suggestion_callback(self, callback: Callable):
        """Thay đổi callback phát âm thanh"""
        self.suggestion_callback = callback
    
    def force_check_now(self) -> Optional[str]:
        """Kiểm tra ngay lập tức (cho test)"""
        if not self.habit_tracker:
            return None
        
        now = datetime.now()
        suggestions = self.habit_tracker.suggest_based_on_habits(self.user_id)
        
        if suggestions:
            top = suggestions[0]
            return f"[TEST] Gợi ý: {top['message']}"
        
        return f"[TEST] Không có gợi ý cho {now.strftime('%H:%M')}"
_proactive_service = None
def get_proactive_service(user_id: int = 1, callback: Optional[Callable] = None):
    """Get or create proactive service instance"""
    global _proactive_service
    if _proactive_service is None:
        _proactive_service = ProactiveService(user_id, callback)
    return _proactive_service
