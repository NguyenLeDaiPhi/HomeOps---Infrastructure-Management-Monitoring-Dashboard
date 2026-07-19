import psutil
import socket 
import json 
import time 

def ram_stats():
    memory = psutil.virtual_memory()

    data = {
        "total_gb": round(memory.total / (1024 ** 3), 2),
        "used_gb": round(memory.used / (1024 ** 3), 2),
        "available_gb": round(memory.available / (1024 ** 3), 2),
        "percent": memory.percent
    }
    return data