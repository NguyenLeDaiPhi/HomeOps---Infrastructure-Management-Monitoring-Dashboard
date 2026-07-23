import psutil 
from typing import Dict, Any

def process_snapshot() -> Dict[int, Dict[str, Any]]:
    """
    Captures a snapshot of currently running processes with their metadata.
    """
    snapshot = {}
    data_process = psutil.process_iter(attrs=[
        "pid",
        "name", 
        "username",
        "status", 
        "cpu_percent", 
        "memory_percent",
        "create_time"
    ])

    for proc in data_process:
        try:
            info = proc.info
            # Round numeric percentages for clean reporting
            if info.get('cpu_percent') is not None:
                info['cpu_percent'] = round(info['cpu_percent'], 1)
            if info.get('memory_percent') is not None:
                info['memory_percent'] = round(info['memory_percent'], 1)

            snapshot[info['pid']] = info
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    return snapshot
