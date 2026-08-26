"""
Habit Recommendation Service - Business Logic Layer

Chịu trách nhiệm tạo gợi ý dựa trên thói quen người dùng
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional


class HabitRecommendationService:
    """Service for generating habit-based recommendations"""
    
    def __init__(self, repository, learning_service):
        self.repo = repository
        self.learning = learning_service
        self._cache = {}  # Cache suggestions per user_id với TTL ngắn
        self._cache_ttl = 30  # 30 giây cache
    
    def suggest_based_on_habits(self, user_id: int) -> List[Dict]:
        """Generate suggestions based on user's learned habits + burst habits.
        Có cache ngắn 30s để tránh query DB liên tục khi wake up."""
        try:
            # Check cache
            now = datetime.now()
            cache_key = f"suggest_{user_id}"
            if cache_key in self._cache:
                cached_time, cached_result = self._cache[cache_key]
                if (now - cached_time).total_seconds() < self._cache_ttl:
                    return cached_result
            
            days = 7
            suggestions = []
            seen_apps = set()

            # === PHASE 1: Check user_habits table (burst detection / learned habits) ===
            try:
                learned_habits = self.repo.get_user_habits_raw(user_id, min_confidence=0.5)
                for mucTieu, loaiThoiQuen, soLanGoiY, doTinCay, lanThayDoiCuoi in learned_habits:
                    if loaiThoiQuen == 'app_usage' and mucTieu not in seen_apps:
                        seen_apps.add(mucTieu)
                        last_dt = lanThayDoiCuoi if isinstance(lanThayDoiCuoi, datetime) else now
                        suggestions.append({
                            'type': 'habit',
                            'app': mucTieu,
                            'confidence': doTinCay,
                            'score': min(3, int(doTinCay * 5)),
                            'count': soLanGoiY,
                            'last_opened': last_dt,
                            'message': f'Thói quen dùng {mucTieu}: độ tin cậy {doTinCay:.0%}, {soLanGoiY} lần.',
                            'priority': 'high'
                        })
            except Exception:
                pass

            # === PHASE 2: Analyze app_usage_logs for frequent apps ===
            daily_usage = []

            if hasattr(self.repo, 'get_recent_app_usage_by_day'):
                try:
                    daily_usage = self.repo.get_recent_app_usage_by_day(user_id, days=days)
                except Exception:
                    daily_usage = []

            if daily_usage:
                activity_by_app = {}
                last_opened_by_app = {}

                for app_name, day, count, last_opened in daily_usage:
                    activity_by_app.setdefault(app_name, {})[day] = count
                    last_opened_dt = last_opened
                    if isinstance(last_opened, str):
                        try:
                            last_opened_dt = datetime.fromisoformat(last_opened)
                        except ValueError:
                            last_opened_dt = datetime.now()

                    if app_name not in last_opened_by_app or last_opened_dt > last_opened_by_app[app_name]:
                        last_opened_by_app[app_name] = last_opened_dt

                start_date = datetime.now().date() - timedelta(days=days - 1)
                window = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)]

                for app_name, day_counts in activity_by_app.items():
                    if app_name in seen_apps:
                        continue  # Đã có từ user_habits
                    score = 0
                    open_days = 0
                    for day_key in window:
                        if day_counts.get(day_key, 0) > 0:
                            score = min(3, score + 1)
                            open_days += 1
                        else:
                            score = max(0, score - 1)

                    if score > 0:
                        last_opened_dt = last_opened_by_app.get(app_name, datetime.now())
                        confidence = min(0.95, 0.2 + score * 0.22)
                        suggestions.append({
                            'type': 'habit',
                            'app': app_name,
                            'confidence': confidence,
                            'score': score,
                            'count': open_days,
                            'last_opened': last_opened_dt,
                            'message': f'Gợi ý dùng {app_name}: điểm thói quen {score}/3, lần cuối mở {last_opened_dt.strftime("%H:%M")}.',
                            'priority': 'high'
                        })
            else:
                recent = self.repo.get_recent_app_usage(user_id, days=days)
                for app_name, count, last_opened in recent:
                    if app_name in seen_apps:
                        continue
                    if count >= 3:  # Frequent app fallback
                        last_opened_dt = last_opened
                        if isinstance(last_opened, str):
                            try:
                                last_opened_dt = datetime.fromisoformat(last_opened)
                            except ValueError:
                                last_opened_dt = datetime.now()

                        days_ago = max(0, (datetime.now().date() - last_opened_dt.date()).days)
                        recency_bonus = max(0.0, (7 - days_ago) / 7)
                        score = count + recency_bonus
                        confidence = min(0.95, count / 10 + recency_bonus * 0.05)

                        suggestions.append({
                            'type': 'habit',
                            'app': app_name,
                            'confidence': confidence,
                            'score': score,
                            'count': count,
                            'last_opened': last_opened_dt,
                            'message': f'Bạn thường dùng {app_name} ({count} lần/tuần), lần cuối mở {last_opened_dt.strftime("%H:%M")}.',
                            'priority': 'high'
                        })

            suggestions.sort(key=lambda x: (-x['score'], -x['last_opened'].timestamp()))
            result = suggestions[:3]
            
            # Lưu cache
            self._cache[cache_key] = (now, result)
            
            return result
        except Exception:
            return []
    
    def suggest_based_on_sequence(self, user_id: int, current_app: str) -> List[Dict]:
        """Generate suggestions based on app sequence patterns"""
        try:
            # Get sequences starting from current app
            sequences = self.repo.get_sequences_from_app(user_id, current_app, min_confidence=0.3)
            
            suggestions = []
            for app_after, avg_time, frequency, confidence in sequences[:3]:
                if confidence >= 0.3:
                    suggestions.append({
                        'type': 'sequence',
                        'app': app_after,
                        'confidence': confidence,
                        'message': f'Thường sau {current_app} bạn mở {app_after} ({frequency} lần)',
                        'priority': 'medium',
                        'avg_time_between': avg_time
                    })
            
            return suggestions
            
        except Exception:
            return []
    
    def suggest_based_on_workflow(self, user_id: int) -> List[Dict]:
        """Generate suggestions based on workflow patterns"""
        try:
            # Get user's workflows
            workflows = self.repo.get_workflows(user_id, min_confidence=0.4, limit=3)
            
            suggestions = []
            for workflow_name, app_chain, frequency, confidence in workflows:
                if confidence >= 0.4:
                    apps = app_chain.split(' → ')
                    suggestions.append({
                        'type': 'workflow',
                        'workflow_name': workflow_name,
                        'app_chain': apps,
                        'confidence': confidence,
                        'message': f'Workflow: {workflow_name} ({frequency} lần)',
                        'priority': 'high'
                    })
            
            return suggestions
            
        except Exception:
            return []
    
    def get_all_suggestions(self, user_id: int, current_app: str = None) -> List[Dict]:
        """Get all types of suggestions"""
        suggestions = []
        
        # Habit-based suggestions
        habit_suggestions = self.suggest_based_on_habits(user_id)
        suggestions.extend(habit_suggestions)
        
        # Sequence-based suggestions
        if current_app:
            sequence_suggestions = self.suggest_based_on_sequence(user_id, current_app)
            suggestions.extend(sequence_suggestions)
        
        # Workflow-based suggestions
        workflow_suggestions = self.suggest_based_on_workflow(user_id)
        suggestions.extend(workflow_suggestions)
        
        # Sort by priority and confidence
        suggestions.sort(key=lambda x: (
            0 if x['priority'] == 'high' else 1 if x['priority'] == 'medium' else 2,
            -x['confidence']
        ))
        
        return suggestions[:5]  # Return top 5 suggestions
