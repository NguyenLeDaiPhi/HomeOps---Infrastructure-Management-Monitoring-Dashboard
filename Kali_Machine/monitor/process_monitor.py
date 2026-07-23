from typing import List, Dict, Any
from collector.process import process_snapshot
from config import KaliConfig

class ProcessMonitor:
    """
    Monitors process events (started, stopped, status/user/name changes, high CPU/Memory resource usage).
    """
    def __init__(self):
        self.previous_process: Dict[int, Dict[str, Any]] = process_snapshot()
        
    def check_changes(self) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        current_process = process_snapshot()

        current_pids = set(current_process.keys())
        previous_pids = set(self.previous_process.keys())
        
        started_pids = current_pids - previous_pids
        stopped_pids = previous_pids - current_pids

        # Process Started Events
        for pid in started_pids:
            proc_info = current_process[pid]
            events.append({
                "event": "PROCESS_STARTED",
                "pid": pid,
                "name": proc_info.get("name", "Unknown"),
                "username": proc_info.get("username", "N/A")
            })
        
        # Process Stopped Events
        for pid in stopped_pids:
            proc_info = self.previous_process[pid]
            events.append({
                "event": "PROCESS_STOPPED",
                "pid": pid, 
                "name": proc_info.get("name", "Unknown"),
                "username": proc_info.get("username", "N/A")
            })

        # Process Metadata Fields to Compare
        PROCESS_FIELDS = {
            "status": "STATUS_CHANGED", 
            "username": "OWNER_CHANGED",
            "name": "NAME_CHANGED"
        }

        common_pids = current_pids & previous_pids

        for pid in common_pids:
            current = current_process[pid]
            previous = self.previous_process[pid]

            # Field attribute change checks
            for field, event_name in PROCESS_FIELDS.items():
                if current.get(field) != previous.get(field):
                    events.append({
                        "event": event_name, 
                        "pid": pid, 
                        "name": current.get("name"),
                        "old": previous.get(field),
                        "new": current.get(field)
                    })

            # High Resource Consumption Checks (evaluated ONCE per process)
            curr_cpu = current.get("cpu_percent") or 0.0
            prev_cpu = previous.get("cpu_percent") or 0.0
            if abs(curr_cpu - prev_cpu) >= KaliConfig.CPU_THRESHOLD or curr_cpu >= 80.0:
                events.append({
                    "event": "HIGH_CPU",
                    "pid": pid, 
                    "name": current.get("name"), 
                    "cpu": curr_cpu
                })

            curr_mem = current.get("memory_percent") or 0.0
            prev_mem = previous.get("memory_percent") or 0.0
            if abs(curr_mem - prev_mem) >= KaliConfig.MEM_THRESHOLD or curr_mem >= 50.0:
                events.append({
                    "event": "HIGH_MEMORY",
                    "pid": pid, 
                    "name": current.get("name"), 
                    "memory": curr_mem
                })

        self.previous_process = current_process
        return events

if __name__ == "__main__":
    import json
    monitor = ProcessMonitor()
    process_data = monitor.check_changes()
    print(json.dumps(process_data, indent=4))
