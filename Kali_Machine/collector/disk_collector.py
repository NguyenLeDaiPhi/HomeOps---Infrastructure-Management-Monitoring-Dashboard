import psutil
from typing import List, Dict, Any

def disk_stats() -> List[Dict[str, Any]]: 
    """
    Collects disk partition storage statistics.
    """
    disk_data = []
    for partition in psutil.disk_partitions(all=False):
        try: 
            usage = psutil.disk_usage(partition.mountpoint)
            partition_info = {
                "mountpoint": partition.mountpoint, 
                "device": partition.device,
                "fstype": partition.fstype, 
                "total_gb": round(usage.total / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2), 
                "used_gb": round(usage.used / (1024**3), 2),
                "usage_percent": usage.percent
            }
            disk_data.append(partition_info)
        except (PermissionError, OSError):
            continue
    return disk_data