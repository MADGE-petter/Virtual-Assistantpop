"""App Scanner - Tìm kiếm ứng dụng đã cài đặt trên hệ thống."""

import os
import platform
import subprocess
import glob
from pathlib import Path


class AppScanner:
    """Quét và tìm kiếm ứng dụng đã cài đặt."""
    
    def __init__(self):
        self.app_cache = {}
        self._scan_all_sources()
    
    def _scan_all_sources(self):
        """Quét tất cả các nguồn để tìm ứng dụng."""
        if platform.system() == "Windows":
            self._scan_start_menu()
            self._scan_program_files_deep()
            self._scan_common_apps()
            self._scan_registry_uninstall()
        elif platform.system() == "Darwin":
            self._scan_mac_apps()
        else:
            self._scan_linux_apps()
    
    def _scan_start_menu(self):
        """Quét Start Menu - nơi chứa shortcut của hầu hết ứng dụng."""
        start_menu_dirs = [
            os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs'),
            os.path.join(os.environ.get('PROGRAMDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs'),
            os.path.join('C:', 'ProgramData', 'Microsoft', 'Windows', 'Start Menu', 'Programs'),
        ]
        
        for start_dir in start_menu_dirs:
            if not os.path.exists(start_dir):
                continue
            try:
                for root, dirs, files in os.walk(start_dir):
                    for item in files:
                        if item.endswith(('.lnk', '.exe', '.url')):
                            full_path = os.path.join(root, item)
                            app_name = os.path.splitext(item)[0].lower()
                            # Ưu tiên .exe và .lnk, tránh ghi đè bởi .url
                            if app_name not in self.app_cache or not full_path.endswith('.url'):
                                self.app_cache[app_name] = full_path
                    for item in dirs:
                        # Một số app có thư mục riêng trong Start Menu
                        dir_path = os.path.join(root, item)
                        item_lower = item.lower()
                        if item_lower not in self.app_cache:
                            self.app_cache[item_lower] = dir_path
            except Exception as e:
                print(f"[AppScanner] Lỗi quét Start Menu {start_dir}: {e}")
    
    # Các file .exe không nên dùng làm entry point
    _IGNORED_EXE_NAMES = {
        'update', 'uninstall', 'unins000', 'unins001', 'setup', 'install',
        'installer', 'crashpad_handler', 'crashreporter', 'crash_report',
        'cefsharp.browsersubprocess', 'elevation_service', 'notification_helper',
        'debug', 'cleanup', 'remover', 'patcher', 'launcher', 'wizard',
    }
    
    def _is_valid_entry_exe(self, exe_name: str, parent_dir: str) -> bool:
        """Kiểm tra xem .exe có phải là entry point hợp lệ không."""
        name_lower = exe_name.lower()
        
        # Loại bỏ các file không phải entry point
        for ignored in self._IGNORED_EXE_NAMES:
            if ignored in name_lower:
                return False
        
        return True
    
    def _pick_best_exe(self, exe_files: list, parent_dir: str) -> str:
        """Chọn file .exe tốt nhất từ danh sách - ưu tiên trùng tên thư mục cha."""
        if not exe_files:
            return None
        
        parent_name = os.path.basename(parent_dir).lower()
        
        # Ưu tiên 1: file .exe trùng tên thư mục cha
        for exe_path in exe_files:
            exe_name = os.path.splitext(os.path.basename(exe_path))[0].lower()
            if exe_name == parent_name:
                return exe_path
        
        # Ưu tiên 2: file .exe có chứa tên thư mục cha
        for exe_path in exe_files:
            exe_name = os.path.splitext(os.path.basename(exe_path))[0].lower()
            if parent_name in exe_name:
                return exe_path
        
        # Ưu tiên 3: file .exe đầu tiên hợp lệ
        for exe_path in exe_files:
            exe_name = os.path.splitext(os.path.basename(exe_path))[0].lower()
            if self._is_valid_entry_exe(exe_name, parent_dir):
                return exe_path
        
        # Fallback: file đầu tiên
        return exe_files[0]
    
    def _scan_program_files_deep(self):
        """Quét sâu các thư mục Program Files để tìm .exe."""
        program_dirs = []
        for env_key in ['PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA']:
            path = os.environ.get(env_key, '')
            if path and os.path.exists(path):
                program_dirs.append(path)
        
        # Thêm các thư mục phổ biến khác
        extra_dirs = [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs'),
            os.path.join(os.environ.get('APPDATA', ''), '..', 'Local', 'Programs'),
        ]
        for d in extra_dirs:
            if os.path.exists(d) and d not in program_dirs:
                program_dirs.append(d)
        
        for program_dir in program_dirs:
            try:
                # Chỉ quét 2 cấp để tránh quá lâu
                for root, dirs, files in os.walk(program_dir):
                    depth = root[len(program_dir):].count(os.sep)
                    if depth > 2:
                        dirs.clear()  # Không đi sâu hơn
                        continue
                    
                    # Gom tất cả .exe trong thư mục này
                    exe_files = []
                    for item in files:
                        if item.endswith('.exe'):
                            full_path = os.path.join(root, item)
                            exe_name = os.path.splitext(item)[0].lower()
                            if self._is_valid_entry_exe(exe_name, root):
                                exe_files.append(full_path)
                    
                    if exe_files:
                        # Chọn file .exe tốt nhất
                        best_exe = self._pick_best_exe(exe_files, root)
                        if best_exe:
                            app_name = os.path.splitext(os.path.basename(best_exe))[0].lower()
                            if app_name not in self.app_cache:
                                self.app_cache[app_name] = best_exe
            except Exception as e:
                print(f"[AppScanner] Lỗi quét {program_dir}: {e}")
    
    def _scan_registry_uninstall(self):
        """Quét Windows Registry để tìm ứng dụng đã cài đặt."""
        try:
            import winreg
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            ]
            
            for hkey, reg_path in registry_paths:
                try:
                    key = winreg.OpenKey(hkey, reg_path)
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            try:
                                display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                install_location = ""
                                try:
                                    install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                except:
                                    pass
                                
                                app_name_lower = display_name.lower().strip()
                                # Tìm file .exe trong thư mục cài đặt
                                if install_location and os.path.exists(install_location):
                                    exe_files = glob.glob(os.path.join(install_location, "*.exe"))
                                    if exe_files:
                                        self.app_cache[app_name_lower] = exe_files[0]
                                        continue
                                
                                # Lưu tên app để fallback tìm sau
                                if app_name_lower not in self.app_cache:
                                    self.app_cache[app_name_lower] = None  # Đánh dấu đã biết app này
                            except:
                                pass
                            finally:
                                winreg.CloseKey(subkey)
                        except:
                            pass
                    winreg.CloseKey(key)
                except Exception as e:
                    print(f"[AppScanner] Lỗi registry {reg_path}: {e}")
        except ImportError:
            print("[AppScanner] Không import được winreg")
        except Exception as e:
            print(f"[AppScanner] Lỗi quét registry: {e}")
    
    def _scan_common_apps(self):
        """Quét các ứng dụng phổ biến với đường dẫn cụ thể."""
        common_apps = {
            'chrome': ['Google\\Chrome\\Application\\chrome.exe'],
            'firefox': ['Mozilla Firefox\\firefox.exe'],
            'edge': ['Microsoft\\Edge\\Application\\msedge.exe'],
            'word': ['Microsoft Office\\root\\Office16\\WINWORD.EXE', 'Microsoft Office\\Office16\\WINWORD.EXE'],
            'excel': ['Microsoft Office\\root\\Office16\\EXCEL.EXE', 'Microsoft Office\\Office16\\EXCEL.EXE'],
            'powerpoint': ['Microsoft Office\\root\\Office16\\POWERPNT.EXE', 'Microsoft Office\\Office16\\POWERPNT.EXE'],
            'notepad': ['notepad.exe'],
            'calculator': ['calc.exe'],
            'zalo': ['Zalo\\ZaloPC\\ZaloPC.exe', 'Zalo\\Zalo.exe'],
            'code': ['Microsoft VS Code\\Code.exe'],
            'vscode': ['Microsoft VS Code\\Code.exe'],
            'spotify': ['Spotify\\Spotify.exe', 'WindowsApps\\SpotifyAB.SpotifyMusic_*\\Spotify.exe'],
            'discord': ['Discord\\app-*\\Discord.exe', 'Discord\\Discord.exe'],
            'telegram': ['Telegram Desktop\\Telegram.exe'],
            'skype': ['Microsoft\\Skype for Desktop\\Skype.exe'],
            'slack': ['Slack\\slack.exe'],
            'notion': ['Notion\\Notion.exe'],
            'obsidian': ['Obsidian\\Obsidian.exe'],
            'sublime': ['Sublime Text 3\\sublime_text.exe', 'Sublime Text\\sublime_text.exe'],
            'notepad++': ['Notepad++\\notepad++.exe'],
            '7zip': ['7-Zip\\7zFM.exe'],
            'winrar': ['WinRAR\\WinRAR.exe'],
            'vlc': ['VideoLAN\\VLC\\vlc.exe'],
            'obs': ['obs-studio\\bin\\64bit\\obs64.exe'],
            'steam': ['Steam\\steam.exe'],
            'epic': ['Epic Games\\Launcher\\Portal\\Binaries\\Win32\\EpicGamesLauncher.exe'],
            'messenger': ['Messenger\\Messenger.exe'],
            'capcut': ['CapCut\\CapCut.exe'],
            'canva': ['Canva\\Canva.exe'],
            'figma': ['Figma\\Figma.exe'],
            'postman': ['Postman\\Postman.exe'],
            'docker': ['Docker\\Docker\\Docker Desktop.exe'],
            'whatsapp': ['WhatsApp\\WhatsApp.exe'],
            'zoom': ['Zoom\\bin\\Zoom.exe', 'Zoom\\Zoom.exe'],
            'teams': ['Microsoft\\Teams\\current\\Teams.exe'],
            'onenote': ['Microsoft Office\\root\\Office16\\ONENOTE.EXE'],
            'outlook': ['Microsoft Office\\root\\Office16\\OUTLOOK.EXE'],
            'paint': ['mspaint.exe'],
            'cmd': ['cmd.exe'],
            'powershell': ['powershell.exe'],
            'task manager': ['taskmgr.exe'],
            'control panel': ['control.exe'],
            'file explorer': ['explorer.exe'],
            'snipping tool': ['SnippingTool.exe'],
            'camera': ['microsoft.windows.camera_*\\WindowsCamera.exe'],
            'photos': ['microsoft.windows.photos_*\\Microsoft.Photos.exe'],
        }
        
        program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
        program_files_x86 = os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
        local_appdata = os.environ.get('LOCALAPPDATA', '')
        windows_apps = os.path.join(program_files, 'WindowsApps')
        
        for app_name, paths in common_apps.items():
            if app_name in self.app_cache and self.app_cache[app_name] is not None:
                continue  # Đã tìm thấy từ nguồn khác
            
            for path in paths:
                # System command (không có đường dẫn)
                if '\\' not in path and '/' not in path:
                    self.app_cache[app_name] = path
                    break
                
                # Thử tất cả các thư mục
                for base_dir in [program_files, program_files_x86, local_appdata, windows_apps]:
                    if '*' in path:
                        # Hỗ trợ wildcard (cho WindowsApps)
                        pattern = os.path.join(base_dir, path)
                        matches = glob.glob(pattern)
                        if matches:
                            self.app_cache[app_name] = matches[0]
                            break
                    else:
                        full_path = os.path.join(base_dir, path)
                        if os.path.exists(full_path):
                            self.app_cache[app_name] = full_path
                            break
                else:
                    continue
                break
    
    def _scan_mac_apps(self):
        """Quét ứng dụng trên macOS."""
        app_dirs = ['/Applications', str(Path.home() / 'Applications')]
        for app_dir in app_dirs:
            if os.path.exists(app_dir):
                try:
                    for item in os.listdir(app_dir):
                        if item.endswith('.app'):
                            app_name = item.replace('.app', '').lower()
                            self.app_cache[app_name] = os.path.join(app_dir, item)
                except:
                    pass
    
    def _scan_linux_apps(self):
        """Quét ứng dụng trên Linux."""
        app_dirs = ['/usr/share/applications', str(Path.home() / '.local/share/applications')]
        for app_dir in app_dirs:
            if os.path.exists(app_dir):
                try:
                    for item in os.listdir(app_dir):
                        if item.endswith('.desktop'):
                            app_name = item.replace('.desktop', '').lower()
                            self.app_cache[app_name] = os.path.join(app_dir, item)
                except:
                    pass
    
    def _try_find_with_where(self, app_name):
        """Dùng lệnh 'where' của Windows để tìm ứng dụng."""
        try:
            result = subprocess.run(
                ['where', app_name],
                capture_output=True, text=True, timeout=5,
                shell=True
            )
            if result.returncode == 0 and result.stdout.strip():
                paths = result.stdout.strip().split('\n')
                for p in paths:
                    p = p.strip()
                    if p.lower().endswith('.exe') and os.path.exists(p):
                        return p
        except Exception:
            pass
        return None
    
    def _try_find_by_wildcard_exe(self, app_name):
        """Tìm file .exe có tên gần giống trong Program Files."""
        search_name = app_name.replace(' ', '*')
        program_dirs = [
            os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
            os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'),
            os.environ.get('LOCALAPPDATA', ''),
        ]
        
        for program_dir in program_dirs:
            if not os.path.exists(program_dir):
                continue
            try:
                pattern = os.path.join(program_dir, f"**/*{search_name}*.exe")
                matches = glob.glob(pattern, recursive=True)
                if matches:
                    return matches[0]
            except Exception:
                pass
        return None
    
    def find_app(self, app_name):
        """Tìm ứng dụng theo tên. Trả về (tên_app, đường_dẫn)."""
        app_name_lower = app_name.lower().strip()
        
        # 1. Tìm chính xác trong cache
        if app_name_lower in self.app_cache:
            cached = self.app_cache[app_name_lower]
            if cached is not None:
                return app_name_lower, cached
        
        # 2. Tìm gần đúng trong cache
        for cached_name, cached_path in self.app_cache.items():
            if cached_path is None:
                continue
            if app_name_lower in cached_name or cached_name in app_name_lower:
                return cached_name, cached_path
        
        # 3. Thử các biến thể tên
        variations = [
            app_name_lower,
            app_name_lower.replace(' ', ''),
            app_name_lower.replace('-', ''),
            app_name_lower.replace('_', ''),
            app_name_lower.replace('.', ''),
        ]
        
        for variant in variations:
            for cached_name, cached_path in self.app_cache.items():
                if cached_path is None:
                    continue
                if variant in cached_name:
                    return cached_name, cached_path
        
        # 4. Fallback: dùng Windows 'where' command
        found = self._try_find_with_where(app_name_lower)
        if found:
            self.app_cache[app_name_lower] = found
            return app_name_lower, found
        
        # 5. Fallback: tìm wildcard .exe
        found = self._try_find_by_wildcard_exe(app_name_lower)
        if found:
            self.app_cache[app_name_lower] = found
            return app_name_lower, found
        
        # 6. Thử mở trực tiếp bằng start command (fallback cuối)
        return None, None
    
    def find_app_fuzzy(self, app_name, max_results=5):
        """Tìm kiếm fuzzy matching - trả về danh sách (tên_app, đường_dẫn, điểm_số) sắp xếp theo độ liên quan."""
        app_name_lower = app_name.lower().strip()
        results = []
        
        for cached_name, cached_path in self.app_cache.items():
            if cached_path is None:
                continue
            
            score = self._fuzzy_score(app_name_lower, cached_name)
            if score > 0:
                results.append((cached_name, cached_path, score))
        
        # Sắp xếp theo điểm số giảm dần
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:max_results]
    
    def _fuzzy_score(self, query, target):
        """Tính điểm fuzzy matching giữa query và target.
        Trả về 0 nếu không liên quan, điểm càng cao càng khớp.
        """
        query = query.lower()
        target = target.lower()
        
        # Khớp chính xác
        if query == target:
            return 100
        
        # Target chứa query
        if query in target:
            # Ưu tiên query nằm ở đầu
            pos = target.find(query)
            return 80 - pos
        
        # Query chứa target
        if target in query:
            return 60
        
        # Đếm số ký tự khớp liên tiếp (subsequence matching)
        score = 0
        q_idx = 0
        consecutive = 0
        for t_char in target:
            if q_idx < len(query) and query[q_idx] == t_char:
                consecutive += 1
                score += consecutive * 2
                q_idx += 1
            else:
                consecutive = 0
        
        # Chỉ trả về nếu khớp được ít nhất 50% query
        if q_idx >= len(query) * 0.5:
            return score
        return 0
    
    def refresh_cache(self):
        """Làm mới cache - quét lại tất cả nguồn."""
        self.app_cache = {}
        self._scan_all_sources()
        print(f"[AppScanner] Cache refreshed: {len(self.app_cache)} apps found")
