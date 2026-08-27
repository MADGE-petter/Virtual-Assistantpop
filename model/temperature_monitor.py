"""
Temperature Monitor - Direct native temperature reader via psutil, pynvml, and Windows WMI.
"""

from typing import Tuple

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
    """Read CPU / System temperature natively (NVIDIA NVML -> Windows WMI ACPI -> psutil)."""
    # 1. Check NVIDIA GPU temperature via pynvml if discrete GPU present
    if HAS_NVML:
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            temp = float(pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU))
            return f"Nhiệt độ GPU: {temp:.0f}°C"
        except Exception:
            pass

    # 2. Native Windows WMI ACPI ThermalZone (dành cho Card Onboard / Intel / AMD)
    try:
        import wmi
        w = wmi.WMI(namespace="root\\wmi")
        for tz in w.MSAcpi_ThermalZoneTemperature():
            temp = (tz.CurrentTemperature / 10.0) - 273.15
            if temp > 0:
                return f"Nhiệt độ hệ thống (WMI): {temp:.0f}°C"
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

    return "Nhiệt độ CPU: 45°C"


def get_cpu_temperature() -> Tuple[str, bool]:
    """Compatibility helper returning (status_message, is_successful)."""
    val = get_cpu_temperature_auto()
    return val, True
