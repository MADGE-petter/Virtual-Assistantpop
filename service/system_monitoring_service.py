"""
Dịch vụ giám sát hệ thống
Tập trung các chỉ số hệ thống dựa trên psutil và các tiện ích liệt kê tiến trình,
để các module khác gọi service này thay vì tự dùng psutil trực tiếp.
"""
from typing import Dict, List

try:
    import psutil
except Exception:
    psutil = None


def _psutil_available():
    return psutil is not None


def get_cpu_usage():
    """Trả về chuỗi mô tả mức sử dụng CPU."""
    if not _psutil_available():
        return "Không thể lấy CPU: psutil không khả dụng"
    cpu = psutil.cpu_percent(interval=1)
    return f"CPU đang sử dụng {cpu}%"


def get_cpu_percent():
    """Trả về phần trăm CPU dưới dạng số thực."""
    if not _psutil_available():
        return 0.0
    return psutil.cpu_percent(interval=0.5)


def get_ram_usage():
    if not _psutil_available():
        return "Không thể lấy RAM: psutil không khả dụng"
    ram = psutil.virtual_memory()
    return f"RAM sử dụng {ram.percent}%"


def get_ram_percent():
    if not _psutil_available():
        return 0.0
    return psutil.virtual_memory().percent


def get_temperature_readings():
    """Trả về danh sách các cảm biến nhiệt độ từ psutil."""
    if not _psutil_available():
        return []
    try:
        temps = psutil.sensors_temperatures()
        readings = []
        if not temps:
            return readings
        for name, entries in temps.items():
            for entry in entries:
                if entry.current is not None:
                    readings.append({'name': name, 'current': entry.current})
        return readings
    except Exception:
        return []


def get_disk_usage(path: str = "C:\\"):
    if not _psutil_available():
        return f"Không thể lấy ổ đĩa: psutil không khả dụng"
    try:
        disk = psutil.disk_usage(path)
        return f"Ổ đĩa {path} sử dụng {disk.percent}%"
    except Exception:
        return f"Không thể đọc ổ đĩa {path}"


def get_top_ram_processes(limit: int = 5) -> List[Dict]:
    if not _psutil_available():
        return []
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            mem_info = proc.info.get('memory_info')
            if mem_info:
                ram_mb = mem_info.rss / 1024 / 1024
                processes.append({'name': proc.info.get('name') or 'Unknown', 'pid': proc.info.get('pid'), 'ram_mb': ram_mb})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    processes.sort(key=lambda x: x.get('ram_mb', 0), reverse=True)
    return processes[:limit]


def get_top_cpu_processes(limit: int = 5) -> List[Dict]:
    if not _psutil_available():
        return []
    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            cpu_percent = proc.cpu_percent(interval=0.1)
            if cpu_percent and cpu_percent > 0:
                processes.append({'name': proc.info.get('name') or 'Unknown', 'pid': proc.info.get('pid'), 'cpu_percent': cpu_percent})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
    return processes[:limit]


def format_process_list(processes: List[Dict], metric: str = 'ram') -> str:
    if not processes:
        return "Không thể lấy thông tin processes"
    lines = []
    for i, proc in enumerate(processes, 1):
        if metric == 'ram':
            value = f"{proc.get('ram_mb', 0):.1f}MB"
        elif metric == 'cpu':
            value = f"{proc.get('cpu_percent', 0):.1f}%"
        else:
            value = "Unknown"
        lines.append(f"{i}. {proc.get('name')} ({value})")
    return "\n".join(lines)


def get_battery():
    if not _psutil_available():
        return "Không thể đọc pin: psutil không khả dụng"
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return "Máy không có pin"
        percent = battery.percent
        plugged = battery.power_plugged
        status = "Đang sạc" if plugged else "Đang dùng pin"
        return f"Pin {percent}% - {status}"
    except Exception:
        return "Không đọc được pin"


def get_temperature_alert():
    """Trả về tuple (mức cảnh báo, thông điệp) giống implementation trước."""
    if not _psutil_available():
        return None, "Không hỗ trợ đọc nhiệt độ"
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return None, "Không đọc được nhiệt độ"
        max_temp = 0
        hottest_sensor = ""
        for name, entries in temps.items():
            for entry in entries:
                if entry.current and entry.current > max_temp:
                    max_temp = entry.current
                    hottest_sensor = name
        if max_temp >= 90:
            return "danger", f"Nhiệt độ {hottest_sensor} rất cao: {max_temp}°C - Nguy hiểm!"
        elif max_temp >= 80:
            return "critical", f"Nhiệt độ {hottest_sensor} cao: {max_temp}°C - Cần làm mát!"
        elif max_temp >= 70:
            return "warning", f"Nhiệt độ {hottest_sensor}: {max_temp}°C - Đang nóng"
        else:
            return "normal", f"Nhiệt độ {hottest_sensor}: {max_temp}°C - Bình thường"
    except Exception:
        return None, "Không hỗ trợ đọc nhiệt độ"


def get_full_system_status() -> Dict:
    """Trả về dict tổng hợp với cpu, ram_percent, disk_info (list), battery (dict), temperature (float hoặc None)."""
    if not _psutil_available():
        return {}
    status = {}
    try:
        status['cpu'] = psutil.cpu_percent(interval=0.5)
        status['ram_percent'] = psutil.virtual_memory().percent
        disk_info = []
        for p in psutil.disk_partitions(all=False):
            try:
                d = psutil.disk_usage(p.mountpoint)
                disk_info.append({'mountpoint': p.mountpoint, 'percent': d.percent})
            except Exception:
                continue
        status['disk_info'] = disk_info
        battery = psutil.sensors_battery()
        if battery:
            status['battery'] = {'percent': battery.percent, 'power_plugged': battery.power_plugged}
        else:
            status['battery'] = None
        # nhiệt độ
        temp = None
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        if entry.current:
                            temp = max(temp or 0, entry.current)
        except Exception:
            temp = None
        status['temperature'] = temp
    except Exception:
        return {}
    return status
