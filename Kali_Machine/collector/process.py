import psutil 
import json

def process_snapshot():
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
            snapshot[proc.info['pid']] = proc.info
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return snapshot
