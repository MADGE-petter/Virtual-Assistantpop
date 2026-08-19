"""Temperature Monitor - Tích hợp OpenHardwareMonitor/LibreHardwareMonitor"""

import os
import subprocess
import time
from typing import Optional, Tuple

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    psutil = None

from utils.paths import resource_path
class TemperatureMonitor:
    """Quản lý việc đọc nhiệt độ từ OHM/LHM"""

    @staticmethod
    def _ohm_paths():
        return [
            resource_path("tools", "OpenHardwareMonitor", "OpenHardwareMonitor.exe"),
            resource_path("tools", "LibreHardwareMonitor", "LibreHardwareMonitor.exe"),
        ]
    
    def __init__(self):
        self._ohm_process: Optional[subprocess.Popen] = None
        self._ohm_path: Optional[str] = None
        
    def find_ohm(self) -> Optional[str]:
        """Tìm đường dẫn đến OHM/LHM"""
        for path in self._ohm_paths():
            if os.path.exists(path):
                return path
        return None
    
    def is_ohm_running(self) -> bool:
        """Kiểm tra OHM/LHM đã chạy chưa"""
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name'].lower()
                if 'openhardwaremonitor' in name or 'librehardwaremonitor' in name:
                    return True
            except:
                pass
        return False
    
    def start_ohm(self, admin: bool = True) -> bool:
        """Khởi động OHM với quyền admin"""
        if self.is_ohm_running():
            print("[TemperatureMonitor] OHM/LHM đã đang chạy")
            return True
            
        ohm_path = self.find_ohm()
        if not ohm_path:
            print("[TemperatureMonitor] Không tìm thấy OHM/LHM")
            return False
            
        try:
            if admin:
                # Khởi động với quyền admin sử dụng runas
                # Hoặc dùng shell execute
                import ctypes
                from ctypes import wintypes

                # Kiểm tra đã là admin chưa
                if ctypes.windll.shell32.IsUserAnAdmin():
                    # Đã là admin, chạy bình thường
                    self._ohm_process = subprocess.Popen(
                        [ohm_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    # Chưa là admin, yêu cầu elevation
                    # Dùng ShellExecute để chạy với admin
                    SW_MINIMIZE = 6
                    result = ctypes.windll.shell32.ShellExecuteW(
                        None,  # hwnd
                        "runas",  # lpVerb - yêu cầu admin
                        ohm_path,  # lpFile
                        "",  # lpParameters
                        os.path.dirname(ohm_path),  # lpDirectory
                        SW_MINIMIZE  # nShowCmd - minimize
                    )
                    if result <= 32:  # Lỗi nếu <= 32
                        print(f"[TemperatureMonitor] Không thể khởi động OHM với admin (error: {result})")
                        # Thử chạy không admin
                        self._ohm_process = subprocess.Popen(
                            [ohm_path],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
            else:
                # Không cần admin
                self._ohm_process = subprocess.Popen(
                    [ohm_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
            # Đợi OHM khởi động và tạo WMI namespace
            print("[TemperatureMonitor] Đang đợi OHM khởi động...")
            time.sleep(20)  # Tăng lên 20s để WMI namespace kịp tạo
            
            # Kiểm tra lại
            if self.is_ohm_running():
                print("[TemperatureMonitor] OHM đã khởi động thành công")
                return True
            else:
                print("[TemperatureMonitor] OHM không khởi động được")
                return False
                
        except Exception as e:
            print(f"[TemperatureMonitor] Lỗi khởi động OHM: {e}")
            return False
    
    def stop_ohm(self):
        """Dừng OHM/LHM - kill tất cả process đang chạy"""
        # 1. Dừng process nếu bot tự khởi động
        if self._ohm_process:
            try:
                self._ohm_process.terminate()
                self._ohm_process.wait(timeout=3)
            except:
                pass
            self._ohm_process = None
        
        # 2. Kill tất cả process OHM/LHM đang chạy (trường hợp khởi động bằng admin)
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                name = proc.info['name'].lower()
                if 'openhardwaremonitor' in name or 'librehardwaremonitor' in name:
                    print(f"[TemperatureMonitor] Killing process {name} (PID: {proc.info['pid']})")
                    psutil.Process(proc.info['pid']).terminate()
            except:
                pass
    
    def _read_wmi_admin(self) -> Optional[float]:
        """Đọc nhiệt độ qua WMI với quyền admin - thử nhiều class"""
        import wmi

        # 1. Thử MSAcpi_ThermalZoneTemperature (root\wmi, cần admin)
        try:
            w = wmi.WMI(namespace="root\\wmi", privileges=["Security"])
            temps = w.MSAcpi_ThermalZoneTemperature()
            if temps:
                for t in temps:
                    raw = t.CurrentTemperature
                    celsius = (raw / 10.0) - 273.15
                    print(f"[WMI] MSAcpi_ThermalZone: {raw} -> {celsius:.1f}°C")
                    if 1 <= celsius <= 105:
                        return celsius
        except Exception as e:
            print(f"[WMI] MSAcpi error: {e}")
        
        # 2. Thử Win32_TemperatureProbe
        try:
            w = wmi.WMI()
            probes = w.Win32_TemperatureProbe()
            for p in probes:
                if hasattr(p, 'CurrentReading') and p.CurrentReading:
                    val = float(p.CurrentReading)
                    print(f"[WMI] TemperatureProbe: {val}°C")
                    if 1 <= val <= 105:
                        return val
        except Exception as e:
            print(f"[WMI] TemperatureProbe error: {e}")
        
        # 3. Thử CIM_Sensor (một số máy Dell/HP có)
        try:
            w = wmi.WMI(namespace="root\\cimv2")
            sensors = w.CIM_Sensor()
            temps = []
            for s in sensors:
                if hasattr(s, 'CurrentValue') and 'temp' in str(s.Name).lower():
                    try:
                        val = float(s.CurrentValue)
                        if 1 <= val <= 105:
                            temps.append(val)
                    except:
                        pass
            if temps:
                return max(temps)
        except:
            pass
        
        # 4. Thử Win32_PerfFormattedData_Counters_ThermalZoneInformation
        try:
            w = wmi.WMI()
            zones = w.Win32_PerfFormattedData_Counters_ThermalZoneInformation()
            valid = [z.Temperature for z in zones if hasattr(z, 'Temperature') and z.Temperature and 1 <= z.Temperature <= 105]
            if valid:
                return max(valid)
        except:
            pass
        
        return None
    
    def _read_nvidia_gpu_temp(self) -> Optional[float]:
        """Đọc nhiệt độ GPU NVIDIA qua NVML (nếu có)"""
        try:
            try:
                from pynvml import (
                    NVML_TEMPERATURE_GPU,
                    nvmlDeviceGetCount,
                    nvmlDeviceGetHandleByIndex,
                    nvmlDeviceGetTemperature,
                    nvmlInit,
                )
            except ImportError:
                # Fallback to nvidia-ml-py (new package name)
                from nvidia_ml_py import (
                    NVML_TEMPERATURE_GPU,
                    nvmlDeviceGetCount,
                    nvmlDeviceGetHandleByIndex,
                    nvmlDeviceGetTemperature,
                    nvmlInit,
                )
            nvmlInit()
            device_count = nvmlDeviceGetCount()
            if device_count > 0:
                handle = nvmlDeviceGetHandleByIndex(0)  # GPU đầu tiên
                temp = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)
                print(f"[NVML] GPU temperature: {temp}°C")
                if 1 <= temp <= 105:
                    return float(temp)
        except ImportError:
            pass  # Cả pynvml và nvidia-ml-py đều chưa cài
        except Exception as e:
            print(f"[NVML] Error: {e}")
        return None
    
    def _read_thermal_performance_counter(self) -> Optional[float]:
        """Đọc nhiệt độ từ Windows Performance Counters (giống Task Manager)"""
        return self._read_wmi_admin()
    
    def get_temperature(self, retry_count: int = 0) -> Tuple[bool, str]:
        """
        Lấy nhiệt độ CPU
        Args:
            retry_count: Số lần đã retry (tránh vòng lặp vô hạn)
        Returns: (success, message)
        """
        if retry_count > 4:
            return False, "Không đọc được nhiệt độ. Đã thử: WMI ThermalZone, OHM/LHM. Máy này có thể không hỗ trợ đọc nhiệt độ qua phần mềm."
        
        # Thử các phương pháp đọc nhiệt độ
        
        # 0. Thử đọc từ NVIDIA NVML (nhanh, chính xác cho GPU NVIDIA)
        gpu_temp = self._read_nvidia_gpu_temp()
        if gpu_temp:
            return True, f"Nhiệt độ GPU: {gpu_temp:.1f}°C"
        
        # 1. Thử đọc từ Windows WMI ThermalZone (giống Task Manager, không cần OHM)
        temp = self._read_thermal_performance_counter()
        if temp:
            return True, f"Nhiệt độ hệ thống: {temp:.1f}°C"
        
        # 1. Thử đọc từ OHM/LHM WMI
        try:
            import wmi

            # Thử LibreHardwareMonitor trước
            try:
                w = wmi.WMI(namespace="root\\LibreHardwareMonitor")
                sensors = w.Sensor()
                print(f"[TemperatureMonitor] LHM sensors found: {len(sensors)}")
                cpu_temps = []
                for sensor in sensors:
                    print(f"[TemperatureMonitor] LHM Sensor: {sensor.Name} - {sensor.SensorType} = {sensor.Value}")
                    if "Temperature" in str(sensor.SensorType):
                        sensor_name = str(sensor.Name).lower()
                        sensor_value = float(sensor.Value)
                        # Kiểm tra giá trị hợp lý (1-105°C, 0°C không hợp lý)
                        if not (1 <= sensor_value <= 105):
                            print(f"[TemperatureMonitor] Bỏ qua {sensor.Name}: {sensor_value}°C (ngoài phạm vi)")
                            continue
                        # Loại trừ GPU sensors
                        if 'gpu' in sensor_name or 'nvidia' in sensor_name or 'amd' in sensor_name or 'radeon' in sensor_name:
                            continue
                        # Tìm các sensor CPU temperature - ưu tiên chứa "cpu" hoặc "package"
                        if 'cpu' in sensor_name or 'package' in sensor_name or 'tctl' in sensor_name:
                            cpu_temps.append((sensor.Name, sensor_value))
                        # Nếu có "core" nhưng KHÔNG phải GPU, cũng thêm vào (core CPU)
                        elif 'core' in sensor_name or 'tdie' in sensor_name or 'processor' in sensor_name:
                            cpu_temps.append((sensor.Name, sensor_value))
                if cpu_temps:
                    # Lấy nhiệt độ cao nhất
                    hottest = max(cpu_temps, key=lambda x: x[1])
                    print(f"[TemperatureMonitor] Chọn nhiệt độ: {hottest[0]} = {hottest[1]:.1f}°C")
                    return True, f"Nhiệt độ {hottest[0]}: {hottest[1]:.1f}°C"
            except Exception as e:
                print(f"[TemperatureMonitor] LHM WMI error: {e}")
                pass
            
            # Thử OpenHardwareMonitor
            try:
                w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
                sensors = w.Sensor()
                print(f"[TemperatureMonitor] OHM sensors found: {len(sensors)}")
                cpu_temps = []
                for sensor in sensors:
                    print(f"[TemperatureMonitor] OHM Sensor: {sensor.Name} - {sensor.SensorType} = {sensor.Value}")
                    if "Temperature" in str(sensor.SensorType):
                        sensor_name = str(sensor.Name).lower()
                        sensor_value = float(sensor.Value)
                        # Kiểm tra giá trị hợp lý (1-105°C, 0°C không hợp lý)
                        if not (1 <= sensor_value <= 105):
                            print(f"[TemperatureMonitor] Bỏ qua {sensor.Name}: {sensor_value}°C (ngoài phạm vi)")
                            continue
                        # Loại trừ GPU sensors
                        if 'gpu' in sensor_name or 'nvidia' in sensor_name or 'amd' in sensor_name or 'radeon' in sensor_name:
                            continue
                        # Tìm các sensor CPU temperature - ưu tiên chứa "cpu" hoặc "package"
                        if 'cpu' in sensor_name or 'package' in sensor_name or 'tctl' in sensor_name:
                            cpu_temps.append((sensor.Name, sensor_value))
                        # Nếu có "core" nhưng KHÔNG phải GPU, cũng thêm vào (core CPU)
                        elif 'core' in sensor_name or 'tdie' in sensor_name or 'processor' in sensor_name:
                            cpu_temps.append((sensor.Name, sensor_value))
                if cpu_temps:
                    # Lấy nhiệt độ cao nhất
                    hottest = max(cpu_temps, key=lambda x: x[1])
                    print(f"[TemperatureMonitor] Chọn nhiệt độ: {hottest[0]} = {hottest[1]:.1f}°C")
                    return True, f"Nhiệt độ {hottest[0]}: {hottest[1]:.1f}°C"
                
                # Không có CPU temp, thử tìm GPU temp làm fallback
                gpu_temps = []
                for sensor in sensors:
                    if "Temperature" in str(sensor.SensorType):
                        sensor_name = str(sensor.Name).lower()
                        if 'gpu' in sensor_name or 'nvidia' in sensor_name:
                            try:
                                val = float(sensor.Value)
                                if 1 <= val <= 105:
                                    gpu_temps.append((sensor.Name, val))
                            except:
                                pass
                if gpu_temps:
                    hottest_gpu = max(gpu_temps, key=lambda x: x[1])
                    print(f"[TemperatureMonitor] Không có CPU temp, dùng GPU: {hottest_gpu[0]} = {hottest_gpu[1]:.1f}°C")
                    return True, f"Nhiệt độ GPU (không đọc được CPU): {hottest_gpu[1]:.1f}°C"
                    
            except Exception as e:
                print(f"[TemperatureMonitor] OHM WMI error: {e}")
                pass
                
        except ImportError as e:
            print(f"[TemperatureMonitor] WMI import error: {e}")
            pass
        
        # 2. Thử psutil (Linux/một số Windows)
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        if entry.current:
                            return True, f"Nhiệt độ {name}: {entry.current:.1f}°C"
        except:
            pass
        
        # Không đọc được - kiểm tra OHM có cài không
        ohm_path = self.find_ohm()
        if not ohm_path:
            tools_dir = resource_path("tools")
            message = f"Chưa tìm thấy OpenHardwareMonitor. Vui lòng:\n1. Copy folder OpenHardwareMonitor vào: {tools_dir}\n2. Hoặc chạy OpenHardwareMonitor trước rồi hỏi lại."
            print(f"[TemperatureMonitor] {message}")
            return False, message
        
        # OHM có nhưng chưa chạy → tự động khởi động
        if not self.is_ohm_running():
            print("[TemperatureMonitor] OHM đã cài nhưng chưa chạy, đang khởi động...")
            if self.start_ohm(admin=True):
                time.sleep(12)  # Đợi lâu hơn cho WMI namespace
                return self.get_temperature(retry_count + 1)
        
        # OHM đang chạy nhưng vẫn không đọc được → có thể WMI chưa sẵn sàng
        # Thử lại với delay tăng dần
        delay = 10 + (retry_count * 5)  # 10s, 15s, 20s, 25s, 30s
        print(f"[TemperatureMonitor] OHM đang chạy nhưng không đọc được WMI (retry {retry_count + 1}), thử lại sau {delay}s...")
        time.sleep(delay)
        return self.get_temperature(retry_count + 1)


# Singleton instance
_monitor = TemperatureMonitor()

def get_cpu_temperature_auto() -> str:
    """Hàm tiện ích để đọc nhiệt độ (tự động khởi động OHM nếu cần)"""
    success, message = _monitor.get_temperature()
    return message

def start_temperature_monitor() -> bool:
    """Khởi động OHM khi bot start"""
    return _monitor.start_ohm(admin=True)

def stop_temperature_monitor():
    """Dừng OHM khi bot stop"""
    _monitor.stop_ohm()
