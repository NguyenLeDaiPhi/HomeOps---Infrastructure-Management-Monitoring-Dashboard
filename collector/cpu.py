import psutil

def cpu_stats():
    try: 
        load_avg = list(psutil.getloadavg())
    except: 
        load_avg = [0.0, 0.0, 0.0]
    
    data = {
        "total_cpu": psutil.cpu_percent(interval=1),
        "per_core_cpu": psutil.cpu_percent(percpu=True),
        "logical_cores": psutil.cpu_count(logical=True),
        "physical_cores": psutil.cpu_count(logical=False),
        "frequency_mhz": psutil.cpu_count(logical=False),
        "load_average": load_avg
    }
    return data


