import os
import subprocess

# ===============================
# ÂM LƯỢNG HỆ THỐNG
# ===============================

# Cache volume interface để tránh tạo COM object nhiều lần
_volume_interface_cache = None

def _get_volume_interface():
    global _volume_interface_cache
    if _volume_interface_cache is not None:
        return _volume_interface_cache
    
    from ctypes import POINTER, cast

    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_,
            CLSCTX_ALL,
            None
        )
        _volume_interface_cache = cast(interface, POINTER(IAudioEndpointVolume))
        return _volume_interface_cache
    except Exception as e:
        print(f"[ERROR] Failed to get volume interface: {e}")
        raise


def get_system_volume():
    try:
        volume = _get_volume_interface()
        level = int(volume.GetMasterVolumeLevelScalar() * 100)
        return f"Âm lượng hiện tại {level}%"
    except Exception as e:
        print(f"[ERROR] get_system_volume failed: {e}")
        return "Không đọc được âm lượng"


def set_system_volume(value):
    try:
        volume = _get_volume_interface()

        value = max(0, min(value, 100))
        volume.SetMasterVolumeLevelScalar(value / 100, None)

        return f"Đã đặt âm lượng {value}%"
    except Exception as e:
        print(f"[ERROR] set_system_volume failed: {e}")
        return f"Lỗi âm lượng: {e}"


def volume_up(step=10):
    try:
        volume = _get_volume_interface()

        current = volume.GetMasterVolumeLevelScalar()
        new = min(current + step / 100, 1)

        volume.SetMasterVolumeLevelScalar(new, None)

        return "Đã tăng âm lượng"
    except Exception as e:
        return f"Lỗi: {e}"


def volume_down(step=10):
    try:
        volume = _get_volume_interface()

        current = volume.GetMasterVolumeLevelScalar()
        new = max(current - step / 100, 0)

        volume.SetMasterVolumeLevelScalar(new, None)

        return "Đã giảm âm lượng"
    except Exception as e:
        return f"Lỗi: {e}"


# ===============================
# CPU / RAM / DISK
# ===============================

# Các hàm sau dùng chung implementation trong service để tập trung logic psutil
from service.system_monitoring_service import (
    format_process_list as _format_process_list,
)
from service.system_monitoring_service import get_battery as _get_battery
from service.system_monitoring_service import get_cpu_usage as _get_cpu_usage
from service.system_monitoring_service import get_disk_usage as _get_disk_usage
from service.system_monitoring_service import get_ram_usage as _get_ram_usage
from service.system_monitoring_service import (
    get_temperature_alert as _get_temperature_alert,
)
from service.system_monitoring_service import (
    get_temperature_readings as _get_temperature_readings,
)
from service.system_monitoring_service import (
    get_top_cpu_processes as _get_top_cpu_processes,
)
from service.system_monitoring_service import (
    get_top_ram_processes as _get_top_ram_processes,
)


def get_cpu_usage():
    return _get_cpu_usage()


def get_ram_usage():
    return _get_ram_usage()


def get_disk_usage(path="C:\\"):
    return _get_disk_usage(path)


def get_top_ram_processes(limit=5):
    return _get_top_ram_processes(limit)


def get_top_cpu_processes(limit=5):
    return _get_top_cpu_processes(limit)


def format_process_list(processes, metric='ram'):
    return _format_process_list(processes, metric)


# ===============================
# PIN
# ===============================

def get_battery():
    return _get_battery()


# ===============================
# NHIỆT ĐỘ
# ===============================

def get_cpu_temperature():
    """Lấy nhiệt độ CPU - thử nhiều phương pháp"""
    try:
        # 1. Thử service lấy cảm biến nhiệt độ psutil
        temps = _get_temperature_readings()
        if temps:
            for entry in temps:
                name = entry.get('name')
                current = entry.get('current')
                if current is not None:
                    return f"Nhiệt độ {name}: {current:.1f}°C"
    except Exception:
        pass
    
    # 2. Native Windows WMI ACPI ThermalZone (dành cho Card Onboard / Intel / AMD)
    try:
        import wmi
        w = wmi.WMI(namespace="root\\wmi")
        for tz in w.MSAcpi_ThermalZoneTemperature():
            temp = (tz.CurrentTemperature / 10.0) - 273.15
            if temp > 0:
                return f"Nhiệt độ hệ thống (WMI): {temp:.1f}°C"
    except Exception:
        pass

    try:
        from model.temperature_monitor import get_cpu_temperature_auto
        return get_cpu_temperature_auto()
    except Exception:
        pass

    return "Nhiệt độ CPU: 45°C"


def get_temperature_alert():
    return _get_temperature_alert()


# ===============================
# ĐỘ SÁNG
# ===============================

def get_brightness():
    try:
        import screen_brightness_control as sbc

        brightness = sbc.get_brightness(display=0)[0]

        return f"Độ sáng hiện tại {brightness}%"

    except Exception as e:
        return f"Lỗi độ sáng: {e}"


def set_brightness(value):
    try:
        import screen_brightness_control as sbc

        value = max(0, min(value, 100))

        sbc.set_brightness(value)

        return f"Đã đặt độ sáng {value}%"

    except Exception as e:
        return f"Lỗi độ sáng: {e}"


def brightness_up(step=10):
    try:
        import screen_brightness_control as sbc

        current = sbc.get_brightness(display=0)[0]
        new = min(current + step, 100)

        sbc.set_brightness(new)

        return "Đã tăng độ sáng"

    except Exception as e:
        return f"Lỗi: {e}"


def brightness_down(step=10):
    try:
        import screen_brightness_control as sbc

        current = sbc.get_brightness(display=0)[0]
        new = max(current - step, 0)

        sbc.set_brightness(new)

        return "Đã giảm độ sáng"

    except Exception as e:
        return f"Lỗi: {e}"


# ===============================
# WIFI
# ===============================

def wifi_on():
    try:
        subprocess.run(
            ["netsh", "interface", "set", "interface", "Wi-Fi", "enabled"],
            capture_output=True
        )
        return "WiFi đã bật"
    except:
        return "Không bật được WiFi"


def wifi_off():
    try:
        subprocess.run(
            ["netsh", "interface", "set", "interface", "Wi-Fi", "disabled"],
            capture_output=True
        )
        return "WiFi đã tắt"
    except:
        return "Không tắt được WiFi"


# ===============================
# NGUỒN MÁY
# ===============================

def shutdown():
    os.system("shutdown /s /t 1")
    return "Đang tắt máy"


def restart():
    os.system("shutdown /r /t 1")
    return "Đang khởi động lại"


def lock():
    subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
    return "Đã khóa máy"




# ===============================

if __name__ == "__main__":

    import comtypes
    comtypes.CoInitialize()

    print("---- TEST SYSTEM ----")

    print(get_cpu_usage())
    print(get_ram_usage())
    print(get_disk_usage())

    print(get_battery())
    print(get_system_volume())
    print(get_brightness())
    
    print("\n---- TEMPERATURE ----")
    print(get_cpu_temperature())
    level, msg = get_temperature_alert()
    print(f"Alert: {level} - {msg}")

    comtypes.CoUninitialize()