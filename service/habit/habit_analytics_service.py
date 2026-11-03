"""
Habit Analytics Service - Business Logic Layer

Chịu trách nhiệm thống kê và phân tích dữ liệu thói quen
"""

from typing import Dict, List, Tuple


class HabitAnalyticsService:
    """Service for statistics and analytics"""
    
    def __init__(self, repository):
        self.repo = repository
    
    def get_habit_stats(self, user_id: int, days: int = 7) -> Dict:
        """Get habit statistics for user"""
        try:
            recent = self.repo.get_recent_app_usage(user_id, days)
            
            total_apps = len(recent)
            total_opens = sum(count for _, count, _ in recent)
            avg_opens = total_opens / total_apps if total_apps > 0 else 0
            
            return {
                'total_apps': total_apps,
                'total_opens': total_opens,
                'avg_opens_per_app': round(avg_opens, 1),
                'top_apps': recent[:5]
            }
        except Exception:
            return {}
    
    def get_database_stats(self) -> Dict:
        """Get overall database statistics"""
        try:
            return self.repo.get_table_counts()
        except Exception:
            return {}
    
    def get_workflows_stats(self, user_id: int) -> Dict:
        """Get workflow statistics for user"""
        try:
            workflows = self.repo.get_workflows(user_id, min_confidence=0.1, limit=10)
            
            if not workflows:
                return {
                    'total_workflows': 0,
                    'avg_executions': 0,
                    'max_executions': 0
                }
            
            total_workflows = len(workflows)
            executions = [wf[2] for wf in workflows]  # soLanThucHien
            avg_executions = sum(executions) / len(executions) if executions else 0
            max_executions = max(executions) if executions else 0
            
            return {
                'total_workflows': total_workflows,
                'avg_executions': round(avg_executions, 1),
                'max_executions': max_executions
            }
        except Exception:
            return {}
    
    def get_user_habits(self, user_id: int, min_confidence: float = 0.0) -> List[Dict]:
        """Get user's learned habits with details"""
        try:
            habits_raw = self.repo.get_user_habits_raw(user_id, min_confidence)
            
            habits = []
            for habit in habits_raw:
                habits.append({
                    'target': habit[0],
                    'type': habit[1], 
                    'time_bucket': habit[2],
                    'day_type': habit[3],
                    'frequency': habit[4],
                    'confidence': round(habit[5], 3),
                    'last_seen': habit[6]
                })
            
            return habits
        except Exception:
            return []
    
    def get_sequences(self, user_id: int, min_confidence: float = 0.0) -> List[Dict]:
        """Get user's learned app sequences"""
        try:
            # This would query app_sequences table
            # For now, return empty list
            return []
        except Exception:
            return []
    
    def get_workflows(self, user_id: int, min_confidence: float = 0.0) -> List[Dict]:
        """Get user's learned workflows"""
        try:
            workflows_raw = self.repo.get_workflows(user_id, min_confidence, limit=5)
            
            workflows = []
            for workflow in workflows_raw:
                workflows.append({
                    'name': workflow[0],
                    'app_chain': workflow[1],
                    'frequency': workflow[2],
                    'confidence': round(workflow[3], 3),
                    'last_executed': workflow[4]
                })
            
            return workflows
        except Exception:
            return []
