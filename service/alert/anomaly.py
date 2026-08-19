"""
Anomaly Detection Service

Service for detecting behavioral anomalies and pattern changes

Key features for Evaluation/Khảo sát:
1. Anomaly Detection: Phát hiện hành vi bất thường
2. Pattern Drift: Phát hiện thay đổi thói quen
3. Learning Evaluation: Chứng minh hệ thống học và thích nghi
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Optional


class AnomalyDetectionService:
    """Service for detecting behavioral anomalies and pattern changes"""
    
    def __init__(self, repository, alert_service):
        self.repo = repository
        self.alerts = alert_service
        self.anomaly_threshold = 2.0  # 2 standard deviations
    
    def _get_connection(self):
        return self.repo._get_connection()
    
    def detect_app_anomaly(self, user_id: int, app_name: str, 
                          current_hour: int = None) -> Optional[Dict]:
        """Detect if user opens unusual app at unusual time
        
        Example: User never opens Blender at 3am → anomaly
        """
        try:
            if current_hour is None:
                current_hour = datetime.now().hour
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get historical usage of this app by hour
                cursor.execute("""
                    SELECT strftime('%H', thoiGianMo) as hour, COUNT(*) as count
                    FROM app_usage_logs
                    WHERE maNguoiDung = ? AND tenUngDung = ?
                      AND thoiGianMo >= datetime('now', '-30 days')
                    GROUP BY hour
                    ORDER BY count DESC
                """, (user_id, app_name))
                
                hour_distribution = {int(row[0]): row[1] for row in cursor.fetchall()}
                
                if not hour_distribution:
                    return None  # New app, no baseline
                
                total_uses = sum(hour_distribution.values())
                
                # Calculate expected probability for current hour
                current_hour_24 = current_hour
                expected_prob = hour_distribution.get(current_hour_24, 0) / total_uses if total_uses > 0 else 0
                
                # Calculate mean and std of usage probability across hours
                probs = [count / total_uses for count in hour_distribution.values()]
                mean_prob = sum(probs) / len(probs)
                std_prob = (sum((p - mean_prob) ** 2 for p in probs) / len(probs)) ** 0.5
                
                # Anomaly if current hour probability is significantly lower than mean
                if std_prob > 0 and expected_prob < mean_prob - self.anomaly_threshold * std_prob:
                    # This is unusual time for this app
                    usual_hours = [h for h, c in hour_distribution.items() if c == max(hour_distribution.values())]
                    
                    return {
                        'type': 'unusual_app_time',
                        'severity': 2 if expected_prob == 0 else 3,
                        'app': app_name,
                        'current_hour': current_hour,
                        'usual_hours': usual_hours,
                        'expected_frequency': expected_prob,
                        'mean_frequency': mean_prob,
                        'message': f" {app_name} lúc {current_hour}h? Thường bạn mở app này lúc {', '.join(f'{h}h' for h in usual_hours[:2])}.",
                        'is_anomaly': True
                    }
                
                return None
                
        except Exception as e:
            print(f"[AnomalyDetectionService] Error detecting app anomaly: {e}")
            return None
    
    def detect_behavior_drift(self, user_id: int, days_window: int = 7) -> Optional[Dict]:
        """Detect if user's behavior has changed significantly
        
        Example: User used to use Chrome daily, now using VSCode more
        → Pattern drift detected
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Compare recent vs older period
                recent_start = (datetime.now() - timedelta(days=days_window)).strftime('%Y-%m-%d')
                older_start = (datetime.now() - timedelta(days=days_window * 2)).strftime('%Y-%m-%d')
                older_end = recent_start
                
                # Get top apps in recent period
                cursor.execute("""
                    SELECT tenUngDung, COUNT(*) as count
                    FROM app_usage_logs
                    WHERE maNguoiDung = ? AND DATE(thoiGianMo) >= ?
                    GROUP BY tenUngDung
                    ORDER BY count DESC
                    LIMIT 5
                """, (user_id, recent_start))
                
                recent_top = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Get top apps in older period
                cursor.execute("""
                    SELECT tenUngDung, COUNT(*) as count
                    FROM app_usage_logs
                    WHERE maNguoiDung = ? 
                      AND DATE(thoiGianMo) >= ? AND DATE(thoiGianMo) < ?
                    GROUP BY tenUngDung
                    ORDER BY count DESC
                    LIMIT 5
                """, (user_id, older_start, older_end))
                
                older_top = {row[0]: row[1] for row in cursor.fetchall()}
                
                if not recent_top or not older_top:
                    return None
                
                # Calculate Jaccard similarity between app sets
                recent_set = set(recent_top.keys())
                older_set = set(older_top.keys())
                
                if not older_set:
                    return None
                
                # Check for new dominant apps
                new_dominant = []
                for app, count in recent_top.items():
                    if app not in older_top or recent_top[app] > older_top.get(app, 0) * 2:
                        new_dominant.append((app, count))
                
                # Check for abandoned apps
                abandoned = []
                for app, count in older_top.items():
                    if app not in recent_top or recent_top.get(app, 0) < count * 0.3:
                        abandoned.append((app, count))
                
                if new_dominant or abandoned:
                    drift_significance = len(new_dominant) + len(abandoned)
                    
                    messages = []
                    if new_dominant:
                        apps_str = ', '.join([a[0] for a in new_dominant[:2]])
                        messages.append(f"dùng {apps_str} nhiều hơn")
                    if abandoned:
                        apps_str = ', '.join([a[0] for a in abandoned[:2]])
                        messages.append(f"ít dùng {apps_str}")
                    
                    return {
                        'type': 'behavior_drift',
                        'severity': min(3, drift_significance),
                        'new_dominant_apps': [a[0] for a in new_dominant],
                        'abandoned_apps': [a[0] for a in abandoned],
                        'message': f" Thói quen thay đổi: bạn đang {' và '.join(messages)}.",
                        'is_drift': True,
                        'recent_top': list(recent_top.keys()),
                        'older_top': list(older_top.keys())
                    }
                
                return None
                
        except Exception as e:
            print(f"[AnomalyDetectionService] Error detecting drift: {e}")
            return None
    
    def evaluate_learning_progress(self, user_id: int) -> Dict:
        """Evaluate how well system has learned user behavior
        
        Key metrics for Evaluation/Khảo sát:
        - Confidence trends over time
        - Pattern stability
        - Prediction accuracy indicators
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get habit confidence evolution
                cursor.execute("""
                    SELECT DATE(thoiGianTao) as date, AVG(doTinCay) as avg_conf, COUNT(*) as count
                    FROM user_habits
                    WHERE maNguoiDung = ?
                    GROUP BY date
                    ORDER BY date
                    LIMIT 30
                """, (user_id,))
                
                confidence_trend = []
                for row in cursor.fetchall():
                    confidence_trend.append({
                        'date': row[0],
                        'avg_confidence': round(row[1], 3),
                        'habit_count': row[2]
                    })
                
                # Get sequence learning progress
                cursor.execute("""
                    SELECT AVG(doTinCay) as avg_conf, MAX(soLanGap) as max_freq, COUNT(*) as total
                    FROM app_sequences
                    WHERE maNguoiDung = ?
                """, (user_id,))
                
                seq_result = cursor.fetchone()
                
                # Get workflow learning progress
                cursor.execute("""
                    SELECT AVG(doTinCay) as avg_conf, COUNT(*) as total
                    FROM workflows
                    WHERE maNguoiDung = ?
                """, (user_id,))
                
                wf_result = cursor.fetchone()
                
                # Get baseline learning progress
                cursor.execute("""
                    SELECT loai_metric, AVG(so_lan_do) as avg_samples
                    FROM user_health_baselines
                    WHERE maNguoiDung = ?
                    GROUP BY loai_metric
                """, (user_id,))
                
                baseline_progress = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Calculate learning stage
                total_patterns = (seq_result[2] if seq_result else 0) + (wf_result[1] if wf_result else 0)
                avg_confidence = ((seq_result[0] if seq_result else 0) + (wf_result[0] if wf_result else 0)) / 2
                
                if total_patterns < 5:
                    learning_stage = 'initial'
                elif avg_confidence < 0.3:
                    learning_stage = 'exploring'
                elif avg_confidence < 0.6:
                    learning_stage = 'learning'
                else:
                    learning_stage = 'mature'
                
                return {
                    'learning_stage': learning_stage,
                    'confidence_trend': confidence_trend,
                    'sequences': {
                        'count': seq_result[2] if seq_result else 0,
                        'avg_confidence': round(seq_result[0], 3) if seq_result and seq_result[0] else 0,
                        'max_frequency': seq_result[1] if seq_result else 0
                    },
                    'workflows': {
                        'count': wf_result[1] if wf_result else 0,
                        'avg_confidence': round(wf_result[0], 3) if wf_result and wf_result[0] else 0
                    },
                    'baselines_samples': baseline_progress,
                    'evaluation_summary': f"Đã học {total_patterns} patterns, confidence trung bình {avg_confidence:.2f}"
                }
                
        except Exception as e:
            print(f"[AnomalyDetectionService] Error evaluating learning: {e}")
            return {'learning_stage': 'unknown'}
    
    def generate_evaluation_report(self, user_id: int) -> Dict:
        """Generate comprehensive evaluation report for demo/presentation
        
        Perfect for showing teachers how system learns and adapts!
        """
        try:
            # Get all evaluation data
            learning_progress = self.evaluate_learning_progress(user_id)
            drift = self.detect_behavior_drift(user_id)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get day-by-day app usage evolution
                cursor.execute("""
                    SELECT DATE(thoiGianMo) as date, tenUngDung, COUNT(*) as count
                    FROM app_usage_logs
                    WHERE maNguoiDung = ? AND thoiGianMo >= datetime('now', '-14 days')
                    GROUP BY date, tenUngDung
                    ORDER BY date, count DESC
                """, (user_id,))
                
                daily_usage = defaultdict(lambda: defaultdict(int))
                for row in cursor.fetchall():
                    daily_usage[row[0]][row[1]] = row[2]
                
                # Find trend changes
                trend_changes = []
                dates = sorted(daily_usage.keys())
                
                if len(dates) >= 3:
                    # Compare first half vs second half
                    mid = len(dates) // 2
                    first_half_apps = set()
                    second_half_apps = set()
                    
                    for d in dates[:mid]:
                        first_half_apps.update(daily_usage[d].keys())
                    for d in dates[mid:]:
                        second_half_apps.update(daily_usage[d].keys())
                    
                    new_apps = second_half_apps - first_half_apps
                    if new_apps:
                        trend_changes.append(f"Ngày {dates[0]} đến {dates[mid-1]}: {', '.join(list(first_half_apps)[:3])}")
                        trend_changes.append(f"Ngày {dates[mid]} đến {dates[-1]}: {', '.join(list(second_half_apps)[:3])}")
                
                return {
                    'learning_progress': learning_progress,
                    'behavior_drift': drift,
                    'daily_usage_evolution': dict(daily_usage),
                    'trend_summary': trend_changes,
                    'system_adaptation_proof': {
                        'patterns_learned': learning_progress.get('sequences', {}).get('count', 0) + 
                                          learning_progress.get('workflows', {}).get('count', 0),
                        'confidence_growth': len(learning_progress.get('confidence_trend', [])) > 5,
                        'personalization_level': learning_progress.get('learning_stage', 'initial')
                    }
                }
                
        except Exception as e:
            print(f"[AnomalyDetectionService] Error generating report: {e}")
            return {}
