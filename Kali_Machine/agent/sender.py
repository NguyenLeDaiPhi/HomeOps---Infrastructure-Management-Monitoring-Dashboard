import json
import socket
import time
import struct

from collector.cpu import cpu_stats
from collector.ram import ram_stats
from collector.disk import disk_stats
from collector.network import network_stats

from monitor.network_monitor import NetworkMonitor

WINDOWS_IP = "192.168.2.1"
PORT = 5003

def send_json(sock, payload):
    """
    Send one JSON message terminated by a newline.
    This solves TCP message framing.
    """
    message = json.dumps(payload).encode('utf-8')
    message_length = len(message)
    header = struct.pack("!I", message_length)
    sock.sendall(header)
    sock.sendall(message)

def send_hardware_metrics(sock):
    payload = {
        "type": "HARDWARE_METRICS",
        "hostname": socket.gethostname(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),

        "cpu": cpu_stats(), 
        "ram": ram_stats(), 
        "disk": disk_stats()
    }
    send_json(sock, payload)
    print("[+] Hardware metrics sent")

def send_initial_snapshot(sock):
    
    payload = {
        "type": "INITIAL_SNAPSHOT",
        "hostname": socket.gethostname(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),

        "network": network_stats()
    }

    send_json(sock, payload)

    print("[+] Initial snapshot sent")


def send_network_update(sock, events):

    payload = {
        "type": "NETWORK_EVENT",
        "hostname": socket.gethostname(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),

        "events": events,

        # New snapshot after the change    
        "network": network_stats()
    }

    send_json(sock, payload)

    print("[+] Network update sent")


def send_data():

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print(f"Connecting to {WINDOWS_IP}:{PORT}...")

    try:

        sock.connect((WINDOWS_IP, PORT))

        print("[+] Connected.")

        #
        # Create ONE monitor.
        # It remembers the previous snapshot.
        #
        monitor = NetworkMonitor()

        #
        # Send only once.
        #
        send_initial_snapshot(sock)

        while True:

            #
            # Send metrics every 5 seconds
            #
            send_hardware_metrics(sock)

            #
            # Detect changes
            #
            events = monitor.check_changes()

            #
            # Only send if something changed.
            #
            if events:

                send_network_update(sock, events)

            time.sleep(5)

    except ConnectionRefusedError:

        print("Connection refused.")

    except BrokenPipeError:

        print("Windows server disconnected.")

    except KeyboardInterrupt:

        print("Sender stopped.")

    finally:

        sock.close()


if __name__ == "__main__":

    send_data()
