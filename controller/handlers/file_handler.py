"""File Handler - Xử lý mở file từ Downloads và các thư mục phổ biến."""

import os
import platform
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


class FileHandler:
    """Handler for opening files from Downloads and other directories."""
    
    def __init__(self, audio_service=None, view=None):
        self.audio_service = audio_service
        self.view = view
    
    def set_audio_service(self, audio_service):
        self.audio_service = audio_service
        
    def set_view(self, view):
        self.view = view
        
    def set_user_name(self, name):
        pass
    
    def _get_downloads_path(self):
        """Lấy đường dẫn thư mục Downloads."""
        return str(Path.home() / "Downloads")
    
    def _find_recent_files(self, directory, hours=24, limit=10):
        """Tìm các file gần đây trong thư mục."""
        if not os.path.exists(directory):
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_files = []
        
        try:
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if mod_time > cutoff_time:
                        recent_files.append((filename, filepath, mod_time))
        except Exception as e:
            print(f"Error listing directory: {e}")
            return []
        
        recent_files.sort(key=lambda x: x[2], reverse=True)
        return recent_files[:limit]
    
    def _search_file_by_name(self, directory, name_query):
        """Tìm file theo tên (fuzzy search)."""
        if not os.path.exists(directory):
            return None
        
        query_lower = name_query.lower()
        best_match = None
        best_score = 0
        
        try:
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    filename_lower = filename.lower()
                    if query_lower in filename_lower:
                        score = len(query_lower) / len(filename_lower)
                        if score > best_score:
                            best_score = score
                            best_match = filepath
        except Exception as e:
            print(f"Error searching file: {e}")
            
        return best_match
    
    def _open_file(self, filepath):
        """Mở file bằng ứng dụng mặc định."""
        if not os.path.exists(filepath):
            return f"Không tìm thấy file: {filepath}"
        
        try:
            if platform.system() == "Windows":
                os.startfile(filepath)
            elif platform.system() == "Darwin":
                subprocess.run(["open", filepath])
            else:
                subprocess.run(["xdg-open", filepath])
            return f"Đã mở file: {os.path.basename(filepath)}"
        except Exception as e:
            return f"Lỗi khi mở file: {e}"
    
    def handle_open_file(self, text):
        """Xử lý yêu cầu mở file."""
        downloads_path = self._get_downloads_path()
        text_lower = text.lower()
        
        keywords = ["mở", "file", "app", "ứng dụng", "vừa tải", "vừa tải về",
                    "mới tải", "download", "cho tôi", "hộ tôi", "đi"]
        
        file_name = text
        for keyword in keywords:
            file_name = file_name.replace(keyword, "").strip()
        
        if "vừa tải" in text_lower or "mới tải" in text_lower or "download" in text_lower:
            if "app" in text_lower or "ứng dụng" in text_lower:
                recent_files = self._find_recent_files(downloads_path, hours=48)
                exe_files = [f for f in recent_files if f[0].lower().endswith('.exe')]
                
                if exe_files:
                    return self._open_file(exe_files[0][1])
                else:
                    if recent_files:
                        return self._open_file(recent_files[0][1])
                    else:
                        return "Không tìm thấy file nào trong Downloads gần đây."
            else:
                recent_files = self._find_recent_files(downloads_path, hours=24, limit=1)
                if recent_files:
                    return self._open_file(recent_files[0][1])
                else:
                    return "Không tìm thấy file nào trong Downloads gần đây."
        
        if file_name and len(file_name) > 2:
            found_path = self._search_file_by_name(downloads_path, file_name)
            if found_path:
                return self._open_file(found_path)
            
            desktop_path = str(Path.home() / "Desktop")
            found_path = self._search_file_by_name(desktop_path, file_name)
            if found_path:
                return self._open_file(found_path)
            
            return f"Không tìm thấy file '{file_name}' trong Downloads hoặc Desktop."
        
        return "Bạn muốn mở file nào?"
