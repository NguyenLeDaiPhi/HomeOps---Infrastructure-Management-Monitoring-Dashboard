import psutil
from typing import Dict, Any

def ram_stats() -> Dict[str, Any]:
    """
    Collects virtual and swap memory metrics.
    """
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "total_gb": round(memory.total / (1024 ** 3), 2),
        "used_gb": round(memory.used / (1024 ** 3), 2),
        "available_gb": round(memory.available / (1024 ** 3), 2),
        "percent": memory.percent,
        "swap_total_gb": round(swap.total / (1024 ** 3), 2),
        "swap_used_gb": round(swap.used / (1024 ** 3), 2),
        "swap_percent": swap.percent
    }