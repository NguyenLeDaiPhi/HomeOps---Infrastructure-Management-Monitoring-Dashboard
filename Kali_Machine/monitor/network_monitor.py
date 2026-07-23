from typing import List, Dict, Any
from collector.network import network_stats

class NetworkMonitor:
    """
    Monitors changes in network interface states (added/removed interfaces, IP/MAC/Status/Netmask changes).
    """
    def __init__(self):
        self.previous_snapshot: Dict[str, Any] = network_stats()
    
    def check_changes(self) -> List[Dict[str, Any]]:
        current_snapshot = network_stats()
        events: List[Dict[str, Any]] = []

        previous_interfaces = set(self.previous_snapshot.keys())
        current_interfaces = set(current_snapshot.keys())

        # Detect newly added interfaces
        for iface in current_interfaces - previous_interfaces:
            events.append({
                "event": "INTERFACE_ADDED",
                "interface": iface,
                "new": current_snapshot[iface]
            })

        # Detect removed interfaces
        for iface in previous_interfaces - current_interfaces:
            events.append({
                "event": "INTERFACE_REMOVED", 
                "interface": iface, 
                "old": self.previous_snapshot[iface]
            })

        # Detect changes in existing interfaces
        common_interfaces = previous_interfaces & current_interfaces
        for iface in common_interfaces:
            previous = self.previous_snapshot[iface]
            current = current_snapshot[iface]

            if previous.get("status") != current.get("status"):
                events.append({
                    "event": "STATUS_CHANGED",
                    "interface": iface, 
                    "old": previous.get("status"),
                    "new": current.get("status")
                })

            if previous.get("ip") != current.get("ip"):
                events.append({
                    "event": "IP_CHANGED", 
                    "interface": iface, 
                    "old": previous.get("ip"), 
                    "new": current.get("ip")
                })
            
            if previous.get("mac") != current.get("mac"):
                events.append({
                    "event": "MAC_CHANGED",
                    "interface": iface,
                    "old": previous.get("mac"),
                    "new": current.get("mac")
                })

            if previous.get("netmask") != current.get("netmask"):
                events.append({
                    "event": "NETMASK_CHANGED", 
                    "interface": iface, 
                    "old": previous.get("netmask"), 
                    "new": current.get("netmask")
                })
            
        self.previous_snapshot = current_snapshot
        return events
