"""App Handler - Xử lý mở website và ứng dụng."""

import os
import subprocess
import webbrowser
from datetime import datetime

from service.app_scanner import AppScanner
from service.intern import extract_app_name, extract_domain


def log_app_opened(app_name: str, user_name: str = "user", user_id: int = 1):
    """Log ứng dụng được mở qua analytics service và habit tracker"""
    actual_user_id = user_id
    if actual_user_id == 1 and user_name and user_name not in ("user", "bạn"):
        try:
            from model.Sql import SqlService
            actual_user_id = SqlService().db.get_or_create_user(user_name)
        except Exception:
            actual_user_id = user_id

    try:
        from service.analytics_service import get_analytics_service
        analytics = get_analytics_service(user_name or "user")
        analytics.log_app_opened(app_name)
    except Exception as e:
        print(f"[AppHandler] Analytics log error: {e}")
    
    # Log cho habit tracker (học thói quen)
    try:
        from controller.habit_tracker import get_habit_tracker
        habit_tracker = get_habit_tracker()
        habit_tracker.log_app_opened(actual_user_id, app_name)
        print(f"[HabitTracker] Logged: {app_name} at {datetime.now().strftime('%H:%M')}")
    except Exception as e:
        print(f"[AppHandler] Habit tracker error: {e}")


class AppHandler:
    """Handler for opening websites and applications."""
    
    def __init__(self, audio_service=None, view=None):
        self.audio_service = audio_service
        self.view = view
        self.app_scanner = AppScanner()
        self.login_username = None
        self.user_name = "bạn"
    
    def set_audio_service(self, audio_service):
        self.audio_service = audio_service
    
    def set_view(self, view):
        self.view = view
    
    def set_user_name(self, name):
        self.user_name = name

    def set_login_name(self, name):
        self.login_username = name
    
    def handle_website(self, text):
        """Xử lý mở website."""
        domain = extract_domain(text)
        
        if domain:
            webbrowser.open(domain)
            return f"Tôi đã mở trang web cho bạn."
        else:
            return "Tôi không thể xác định trang web bạn muốn mở."
    
    def handle_app(self, text):
        """Xử lý mở ứng dụng bằng cách tìm trong danh sách đã cài."""
        try:
            # Trích xuất tên app từ text
            app_name = extract_app_name(text)
            
            if not app_name:
                return "Tôi không hiểu bạn muốn mở ứng dụng nào."
            
            print(f"[AppHandler] Looking for app: '{app_name}'")
            
            # Tìm app trong danh sách đã cài (cache + Start Menu + Registry + deep scan)
            found_name, found_path = self.app_scanner.find_app(app_name)
            
            if found_path:
                print(f"[AppHandler] Found: '{found_name}' at '{found_path}'")
                self._open_app(found_name, found_path)
                
                # Log app mở
                actual_user = self.login_username or self.user_name or "user"
                log_app_opened(found_name, actual_user)
                
                return f"Tôi đã mở {found_name}."
            else:
                # Fuzzy matching - gợi ý các app gần giống
                fuzzy_results = self.app_scanner.find_app_fuzzy(app_name, max_results=3)
                if fuzzy_results:
                    suggestions = [name for name, _, _ in fuzzy_results]
                    suggestion_text = ", ".join(suggestions)
                    print(f"[AppHandler] Fuzzy suggestions for '{app_name}': {suggestions}")
                    
                    # Thử mở luôn kết quả đầu tiên nếu điểm cao (>70)
                    best_name, best_path, best_score = fuzzy_results[0]
                    if best_score >= 70:
                        print(f"[AppHandler] Auto-opening best match: '{best_name}' (score: {best_score})")
                        self._open_app(best_name, best_path)
                        actual_user = self.login_username or self.user_name or "user"
                        log_app_opened(best_name, actual_user)
                        return f"Tôi đã mở {best_name}."
                    
                    return f"Tôi không tìm thấy '{app_name}'. Có phải bạn muốn mở: {suggestion_text}?"
                
                # Fallback cuối: thử dùng Windows Start/Run command
                print(f"[AppHandler] Not found in cache, trying start command: '{app_name}'")
                try:
                    subprocess.Popen(["start", "", app_name], shell=True)
                    # Log app mở
                    actual_user = self.login_username or self.user_name or "user"
                    log_app_opened(app_name, actual_user)
                    return f"Tôi đang thử mở {app_name}."
                except Exception as e:
                    print(f"[AppHandler] Start command failed: {e}")
                    return f"Tôi không tìm thấy ứng dụng '{app_name}' trên máy của bạn. Bạn có thể thử lại với tên khác."
            
        except Exception as e:
            print(f"[AppHandler Error] {e}")
            return f"Lỗi khi mở ứng dụng: {str(e)}"
    
    def _open_app(self, app_name, app_path):
        """Mở ứng dụng từ đường dẫn tìm thấy."""
        try:
            # Nếu path là Update.exe, tìm file .exe chính trong cùng thư mục hoặc thư mục con
            if os.path.basename(app_path).lower() in ('update.exe', 'uninstall.exe', 'unins000.exe'):
                parent_dir = os.path.dirname(app_path)
                # Tìm file .exe khác trong cùng thư mục
                found_exe = None
                for item in os.listdir(parent_dir):
                    if item.lower().endswith('.exe') and item.lower() not in ('update.exe', 'uninstall.exe', 'unins000.exe'):
                        found_exe = os.path.join(parent_dir, item)
                        break
                # Nếu không tìm thấy, tìm trong thư mục con (vd: Discord app-1.0.xxx)
                if not found_exe:
                    for item in os.listdir(parent_dir):
                        item_path = os.path.join(parent_dir, item)
                        if os.path.isdir(item_path) and item.lower().startswith('app-'):
                            for sub_item in os.listdir(item_path):
                                if sub_item.lower().endswith('.exe') and sub_item.lower() not in ('update.exe', 'uninstall.exe', 'unins000.exe'):
                                    found_exe = os.path.join(item_path, sub_item)
                                    break
                            if found_exe:
                                break
                if found_exe:
                    app_path = found_exe
                    print(f"[AppHandler] Redirected from Update.exe to: {app_path}")
            
            if app_path.endswith('.lnk'):
                # Shortcut file
                os.startfile(app_path)
            elif app_path.endswith('.url'):
                # URL shortcut
                os.startfile(app_path)
            elif os.path.isdir(app_path):
                # Thư mục - tìm file .exe bên trong
                exe_found = False
                for item in os.listdir(app_path):
                    if item.endswith('.exe') and item.lower() not in ('update.exe', 'uninstall.exe', 'unins000.exe'):
                        exe_path = os.path.join(app_path, item)
                        subprocess.Popen([exe_path], shell=True)
                        exe_found = True
                        break
                if not exe_found:
                    # Không tìm thấy exe, thử mở thư mục
                    os.startfile(app_path)
            elif app_path.endswith('.exe'):
                # File exe trực tiếp
                subprocess.Popen([app_path], shell=True)
            else:
                # Fallback: thử start file
                os.startfile(app_path)
        except Exception as e:
            print(f"[AppHandler] Error opening {app_name}: {e}")
            # Thử dùng start command như fallback
            try:
                subprocess.Popen(["start", "", app_name], shell=True)
            except:
                pass
