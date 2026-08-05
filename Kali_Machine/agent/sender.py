import os
import sys
import json
import socket
import time
import struct
import logging
import threading

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import KaliConfig
from collector.cpu_collector import cpu_stats
from collector.ram_collector import ram_stats
from collector.disk_collector import disk_stats
from collector.network_collector import network_stats
from collector.process_collector import process_snapshot
from monitor.network_monitor import NetworkMonitor
from monitor.process_monitor import ProcessMonitor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("KaliSenderAgent")

# ---------------------------------------------------------------------------
# Docker imports (graceful fallback if Docker SDK not installed)
# ---------------------------------------------------------------------------

_docker_available = False
try:
    from collector.docker_collector import collect_all_container_telemetry
    from monitor.docker_monitor import DockerMonitor
    _docker_available = True
    logger.info("Docker SDK detected — Docker telemetry collection enabled.")
except ImportError:
    logger.warning("Docker SDK not installed — Docker telemetry disabled. Install with: pip install docker")
except Exception as e:
    logger.warning(f"Docker module failed to load: {e} — Docker telemetry disabled.")


sock_lock = threading.Lock()


def send_framed_json(sock: socket.socket, payload: dict) -> None:
    """
    Encodes JSON payload and sends it over TCP socket preceded by a 4-byte big-endian length header.
    Thread-safe socket writing protected by sock_lock.
    """
    message_bytes = json.dumps(payload).encode('utf-8')
    header = struct.pack("!I", len(message_bytes))
    with sock_lock:
        sock.sendall(header + message_bytes)


def send_heartbeat(sock: socket.socket) -> None:
    """Transmits a periodic liveness heartbeat message."""
    payload = {
        "type": "HEARTBEAT",
        "hostname": socket.gethostname(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    send_framed_json(sock, payload)
    logger.debug("Heartbeat signal transmitted")


def heartbeat_worker(sock: socket.socket, stop_event: threading.Event) -> None:
    """Background worker sending periodic heartbeats over the active TCP connection."""
    logger.info(f"Heartbeat thread started (interval: {KaliConfig.HEARTBEAT_INTERVAL}s).")
    while not stop_event.is_set():
        try:
            send_heartbeat(sock)
        except Exception as e:
            logger.warning(f"Heartbeat delivery failed: {e}")
            break
        stop_event.wait(KaliConfig.HEARTBEAT_INTERVAL)


def get_base_payload(message_type: str) -> dict:
    return {
        "type": message_type,
        "hostname": socket.gethostname(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
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


# ---------------------------------------------------------------------------
# Docker Telemetry Senders
# ---------------------------------------------------------------------------

def send_docker_telemetry(sock: socket.socket) -> None:
    """Collects and transmits Docker container telemetry over TCP."""
    if not _docker_available:
        return

    try:
        payload = get_base_payload("DOCKER_TELEMETRY")
        docker_data = collect_all_container_telemetry()
        payload.update(docker_data)
        send_framed_json(sock, payload)
        logger.info(
            f"Docker telemetry transmitted "
            f"({docker_data['docker_info']['running']} running / "
            f"{docker_data['docker_info']['total_containers']} total)"
        )
    except Exception as e:
        logger.warning(f"Failed to send Docker telemetry: {e}")


def send_docker_events(sock: socket.socket, events: list) -> None:
    """Transmits Docker container lifecycle events over TCP."""
    payload = get_base_payload("DOCKER_EVENT")
    payload["events_docker"] = events
    send_framed_json(sock, payload)
    logger.info(f"Docker events transmitted ({len(events)} events)")


# ---------------------------------------------------------------------------
# Command Receiver Thread
# ---------------------------------------------------------------------------

def start_command_receiver_thread():
    """Starts the FastAPI command receiver in a daemon thread."""
    try:
        from agent.command_receiver import start_command_receiver
        thread = threading.Thread(target=start_command_receiver, daemon=True, name="CommandReceiver")
        thread.start()
        logger.info(
            f"Command Receiver started on "
            f"{KaliConfig.COMMAND_API_HOST}:{KaliConfig.COMMAND_API_PORT}"
        )
        return thread
    except ImportError:
        logger.warning("FastAPI/uvicorn not installed — Command Receiver disabled. Install with: pip install fastapi uvicorn")
        return None
    except Exception as e:
        logger.error(f"Failed to start Command Receiver: {e}")
        return None


# ---------------------------------------------------------------------------
# Main Agent Loop
# ---------------------------------------------------------------------------

def run_agent():
    logger.info(f"Starting Kali Telemetry Agent -> Target Windows Host {KaliConfig.WINDOWS_IP}:{KaliConfig.PORT}")

    # Start the command receiver API in a background thread
    cmd_thread = start_command_receiver_thread()

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
            docker_monitor = DockerMonitor() if _docker_available else None

            # Transmit initial telemetry snapshots
            send_initial_network_snapshot(sock)
            send_initial_process_snapshot(sock)

            # Send initial Docker telemetry immediately
            if _docker_available:
                send_docker_telemetry(sock)

            # Start periodic heartbeat thread over active TCP connection
            hb_stop_event = threading.Event()
            hb_thread = threading.Thread(
                target=heartbeat_worker,
                args=(sock, hb_stop_event),
                daemon=True,
                name="HeartbeatSender"
            )
            hb_thread.start()

            # Track separate Docker telemetry interval
            last_docker_send = time.time()

            try:
                while True:
                    send_hardware_metrics(sock)

                    # Check for dynamic state changes
                    net_events = network_monitor.check_changes()
                    if net_events:
                        send_network_update(sock, net_events)

                    proc_events = process_monitor.check_changes()
                    if proc_events:
                        send_process_update(sock, proc_events)

                    # Docker telemetry on its own interval (heavier collection)
                    if _docker_available:
                        now = time.time()
                        if now - last_docker_send >= KaliConfig.DOCKER_TELEMETRY_INTERVAL:
                            send_docker_telemetry(sock)
                            last_docker_send = now

                        # Docker events on every tick (lightweight diff)
                        if docker_monitor:
                            docker_events = docker_monitor.check_changes()
                            if docker_events:
                                send_docker_events(sock, docker_events)

                    time.sleep(KaliConfig.METRIC_INTERVAL)
            finally:
                hb_stop_event.set()
                hb_thread.join(timeout=1.0)

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
