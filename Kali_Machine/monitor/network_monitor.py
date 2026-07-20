from collector.network import network_stats

class NetworkMonitor:
    def __init__(self):
        self.previous_snapshot = network_stats()
    
    def check_changes(self):
        current_snapshot = network_stats()

        events = []

        previous_interface = set(self.previous_snapshot.keys())
        current_interface = set(current_snapshot.keys())

        for iface in current_interface - previous_interface:
            events.append({
                "event": "INTERFACE_ADDED",
                "interface": iface,
                "new": current_snapshot[iface]
            })

        for iface in previous_interface - current_interface:
            events.append({
                "event": "INTERFACE_REMOVED", 
                "interface": iface, 
                "new": self.previous_snapshot[iface]
            })

        common_interface = previous_interface & current_interface

        for iface in common_interface:
            previous = self.previous_snapshot[iface]
            current = current_snapshot[iface]

            if previous["status"] != current["status"]:
                events.append({
                    "event": "STATUS_CHANGED", 
                    "interface": iface, 
                    "old": previous["status"],
                    "new": current["status"]
                })

            if previous["ip"] != current["ip"]:
                events.append({
                    "event": "IP_CHANGED", 
                    "interface": iface, 
                    "old": previous["ip"], 
                    "new": current["ip"]
                })
            
            if previous["mac"] != current["mac"]:
                events.append({
                    "event": "MAC_CHANGED",
                    "interface": iface,
                    "old": previous["mac"],
                    "new": current["mac"]
                })

            if previous["netmask"] != current["netmask"]:
                events.append({
                    "event": "NETMASK_CHANGED", 
                    "interface": iface, 
                    "old": previous["netmask"], 
                    "new": current["netmask"]
                })
            
        self.previous_snapshot = current_snapshot 

        return events
