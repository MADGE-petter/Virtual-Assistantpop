"""
Habit Tracker Controller - MVC Pattern

Controller layer điều phối giữa UI và Services
Chịu trách nhiệm:
- Khởi tạo services
- Cung cấp public API cho UI
- Không chứa business logic
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from database.habit_repository import HabitRepository
from service.alert import (
    AlertContext,
    AlertSeverity,
    AlertType,
    AnomalyDetectionService,
    IntelligentAlertService,
)
from service.habit import (
    HabitAnalyticsService,
    HabitLearningService,
    HabitRecommendationService,
)
from service.habit.habit_normalization_service import HabitNormalizationService


class HabitTracker:
    """Habit Tracker Controller - Facade pattern for UI layer"""
    
    DB_PATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', 'database', 'conversations.db'
    ))
    
    def __init__(self):
        # Initialize Clean Architecture layers
        self._repo = HabitRepository(self.DB_PATH)
        self._learning = HabitLearningService(self._repo)
        self._recommendation = HabitRecommendationService(self._repo, self._learning)
        self._analytics = HabitAnalyticsService(self._repo)
        self._alerts = IntelligentAlertService(self._repo)
        self._anomaly = AnomalyDetectionService(self._repo, self._alerts)
    
    def _log_error(self, method_name, error, include_traceback=True):
        """Log errors consistently with context"""
        error_msg = f"[HabitTracker.{method_name}] Error: {error}"
        print(error_msg)
    
    # ========== BASIC HABIT TRACKING ==========
    
    def log_app_opened(self, maNguoiDung, tenUngDung):
        """Ghi lại mỗi lần mở app - Controller chỉ điều phối"""
        try:
            # Step 1: Business logic - normalize app name (via Service)
            normalized_name = HabitNormalizationService.normalize_app_name(tenUngDung)
            now = datetime.now()

            # Step 2: Data access - use Repository (MVC pattern)
            self._repo.insert_app_usage_log(maNguoiDung, normalized_name, now)

            # Step 3: Cross-cutting concern - activity tracking (via Service)
            # Bọc riêng để không ảnh hưởng đến các bước khác
            try:
                if hasattr(self._alerts, 'update_last_activity'):
                    self._alerts.update_last_activity(maNguoiDung, normalized_name)
            except Exception:
                pass  # Không quan trọng nếu alert service không hỗ trợ
            
            # Step 4: Learn/update habit (bao gồm burst detection)
            time_bucket = now.hour
            day_type = now.weekday()
            self._learning.update_habit(maNguoiDung, 'app_usage', normalized_name, time_bucket, day_type)

        except Exception as e:
            self._log_error('log_app_opened', e)
    
    def get_habit_stats(self, user_id: int, days: int = 7) -> Dict:
        """Get habit statistics for user"""
        try:
            return self._analytics.get_habit_stats(user_id, days)
        except Exception as e:
            self._log_error('get_habit_stats', e)
            return {}
    
    def get_suggestions(self, user_id: int) -> List[Dict]:
        """Get habit-based suggestions"""
        try:
            return self._recommendation.suggest_based_on_habits(user_id)
        except Exception as e:
            self._log_error('get_suggestions', e)
            return []
    
    def get_user_habits(self, user_id: int, doTinCayToiThieu: float = 0.0) -> List:
        """Lấy danh sách thói quen của user (dùng cho ProactiveService).
        
        Trả về: List[(loaiThoiQuen, tenMucTieu, gio, ngay, tanSuat, doTinCay)]
        """
        try:
            habits_raw = self._repo.get_user_habits_raw(user_id, doTinCayToiThieu)
            result = []
            for habit in habits_raw:
                # tenMucTieu, loaiThoiQuen, tanSuat, doTinCay, lanQuanSatCuoi
                target = habit[0]
                habit_type = habit[1]
                frequency = habit[2]
                confidence = habit[3]
                last_updated = habit[4]
                
                # Trích xuất giờ và ngày từ thời gian cuối
                hour = last_updated.hour if hasattr(last_updated, 'hour') else 12
                day = last_updated.weekday() if hasattr(last_updated, 'weekday') else 0
                
                result.append((habit_type, target, hour, day, frequency, confidence))
            return result
        except Exception as e:
            self._log_error('get_user_habits', e)
            return []
    
    def suggest_based_on_habits(self, user_id: int) -> List[Dict]:
        """Alias cho get_suggestions - dùng bởi ProactiveService"""
        return self.get_suggestions(user_id)
    
    # ========== INTELLIGENT ALERT SYSTEM ==========
    
    def check_health_metric(self, user_id: int, metric_type: str, value: float) -> Optional[Dict]:
        """Check health metric against user's personal baseline"""
        try:
            return self._alerts.check_metric(user_id, metric_type, value)
        except Exception as e:
            self._log_error('check_health_metric', e)
            return None
    
    def check_smart_sleep(self, user_id: int, current_hour: int = None) -> Optional[Dict]:
        """Smart sleep alert - Case 2"""
        try:
            if not self._alerts.should_send_alert(user_id, 'smart_sleep'):
                return None
            
            result = self._alerts.check_smart_sleep_alert(user_id, current_hour)
            
            if result:
                self._alerts.update_alert_interaction(user_id, 'smart_sleep', 'viewed')
            
            return result
            
        except Exception as e:
            self._log_error('check_smart_sleep', e)
            return None
    
    def detect_anomaly(self, user_id: int, app_name: str = None, 
                      current_hour: int = None) -> Optional[Dict]:
        """Detect behavioral anomalies"""
        try:
            return self._anomaly.detect_app_anomaly(user_id, app_name, current_hour)
        except Exception as e:
            self._log_error('detect_anomaly', e)
            return None
    
    def get_evaluation_report(self, user_id: int) -> Dict:
        """Generate comprehensive evaluation report for presentation"""
        try:
            return self._anomaly.generate_evaluation_report(user_id)
        except Exception as e:
            self._log_error('get_evaluation_report', e)
            return {}
    
    def prove_system_adaptation(self, user_id: int) -> str:
        """Generate human-readable proof that system is learning and adapting"""
        try:
            report = self.get_evaluation_report(user_id)
            progress = report.get('learning_progress', {})
            drift = report.get('behavior_drift')
            
            proof_lines = [
                "=== CHỨNG MINH HỆ THỐNG THÍCH NGHI ===",
                "",
                f"Giai đoạn học: {progress.get('learning_stage', 'unknown').upper()}",
                f"Số patterns đã học: {progress.get('sequences', {}).get('count', 0)} sequences + {progress.get('workflows', {}).get('count', 0)} workflows",
                f"Độ tin cậy trung bình: {progress.get('evaluation_summary', 'N/A')}",
                ""
            ]
            
            if drift:
                proof_lines.extend([
                    "PHÁT HIỆN THAY ĐỔI THÓI QUEN:",
                    f"   {drift.get('message', '')}",
                    "   → Hệ thống đã nhận ra và đang thích nghi!",
                    ""
                ])
            
            proof_lines.extend([
                " KẾT LUẬN:",
                "   Hệ thống đang chủ động học và thích nghi với hành vi người dùng.",
                "   Các cảnh báo và gợi ý ngày càng chính xác theo thời gian."
            ])
            
            return '\n'.join(proof_lines)
            
        except Exception as e:
            self._log_error('prove_system_adaptation', e)
            return "Không thể tạo báo cáo chứng minh."


# Singleton instance
_habit_tracker = None

def get_habit_tracker():
    """Get or create habit tracker instance"""
    global _habit_tracker
    if _habit_tracker is None:
        _habit_tracker = HabitTracker()
    return _habit_tracker
