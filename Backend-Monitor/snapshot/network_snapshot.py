import psutil 
import socket 
import json

def network_stats(): 
    interfaces = {}

    if_stats = psutil.net_if_stats()
    if_addrs = psutil.net_if_addrs()

    for iface_name, addresses in if_addrs.items():

        # Ignore loopback 
        if iface_name == "lo":
            continue

        status = "UNKNOW"
        
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
            if addr.family == 2: 
                info["ip"] = addr.address
                info["netmask"] = addr.netmask

            if addr.family == psutil.AF_LINK:
                info["mac"] = addr.address
        
        interfaces[iface_name] = info
    return interfaces
    


