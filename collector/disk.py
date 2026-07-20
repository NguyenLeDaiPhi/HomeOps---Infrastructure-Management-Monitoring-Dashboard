import psutil
import json 

def disk_stats(): 
    disk_data = []
    for p in psutil.disk_partitions(all=False):
        try: 
            usage = psutil.disk_usage(p.mountpoint)
            partition_info = {
                "mountpoint": p.mountpoint, 
                "device": p.device,
                "fstyle": p.fstype, 
                "total_gb": round(usage.total / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2), 
                "usage_percent": usage.percent
            }
            disk_data.append(partition_info)
        except PermissionError:
            continue
    return disk_data