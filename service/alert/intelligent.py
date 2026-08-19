"""
Intelligent Alert Service

Service for intelligent personalized alerts based on user behavior baselines

Unlike hard-coded thresholds (if cpu > 90: alert()), this service:
1. Learns each user's personal baselines in different contexts
2. Detects anomalies relative to personal baselines
3. Generates contextual alerts with severity based on deviation magnitude
"""

from datetime import datetime, timedelta
from typing import Dict, Optional

from .types import AlertContext, AlertSeverity, AlertType


class IntelligentAlertService:
    """Service for intelligent personalized alerts based on user behavior baselines"""
    
    def __init__(self, repository):
        self.repo = repository
        self.deviation_thresholds = {
            'minor': 1.0,      # 1 std dev -> info
            'moderate': 2.0,   # 2 std dev -> warning
            'severe': 3.0,     # 3 std dev -> critical
        }
    
    def _get_connection(self):
        """Get database connection"""
        return self.repo._get_connection()
    
    def _detect_app_context(self, user_id: int) -> str:
        """Detect current app context based on recent app usage"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get most recent apps in last 10 minutes
                ten_mins_ago = (datetime.now() - timedelta(minutes=10)).isoformat()
                cursor.execute("""
                    SELECT tenUngDung FROM app_usage_logs
                    WHERE maNguoiDung = ? AND thoiGianMo >= ?
                    ORDER BY thoiGianMo DESC
                    LIMIT 3
                """, (user_id, ten_mins_ago))
                
                recent_apps = [row[0] for row in cursor.fetchall()]
                
                # Classify context based on apps
                gaming_apps = ['steam', 'epic games', 'valorant', 'lol', 'fortnite', 'minecraft']
                coding_apps = ['vscode', 'visual studio', 'pycharm', 'intellij', 'windsurf', 'cursor']
                
                for app in recent_apps:
                    if app in gaming_apps:
                        return 'gaming'
                    if app in coding_apps:
                        return 'coding'
                
                return 'general'
                
        except Exception as e:
            print(f"[IntelligentAlertService] Error detecting app context: {e}")
            return 'general'
    
    def learn_baseline(self, user_id: int, metric_type: str, value: float,
                       app_context: str = 'global') -> None:
        """Learn/update user's personal baseline for a metric
        
        Args:
            user_id: User ID
            metric_type: 'cpu', 'ram', 'disk', 'temperature', 'battery'
            value: Current metric value
            app_context: Context like 'gaming', 'coding', 'idle'
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now()
                
                # Find existing baseline
                cursor.execute("""
                    SELECT id, gia_tri_trung_binh, do_lech_chuan, so_lan_do
                    FROM user_health_baselines
                    WHERE maNguoiDung = ? AND loai_metric = ? AND app_context = ?
                """, (user_id, metric_type, app_context))
                
                result = cursor.fetchone()
                
                if result:
                    baseline_id, old_mean, old_std, count = result
                    
                    # Update using Welford's online algorithm
                    new_count = count + 1
                    delta = value - old_mean
                    new_mean = old_mean + delta / new_count
                    
                    # Update std (variance)
                    if count > 1:
                        old_var = old_std ** 2
                        new_var = (old_var * (count - 1) + delta * (value - new_mean)) / (new_count - 1)
                        new_std = max(0.1, new_var ** 0.5)  # min 0.1 to avoid division by zero
                    else:
                        new_std = abs(value - new_mean) if value != new_mean else 0.1
                    
                    # Calculate normal max (mean + 2*std)
                    normal_max = new_mean + 2 * new_std
                    
                    cursor.execute("""
                        UPDATE user_health_baselines
                        SET gia_tri_trung_binh = ?, do_lech_chuan = ?, 
                            gia_tri_max_thuong = ?, so_lan_do = ?, lan_cap_nhat_cuoi = ?
                        WHERE id = ?
                    """, (new_mean, new_std, normal_max, new_count, now, baseline_id))
                    
                else:
                    # Create new baseline
                    cursor.execute("""
                        INSERT INTO user_health_baselines
                        (maNguoiDung, loai_metric, app_context, gia_tri_trung_binh, 
                         do_lech_chuan, gia_tri_max_thuong, so_lan_do, lan_cap_nhat_cuoi)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (user_id, metric_type, app_context, value, 0.1, value + 0.2, 1, now))
                
                conn.commit()
                
        except Exception as e:
            print(f"[IntelligentAlertService] Error learning baseline: {e}")
    
    def check_metric(self, user_id: int, metric_type: str, current_value: float,
                     app_context: str = None) -> Optional[Dict]:
        """Check if current metric value is abnormal for this user
        
        Returns alert dict if abnormal, None if normal
        """
        try:
            # Auto-detect context if not provided
            if not app_context:
                app_context = self._detect_app_context(user_id)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get baseline for this context, or fall back to global
                cursor.execute("""
                    SELECT gia_tri_trung_binh, do_lech_chuan, gia_tri_max_thuong, so_lan_do
                    FROM user_health_baselines
                    WHERE maNguoiDung = ? AND loai_metric = ? AND app_context = ?
                """, (user_id, metric_type, app_context))
                
                result = cursor.fetchone()
                
                # Fall back to global context if specific not found
                if not result and app_context != 'global':
                    cursor.execute("""
                        SELECT gia_tri_trung_binh, do_lech_chuan, gia_tri_max_thuong, so_lan_do
                        FROM user_health_baselines
                        WHERE maNguoiDung = ? AND loai_metric = ? AND app_context = 'global'
                    """, (user_id, metric_type))
                    result = cursor.fetchone()
                
                # Not enough data yet (need at least 5 samples)
                if not result or result[3] < 5:
                    # Store the value for future learning but don't alert
                    self.learn_baseline(user_id, metric_type, current_value, app_context)
                    return None
                
                mean, std, normal_max, count = result
                
                # Calculate deviation in standard deviations
                if std < 0.1:
                    std = 0.1  # Prevent division by zero
                deviation = (current_value - mean) / std
                
                # Determine severity
                if deviation < self.deviation_thresholds['minor']:
                    return None  # Normal
                elif deviation < self.deviation_thresholds['moderate']:
                    severity = 2  # Warning
                    severity_label = "⚠️"
                elif deviation < self.deviation_thresholds['severe']:
                    severity = 3  # Elevated
                    severity_label = "🔶"
                else:
                    severity = 4  # Critical
                    severity_label = "🚨"
                
                # Create personalized message
                context_label = app_context if app_context != 'general' else ''
                if metric_type == 'cpu':
                    msg = f"{severity_label} CPU {current_value:.1f}% cao bất thường"
                    if context_label:
                        msg += f" khi {context_label}"
                    msg += f" (thường bạn ~{mean:.1f}%)"
                elif metric_type == 'ram':
                    msg = f"{severity_label} RAM đầy {current_value:.1f}% - cao hơn bình thường (thường ~{mean:.1f}%)"
                elif metric_type == 'temperature':
                    msg = f"{severity_label} Nhiệt độ {current_value:.1f}°C - nóng hơn bình thường (thường ~{mean:.1f}°C)"
                elif metric_type == 'battery':
                    msg = f"{severity_label} Pin yếu {current_value:.1f}% - thường bạn không để pin thấp như vậy"
                else:
                    msg = f"{severity_label} {metric_type.upper()} bất thường: {current_value:.1f} (thường ~{mean:.1f})"
                
                # Record alert
                alert_id = self._record_alert(user_id, metric_type, severity, 
                                             current_value, mean, msg)
                
                return {
                    'alert_id': alert_id,
                    'type': f'{metric_type}_abnormal',
                    'severity': severity,
                    'severity_label': severity_label,
                    'current_value': current_value,
                    'user_baseline': mean,
                    'user_normal_max': normal_max,
                    'deviation_std': deviation,
                    'context': app_context,
                    'message': msg,
                    'is_personalized': True
                }
                
        except Exception as e:
            print(f"[IntelligentAlertService] Error checking metric: {e}")
            return None
    
    def _record_alert(self, user_id: int, alert_type: str, severity: int,
                     value: float, baseline: float, description: str) -> int:
        """Record alert to database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO intelligent_alerts
                    (maNguoiDung, loai_canh_bao, muc_do_nghiem_trong, 
                     gia_tri_do_duoc, gia_tri_baseline, mo_ta)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, alert_type, severity, value, baseline, description))
                
                conn.commit()
                return cursor.lastrowid
                
        except Exception:
            return 0
