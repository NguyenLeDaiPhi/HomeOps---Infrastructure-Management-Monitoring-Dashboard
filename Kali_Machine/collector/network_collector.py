import socket
import psutil 
from typing import Dict, Any

def network_stats() -> Dict[str, Any]: 
    """
    Collects network interface IP, MAC, netmask, and UP/DOWN status.
    """
    interfaces = {}

    if_stats = psutil.net_if_stats()
    if_addrs = psutil.net_if_addrs()

    # Link layer family cross-platform handling
    link_family = getattr(psutil, 'AF_LINK', getattr(socket, 'AF_PACKET', None))

    for iface_name, addresses in if_addrs.items():
        # Ignore loopback interface
        if iface_name == "lo":
            continue

        status = "UNKNOWN"
        if iface_name in if_stats:
            status = "UP" if if_stats[iface_name].isup else "DOWN"
        
        info = {
            "interface": iface_name,
            "status": status,
            "ip": None, 
            "netmask": None, 
            "mac": None
        }

        for addr in addresses:
            if addr.family == socket.AF_INET: 
                info["ip"] = addr.address
                info["netmask"] = addr.netmask

            if link_family is not None and addr.family == link_family:
                info["mac"] = addr.address
        
        interfaces[iface_name] = info

    return interfaces
