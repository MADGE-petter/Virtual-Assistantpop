import os
import subprocess
import winreg


def find_application_like_search(app_name: str):
    """Tìm ứng dụng như Windows Search - không cần path chính xác."""
    app_name_lower = app_name.lower()
    found_paths = []
    
    # 1. Tìm trong Windows Registry
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                          r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall") as key:
            for i in range(1024):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    with winreg.OpenKey(key, subkey_name) as subkey:
                        try:
                            display_name = winreg.QueryValueEx(subkey, "DisplayName")[0].lower()
                            install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                            
                            if app_name_lower in display_name:
                                exe_path = _find_exe_in_folder(install_location)
                                if exe_path:
                                    found_paths.append(exe_path)
                        except (FileNotFoundError, OSError):
                            pass
                except OSError:
                    break
    except Exception:
        pass
    
    # 2. Tìm trong Program Files
    program_paths = [
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        r"C:\Users\TUAN NGUYEN\AppData\Local\Programs",
        r"C:\Users\TUAN NGUYEN\AppData\Roaming\Microsoft\Windows\Start Menu\Programs"
    ]
    
    for program_path in program_paths:
        if os.path.exists(program_path):
            for root, dirs, files in os.walk(program_path):
                # Tìm trong thư mục
                for dir_name in dirs:
                    if app_name_lower in dir_name.lower():
                        exe_path = _find_exe_in_folder(os.path.join(root, dir_name))
                        if exe_path and exe_path not in found_paths:
                            found_paths.append(exe_path)
                
                # Tìm file trực tiếp
                for file_name in files:
                    if (app_name_lower in file_name.lower() and 
                        file_name.endswith('.exe')):
                        full_path = os.path.join(root, file_name)
                        if full_path not in found_paths:
                            found_paths.append(full_path)
    
    # 3. Tìm trong PATH environment
    try:
        path_dirs = os.environ.get('PATH', '').split(os.pathsep)
        for path_dir in path_dirs:
            if os.path.exists(path_dir):
                for file_name in os.listdir(path_dir):
                    if (app_name_lower in file_name.lower() and 
                        file_name.endswith('.exe')):
                        found_paths.append(os.path.join(path_dir, file_name))
    except Exception:
        pass
    
    return found_paths


def _find_exe_in_folder(folder_path):
    """Tìm file .exe trong thư mục."""
    if not os.path.exists(folder_path):
        return None
        
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.exe'):
            return os.path.join(folder_path, file_name)
    return None


def open_application_like_search(app_name: str):
    """Mở ứng dụng như Windows Search - tìm tự động và mở app đầu tiên tìm thấy."""
    print(f"Searching for application: {app_name}")
    
    found_paths = find_application_like_search(app_name)
    
    if found_paths:
        app_path = found_paths[0]
        print(f"Found application at: {app_path}")
        
        try:
            if app_path.endswith('.lnk'):
                os.startfile(app_path)
            else:
                subprocess.Popen([app_path], shell=False)
            return f"Đã mở {app_name} thành công."
        except Exception as e:
            return f"Lỗi khi mở {app_name}: {e}"
    else:
        try:
            subprocess.Popen(["start", "search:", app_name], shell=True)
            return f"Đã mở tìm kiếm Windows cho {app_name}."
        except Exception:
            return f"Không tìm thấy {app_name}. Vui lòng kiểm tra tên ứng dụng."


def close_application(app_name: str):
    """Đóng một ứng dụng đang chạy - tùy biến như tìm kiếm."""
    app_name_lower = app_name.lower()
    
    try:
        import psutil

        # Tìm process - ưu tiên chính xác, sau đó fuzzy
        for proc in psutil.process_iter(['pid', 'name']):
            proc_name_lower = proc.info['name'].lower()
            
            # 1. Tìm chính xác với app_name + .exe
            if proc_name_lower == f"{app_name_lower}.exe":
                proc.terminate()
                return f"Đã đóng {app_name}."
            
            # 2. Tìm fuzzy với app_name trong process name
            elif app_name_lower in proc_name_lower:
                proc.terminate()
                return f"Đã đóng {app_name} (tìm thấy: {proc.info['name']})."
        
        return f"Không tìm thấy {app_name} đang chạy."
        
    except ImportError:
        return f"Thư viện psutil không được cài đặt. Không thể đóng ứng dụng."
    except Exception as e:
        return f"Lỗi khi đóng {app_name}: {e}"
