import os
import sys
import json
import socket
import time
import struct
import logging

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import KaliConfig
from collector.cpu import cpu_stats
from collector.ram import ram_stats
from collector.disk import disk_stats
from collector.network import network_stats
from collector.process import process_snapshot
from monitor.network_monitor import NetworkMonitor
from monitor.process_monitor import ProcessMonitor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("KaliSenderAgent")

def send_framed_json(sock: socket.socket, payload: dict) -> None:
    """
    Encodes JSON payload and sends it over TCP socket preceded by a 4-byte big-endian length header.
    """
    message_bytes = json.dumps(payload).encode('utf-8')
    header = struct.pack("!I", len(message_bytes))
    sock.sendall(header + message_bytes)

def get_base_payload(message_type: str) -> dict:
    return {
        "type": message_type,
        "hostname": socket.gethostname(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

def send_hardware_metrics(sock: socket.socket) -> None:
    payload = get_base_payload("HARDWARE_METRICS")
    payload.update({
        "cpu": cpu_stats(),
        "ram": ram_stats(),
        "disk": disk_stats()
    })
    send_framed_json(sock, payload)
    logger.info("Hardware metrics transmitted")

def send_initial_network_snapshot(sock: socket.socket) -> None:
    payload = get_base_payload("INITIAL_NETWORK_SNAPSHOT")
    payload["network"] = network_stats()
    send_framed_json(sock, payload)
    logger.info("Initial network snapshot transmitted")

def send_initial_process_snapshot(sock: socket.socket) -> None:
    payload = get_base_payload("INITIAL_PROCESS_SNAPSHOT")
    payload["process"] = process_snapshot()
    send_framed_json(sock, payload)
    logger.info("Initial process snapshot transmitted")

def send_network_update(sock: socket.socket, events: list) -> None:
    payload = get_base_payload("NETWORK_EVENT")
    payload["events_network"] = events
    payload["network"] = network_stats()
    send_framed_json(sock, payload)
    logger.info(f"Network events update transmitted ({len(events)} events)")

def send_process_update(sock: socket.socket, events: list) -> None:
    payload = get_base_payload("PROCESS_EVENT")
    payload["events_process"] = events
    payload["process"] = process_snapshot()
    send_framed_json(sock, payload)
    logger.info(f"Process events update transmitted ({len(events)} events)")

def run_agent():
    logger.info(f"Starting Kali Telemetry Agent -> Target Windows Host {KaliConfig.WINDOWS_IP}:{KaliConfig.PORT}")

    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10.0)

        try:
            logger.info(f"Attempting TCP connection to {KaliConfig.WINDOWS_IP}:{KaliConfig.PORT}...")
            sock.connect((KaliConfig.WINDOWS_IP, KaliConfig.PORT))
            sock.settimeout(None) # Reset to blocking mode once connected
            logger.info("Successfully connected to Windows monitoring host!")

            # Instantiate change monitors
            network_monitor = NetworkMonitor()
            process_monitor = ProcessMonitor()

            # Transmit initial telemetry snapshots
            send_initial_network_snapshot(sock)
            send_initial_process_snapshot(sock)

            while True:
                send_hardware_metrics(sock)

                # Check for dynamic state changes
                net_events = network_monitor.check_changes()
                if net_events:
                    send_network_update(sock, net_events)

                proc_events = process_monitor.check_changes()
                if proc_events:
                    send_process_update(sock, proc_events)

                time.sleep(KaliConfig.METRIC_INTERVAL)

        except (ConnectionRefusedError, socket.timeout):
            logger.warning(f"Connection refused by target {KaliConfig.WINDOWS_IP}:{KaliConfig.PORT}. Retrying in {KaliConfig.RECONNECT_DELAY}s...")
        except (BrokenPipeError, ConnectionResetError):
            logger.warning("Connection lost to Windows host. Reconnecting...")
        except KeyboardInterrupt:
            logger.info("Agent stopped by user signal.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in agent execution loop: {e}", exc_info=True)
        finally:
            sock.close()
            time.sleep(KaliConfig.RECONNECT_DELAY)

if __name__ == "__main__":
    run_agent()
