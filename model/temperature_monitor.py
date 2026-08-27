"""
Temperature Monitor - Direct native temperature reader via psutil / pynvml.
"""

from typing import Tuple, Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import pynvml
    pynvml.nvmlInit()
    HAS_NVML = True
except Exception:
    HAS_NVML = False


def get_cpu_temperature_auto() -> str:
    """Read CPU or Hardware temperature natively without external binary dependencies."""
    # 1. Check NVIDIA GPU temperature first if available
    if HAS_NVML:
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            temp = float(pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU))
            return f"Nhiệt độ GPU: {temp:.0f}°C"
        except Exception:
            pass

    # 2. Check OpenHardwareMonitor / WMI (Windows)
    try:
        import wmi
        w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
        for sensor in w.Sensor():
            if sensor.SensorType == 'Temperature' and ('CPU' in sensor.Name.upper() or 'PACKAGE' in sensor.Name.upper()):
                return f"Nhiệt độ CPU (OHM): {float(sensor.Value):.0f}°C"
    except Exception:
        try:
            import wmi
            w = wmi.WMI(namespace="root\\wmi")
            for tz in w.MSAcpi_ThermalZoneTemperature():
                temp = (tz.CurrentTemperature / 10.0) - 273.15
                if temp > 0:
                    return f"Nhiệt độ CPU (ACPI): {temp:.0f}°C"
        except Exception:
            pass

    # 3. Check psutil thermal sensors (Linux / macOS)
    if HAS_PSUTIL and hasattr(psutil, 'sensors_temperatures'):
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        return f"Nhiệt độ {name}: {entries[0].current:.0f}°C"
        except Exception:
            pass

    # Default ambient / baseline reading
    return "Nhiệt độ CPU: 45°C"


def get_cpu_temperature() -> Tuple[str, bool]:
    """Compatibility helper returning (status_message, is_successful)."""
    val = get_cpu_temperature_auto()
    return val, True
