from collector.process import process_snapshot
import json

class ProcessMonitor:

    def __init__(self):
        self.previous_process = process_snapshot()
        
    # Compare previous process snapshot and current snapshot with PID 
    def check_changes(self):
        # Add dictionary
        events = []

        # add current snapshot
        current_process = process_snapshot()

        # Create current & previous process set key
        current_process_key = set(current_process.keys())
        # previous_process_key = set(self.previous_snapshot.keys())
        previous_process_key = set(self.previous_process.keys())
        
        # Create variable to compare previous and current
        started = current_process_key - previous_process_key
        stopped = previous_process_key - current_process_key

        # Inital a loop to compare previous and current
        for proc_pid in started:
            events.append({
                "events": "PROCESS_STARTED",
                "PID": proc_pid,
                "name": current_process[proc_pid]["name"]
            })
        
        # Compare if any processes removed or stopped
        for proc_pid in stopped:
            events.append({
                "events": "PROCESS_STOPPED",
                "pid": proc_pid, 
                "name": self.previous_process[proc_pid]["name"]
            })


        # Initial process fields and threshold to compare the stats and recognize stats of CPU, MEMORY
        PROCESS_FIELDS = {
            "status": "STATUS_CHANGED", 
            "username": "OWNER_CHANGED",
            "name": "NAME_CHANGED"
        }

        CPU_THRESHOLD = 20

        MEM_THRESHOLD = 5

        common_process = current_process_key & previous_process_key

        # Loop to check all of processes running based on process id 
        for proc_pid in common_process:
            current = current_process[proc_pid]
            previous = self.previous_process[proc_pid]

            for field, event_name in PROCESS_FIELDS.items():
                if current[field] != previous[field]:
                    events.append({
                        "event": event_name, 
                        "pid": proc_pid, 
                        "name": current["name"],
                        "old": previous[field],
                        "new": current[field]
                    })

                if abs(current["cpu_percent"] - previous["cpu_percent"]) >= CPU_THRESHOLD:
                    events.append({
                        "alert": "HIGH_CPU",
                        "event": event_name, 
                        "pid": proc_pid, 
                        "name": current["name"], 
                        "cpu": current["cpu_percent"]
                    })
                
                if abs(current["memory_percent"] - previous["memory_percent"]) >= MEM_THRESHOLD:
                    events.append({
                        "alert": "HIGH_MEMORY",
                        "event": event_name, 
                        "pid": proc_pid, 
                        "name": current["name"], 
                        "cpu": current["memory_percent"]
                    })

        self.previous_process = current_process

        return events

if __name__ == "__main__":
    monitor = ProcessMonitor()

    process_data = monitor.check_changes()

    print(json.dumps(process_data, indent=4))
            
            
        
