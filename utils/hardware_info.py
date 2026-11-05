"""Hardware Information & Diagnostics Utility.

Provides centralized hardware profiling (CPU, RAM, GPU, Disk, OS)
used across Settings tabs (About tab, Quantization dialog, Telemetry).
Ensures safe driver initialization/shutdown (pynvml) and non-blocking fallbacks.
"""
import platform
import psutil
from typing import Dict, Any


def get_system_hardware_info() -> Dict[str, Any]:
    """Retrieve comprehensive system hardware specifications safely."""
    # 1. RAM info
    mem = psutil.virtual_memory()
    total_ram_gb = mem.total / (1024 ** 3)
    avail_ram_gb = mem.available / (1024 ** 3)

    # 2. OS & CPU info
    os_info = f"{platform.system()} {platform.release()} ({platform.architecture()[0]})"
    cpu_threads = psutil.cpu_count(logical=True) or 1
    cpu_name = platform.processor() or "Intel / AMD Processor"
    cpu_info = f"{cpu_name} ({cpu_threads} Threads)"

    # 3. Disk info
    try:
        drive_path = 'C:\\' if platform.system() == "Windows" else '/'
        disk = psutil.disk_usage(drive_path)
        disk_total = round(disk.total / (1024 ** 3))
        disk_free = round(disk.free / (1024 ** 3))
        disk_info = f"{disk_free} GB trống / {disk_total} GB (Ổ đĩa {drive_path[:2]})"
    except Exception:
        disk_info = "Không thể đọc dữ liệu ổ đĩa"

    # 4. GPU Detection (NVIDIA NVML -> WMI -> Generic Onboard)
    gpu_info = {
        "has_discrete_gpu": False,
        "gpu_name": "Card Onboard (Intel / AMD)",
        "vram_gb": 0.0,
        "display_str": "Intel / AMD Graphics"
    }

    pynvml_initialized = False
    try:
        import warnings
        warnings.filterwarnings('ignore', message=r'.*pynvml.*')
        import pynvml
        pynvml.nvmlInit()
        pynvml_initialized = True

        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        gpu_name = pynvml.nvmlDeviceGetName(handle)
        if isinstance(gpu_name, bytes):
            gpu_name = gpu_name.decode('utf-8', errors='ignore')
        else:
            gpu_name = str(gpu_name)

        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        vram_gb = round(float(int(mem_info.total)) / (1024 ** 3), 1)

        gpu_info["has_discrete_gpu"] = True
        gpu_info["gpu_name"] = gpu_name
        gpu_info["vram_gb"] = vram_gb
        gpu_info["display_str"] = f"{gpu_name} ({vram_gb} GB VRAM)"
    except Exception:
        # Fallback to WMI on Windows
        try:
            import wmi
            w = wmi.WMI()
            controllers = [g.Name for g in w.Win32_VideoController() if g.Name]
            if controllers:
                gpu_info["gpu_name"] = controllers[0]
                gpu_info["display_str"] = controllers[0]
        except Exception:
            pass
    finally:
        if pynvml_initialized:
            try:
                import pynvml
                pynvml.nvmlShutdown()
            except Exception:
                pass

    return {
        "total_ram_gb": total_ram_gb,
        "avail_ram_gb": avail_ram_gb,
        "ram_gb_rounded": round(total_ram_gb),
        "ram_avail_rounded": round(avail_ram_gb, 1),
        "ram_display_str": f"{round(total_ram_gb)} GB RAM (Khả dụng: {round(avail_ram_gb, 1)} GB)",
        "os_info": os_info,
        "cpu_info": cpu_info,
        "cpu_threads": cpu_threads,
        "disk_info": disk_info,
        "gpu": gpu_info
    }

