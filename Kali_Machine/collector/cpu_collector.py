import psutil
from typing import Dict, Any, List

# Prime psutil CPU percent calculation on module load
psutil.cpu_percent(interval=None)

def cpu_stats() -> Dict[str, Any]:
    """
    Collects CPU utilization, core count, frequency, and load average.
    Returns non-blocking metrics.
    """
    try: 
        load_avg: List[float] = list(psutil.getloadavg())
    except (AttributeError, OSError): 
        load_avg = [0.0, 0.0, 0.0]

    freq_mhz = 0.0
    try:
        freq_obj = psutil.cpu_freq()
        if freq_obj and hasattr(freq_obj, 'current'):
            freq_mhz = round(freq_obj.current, 2)
    except Exception:
        freq_mhz = 0.0

    return {
        "total_cpu": psutil.cpu_percent(interval=None),
        "per_core_cpu": psutil.cpu_percent(interval=None, percpu=True),
        "logical_cores": psutil.cpu_count(logical=True) or 1,
        "physical_cores": psutil.cpu_count(logical=False) or 1,
        "frequency_mhz": freq_mhz,
        "load_average": load_avg
    }
