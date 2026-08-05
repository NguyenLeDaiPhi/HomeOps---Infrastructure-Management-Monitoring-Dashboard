import os
import sys
import socket
import json
import struct
import logging
import asyncio
import threading
import time
import hashlib
import base64
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional, Set, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from config.config import WindowsConfig
from database.connection import init_db
from database.repositories import MetricsRepository, HeartbeatRepository, parse_timestamp
from database.retention import start_retention_daemon

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("WindowsListener")

# Non-blocking executor for DB operations so DB never stalls live telemetry
db_executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="DBWriter")

def safe_db_submit(fn, *args, **kwargs):
    """Submits DB task asynchronously. Catches and logs errors without blocking caller."""
    def _wrapper():
        try:
            fn(*args, **kwargs)
        except Exception as e:
            logger.error(f"Async DB write task failed: {e}")

    db_executor.submit(_wrapper)

class StateManager:
    """In-memory telemetry state manager with rolling alert logs and heartbeat tracking."""
    def __init__(self):
        self.lock = threading.Lock()
        self.hosts: Dict[str, Dict[str, Any]] = {}
        self.state: Dict[str, Any] = {
            "agent_status": "OFFLINE",
            "hostname": "Unknown",
            "last_updated": None,
            "hardware": {},
            "network": {},
            "process": {},
            "docker": {
                "containers": [],
                "docker_info": {"total_containers": 0, "running": 0, "paused": 0, "stopped": 0}
            },
            "alerts": [],
            "hosts": {}
        }
        logger.info(f"StateManager initialized id={id(self)} hosts_id={id(self.hosts)}")

    def update_heartbeat(self, hostname: str, timestamp: str) -> bool:
        with self.lock:
            ts_dt = parse_timestamp(timestamp)
            prev_info = self.hosts.get(hostname, {})
            prev_status = prev_info.get("status", "OFFLINE")

            host_info = dict(prev_info)
            host_info.update({
                "status": "ONLINE",
                "last_heartbeat": timestamp,
                "last_heartbeat_dt": ts_dt
            })
            self.hosts[hostname] = host_info

            if "hosts" not in self.state:
                self.state["hosts"] = {}

            host_state = dict(self.state["hosts"].get(hostname, {}))
            host_state.update({
                "status": "ONLINE",
                "last_heartbeat": timestamp
            })
            self.state["hosts"][hostname] = host_state

            if self.state.get("hostname", "Unknown") in ("Unknown", hostname):
                self.state["agent_status"] = "ONLINE"
                self.state["hostname"] = hostname
                self.state["last_updated"] = timestamp

            logger.info(f"StateManager id={id(self)} update_heartbeat host={hostname} host_obj_id={id(host_info)} last_heartbeat_dt_obj_id={id(host_info['last_heartbeat_dt'])}")
            logger.info(f"Heartbeat received from {hostname}: {timestamp}")
            logger.info(f"Parsed heartbeat datetime: {ts_dt.isoformat()}")
            logger.info(f"Stored heartbeat dt for {hostname}: {host_info['last_heartbeat_dt'].isoformat()}")

            return prev_status != "ONLINE"

    def mark_offline(self, hostname: str) -> bool:
        with self.lock:
            if hostname in self.hosts:
                if self.hosts[hostname]["status"] != "OFFLINE":
                    self.hosts[hostname]["status"] = "OFFLINE"
                    if "hosts" in self.state and hostname in self.state["hosts"]:
                        self.state["hosts"][hostname]["status"] = "OFFLINE"
                    if self.state.get("hostname") == hostname:
                        self.state["agent_status"] = "OFFLINE"
                    return True
            return False

    def mark_online(self, hostname: str) -> bool:
        with self.lock:
            if hostname in self.hosts:
                if self.hosts[hostname]["status"] != "ONLINE":
                    self.hosts[hostname]["status"] = "ONLINE"
                    if "hosts" in self.state and hostname in self.state["hosts"]:
                        self.state["hosts"][hostname]["status"] = "ONLINE"
                    if self.state.get("hostname") == hostname:
                        self.state["agent_status"] = "ONLINE"
                    return True
            return False

    def check_heartbeat_timeouts(self, timeout_seconds: float = 30.0) -> List[str]:
        now = datetime.now(timezone.utc)
        timed_out_hosts = []
        with self.lock:
            for h_name, h_info in self.hosts.items():
                if h_info.get("status") != "ONLINE":
                    continue

                hb_dt = h_info.get("last_heartbeat_dt")
                if hb_dt is None:
                    logger.warning(f"Heartbeat timeout check skipped for {h_name}: no stored datetime.")
                    continue

                age_seconds = (now - hb_dt).total_seconds()
                logger.info(
                    f"StateManager id={id(self)} check_heartbeat_timeouts host={h_name} host_obj_id={id(h_info)} "
                    f"last_heartbeat_dt_obj_id={id(hb_dt)} age={age_seconds:.1f}s"
                )

                if age_seconds > timeout_seconds:
                    h_info["status"] = "OFFLINE"
                    if "hosts" in self.state and h_name in self.state["hosts"]:
                        self.state["hosts"][h_name]["status"] = "OFFLINE"
                    if self.state.get("hostname") == h_name:
                        self.state["agent_status"] = "OFFLINE"
                    timed_out_hosts.append(h_name)
        return timed_out_hosts

    def get_host_statuses(self) -> List[Dict[str, Any]]:
        with self.lock:
            res = []
            for h_name, h_info in self.hosts.items():
                res.append({
                    "hostname": h_name,
                    "status": h_info.get("status", "OFFLINE"),
                    "last_heartbeat": h_info.get("last_heartbeat")
                })
            return res

    def update_hardware(self, hostname: str, timestamp: str, cpu: dict, ram: dict, disk: list):
        with self.lock:
            self.state["agent_status"] = "ONLINE"
            self.state["hostname"] = hostname
            self.state["last_updated"] = timestamp
            self.state["hardware"] = {
                "cpu": cpu,
                "ram": ram,
                "disk": disk
            }

            host_info = self.hosts.setdefault(hostname, {})
            host_info["status"] = "ONLINE"
            if "last_heartbeat" not in host_info:
                ts_dt = parse_timestamp(timestamp)
                host_info["last_heartbeat"] = timestamp
                host_info["last_heartbeat_dt"] = ts_dt

            if "hosts" not in self.state:
                self.state["hosts"] = {}
            host_state = dict(self.state["hosts"].get(hostname, {}))
            host_state.update({
                "status": "ONLINE",
                "last_heartbeat": host_info.get("last_heartbeat")
            })
            self.state["hosts"][hostname] = host_state

    def update_network(self, hostname: str, timestamp: str, network: dict):
        with self.lock:
            self.state["hostname"] = hostname
            self.state["last_updated"] = timestamp
            self.state["network"] = network

    def update_process(self, hostname: str, timestamp: str, process: dict):
        with self.lock:
            self.state["hostname"] = hostname
            self.state["last_updated"] = timestamp
            self.state["process"] = process

    def update_docker(self, hostname: str, timestamp: str, containers: list, docker_info: dict):
        with self.lock:
            self.state["hostname"] = hostname
            self.state["last_updated"] = timestamp
            self.state["docker"] = {
                "containers": containers,
                "docker_info": docker_info
            }

    def add_alerts(self, events: list, category: str):
        with self.lock:
            for ev in events:
                alert_entry = {
                    "timestamp": ev.get("timestamp") or self.state.get("last_updated"),
                    "category": category,
                    "event": ev.get("event") or ev.get("alert") or "EVENT",
                    "details": ev
                }
                # Keep last 50 alerts
                self.state["alerts"].insert(0, alert_entry)
                if len(self.state["alerts"]) > 50:
                    self.state["alerts"].pop()

    def get_snapshot(self) -> dict:
        with self.lock:
            return dict(self.state)

global_state = StateManager()
ws_clients: Set[socket.socket] = set()
ws_clients_lock = threading.Lock()

def broadcast_ws_state():
    """Broadcasts current state JSON frame to all connected WebSocket clients."""
    snapshot = global_state.get_snapshot()
    payload = json.dumps(snapshot).encode('utf-8')
    
    # Construct WebSocket unmasked text frame
    length = len(payload)
    if length <= 125:
        header = bytes([0x81, length])
    elif length <= 65535:
        header = bytes([0x81, 126]) + struct.pack("!H", length)
    else:
        header = bytes([0x81, 127]) + struct.pack("!Q", length)

    frame = header + payload

    with ws_clients_lock:
        to_remove = set()
        for client in ws_clients:
            try:
                client.sendall(frame)
            except Exception:
                to_remove.add(client)
        for client in to_remove:
            ws_clients.remove(client)
            try:
                client.close()
            except Exception:
                pass

def broadcast_ws_message(message: dict):
    """Broadcasts an arbitrary JSON message to all connected WebSocket clients.

    Unlike broadcast_ws_state() which sends the full telemetry snapshot,
    this function sends a targeted message dict (e.g. HTTP_REQUEST_EVENT).
    """
    payload = json.dumps(message).encode('utf-8')

    length = len(payload)
    if length <= 125:
        header = bytes([0x81, length])
    elif length <= 65535:
        header = bytes([0x81, 126]) + struct.pack("!H", length)
    else:
        header = bytes([0x81, 127]) + struct.pack("!Q", length)

    frame = header + payload

    with ws_clients_lock:
        to_remove = set()
        for client in ws_clients:
            try:
                client.sendall(frame)
            except Exception:
                to_remove.add(client)
        for client in to_remove:
            ws_clients.remove(client)
            try:
                client.close()
            except Exception:
                pass

def recv_exact(sock: socket.socket, size: int) -> Optional[bytes]:
    """Helper to receive exact N bytes from stream socket."""
    data = b''
    while len(data) < size:
        try:
            chunk = sock.recv(size - len(data))
            if not chunk:
                return None
            data += chunk
        except Exception:
            return None
    return data

def handle_payload(payload: dict, addr: tuple):
    logger.info(f"handle_payload using StateManager id={id(global_state)} hosts_id={id(global_state.hosts)}")
    msg_type = payload.get("type")
    hostname = payload.get("hostname", "Unknown")
    timestamp = payload.get("timestamp", "N/A")

    if msg_type == "HARDWARE_METRICS":
        global_state.update_hardware(
            hostname, timestamp,
            payload.get("cpu", {}),
            payload.get("ram", {}),
            payload.get("disk", [])
        )
        safe_db_submit(MetricsRepository.save_hardware_metrics, payload)

    elif msg_type == "INITIAL_NETWORK_SNAPSHOT":
        global_state.update_network(hostname, timestamp, payload.get("network", {}))

    elif msg_type == "INITIAL_PROCESS_SNAPSHOT":
        global_state.update_process(hostname, timestamp, payload.get("process", {}))

    elif msg_type == "NETWORK_EVENT":
        events = payload.get("events_network", [])
        global_state.add_alerts(events, "NETWORK")
        if "network" in payload:
            global_state.update_network(hostname, timestamp, payload["network"])
        for ev in events:
            safe_db_submit(
                MetricsRepository.save_connection_event,
                hostname, "NETWORK_EVENT", str(ev), timestamp
            )

    elif msg_type == "PROCESS_EVENT":
        events = payload.get("events_process", [])
        global_state.add_alerts(events, "PROCESS")
        if "process" in payload:
            global_state.update_process(hostname, timestamp, payload["process"])

    elif msg_type == "DOCKER_TELEMETRY":
        global_state.update_docker(
            hostname, timestamp,
            payload.get("containers", []),
            payload.get("docker_info", {})
        )
        safe_db_submit(MetricsRepository.save_docker_metrics, payload)

    elif msg_type == "DOCKER_EVENT":
        events = payload.get("events_docker", [])
        global_state.add_alerts(events, "DOCKER")
        for ev in events:
            safe_db_submit(
                MetricsRepository.save_connection_event,
                hostname, "DOCKER_EVENT", str(ev), timestamp
            )

    elif msg_type == "HEARTBEAT":
        global_state.update_heartbeat(hostname, timestamp)
        safe_db_submit(
            HeartbeatRepository.update_host_heartbeat,
            hostname, "ONLINE", timestamp
        )
        ws_msg = {
            "type": "HEARTBEAT_UPDATE",
            "hostname": hostname,
            "status": "ONLINE",
            "last_heartbeat": timestamp
        }
        broadcast_ws_message(ws_msg)

    else:
        logger.warning(f"Received unknown message type: {msg_type} from {addr[0]}")

    # Push updated state to WebSocket clients
    broadcast_ws_state()

def start_tcp_listener():
    """TCP Server listening for incoming Kali Linux agent metrics."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((WindowsConfig.LISTENER_IP, WindowsConfig.PORT))
        server.listen(5)
        logger.info(f"TCP Listener active on {WindowsConfig.LISTENER_IP}:{WindowsConfig.PORT}")

        while True:
            client, addr = server.accept()
            logger.info(f"Agent connected from {addr[0]}:{addr[1]}")
            safe_db_submit(
                MetricsRepository.save_connection_event,
                f"Agent-{addr[0]}", "CONNECTED", f"Agent connected from {addr[0]}:{addr[1]}"
            )
            
            try:
                while True:
                    header = recv_exact(client, 4)
                    if not header:
                        logger.info(f"Agent {addr[0]} disconnected cleanly.")
                        safe_db_submit(
                            MetricsRepository.save_connection_event,
                            f"Agent-{addr[0]}", "DISCONNECTED", f"Agent {addr[0]} disconnected cleanly."
                        )
                        break

                    msg_length = struct.unpack("!I", header)[0]
                    json_bytes = recv_exact(client, msg_length)
                    if not json_bytes:
                        logger.info(f"Agent {addr[0]} connection lost during payload receive.")
                        break

                    try:
                        payload = json.loads(json_bytes.decode('utf-8'))
                        handle_payload(payload, addr)
                    except json.JSONDecodeError as e:
                        logger.error(f"Malformed JSON payload from {addr[0]}: {e}")
                        continue

            except (ConnectionResetError, BrokenPipeError):
                logger.warning(f"Agent connection reset: {addr[0]}")
            except Exception as e:
                logger.error(f"Error handling client {addr[0]}: {e}")
            finally:
                client.close()

    except Exception as e:
        logger.critical(f"TCP Listener failed: {e}")
    finally:
        server.close()

def handle_web_client(client_sock: socket.socket):
    """Handles HTTP API requests and WebSocket upgrade connections for dashboard."""
    try:
        data = client_sock.recv(4096).decode('utf-8', errors='ignore')
        if not data:
            client_sock.close()
            return

        lines = data.split('\r\n')

        # WebSocket Upgrade Handling
        if "Upgrade: websocket" in data or "Sec-WebSocket-Key" in data:
            key = None
            for line in lines:
                if line.lower().startswith("sec-websocket-key:"):
                    key = line.split(":")[1].strip()
                    break

            if key:
                GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
                accept_key = base64.b64encode(hashlib.sha1((key + GUID).encode('utf-8')).digest()).decode('utf-8')
                response = (
                    "HTTP/1.1 101 Switching Protocols\r\n"
                    "Upgrade: websocket\r\n"
                    "Connection: Upgrade\r\n"
                    f"Sec-WebSocket-Accept: {accept_key}\r\n\r\n"
                )
                client_sock.sendall(response.encode('utf-8'))
                
                with ws_clients_lock:
                    ws_clients.add(client_sock)

                # Send initial state immediately
                broadcast_ws_state()
                return

        # Standard HTTP REST fallback endpoint
        snapshot = global_state.get_snapshot()
        json_body = json.dumps(snapshot)
        http_response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "Access-Control-Allow-Methods: GET, OPTIONS\r\n"
            f"Content-Length: {len(json_body.encode('utf-8'))}\r\n\r\n"
            f"{json_body}"
        )
        client_sock.sendall(http_response.encode('utf-8'))
        client_sock.close()

    except Exception:
        try:
            client_sock.close()
        except Exception:
            pass

def start_web_server():
    """HTTP & WebSocket bridge server for Frontend Dashboard."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((WindowsConfig.WEBSOCKET_HOST, WindowsConfig.WEBSOCKET_PORT))
        server.listen(10)
        logger.info(f"Dashboard Web/WebSocket Server active on http://localhost:{WindowsConfig.WEBSOCKET_PORT}")

        while True:
            client, addr = server.accept()
            t = threading.Thread(target=handle_web_client, args=(client,), daemon=True)
            t.start()
    except Exception as e:
        logger.critical(f"Web server failed: {e}")
    finally:
        server.close()

def _heartbeat_monitor_worker():
    logger.info("Heartbeat 1-second background monitor active (timeout: 30s).")
    while True:
        try:
            timed_out_hosts = global_state.check_heartbeat_timeouts(timeout_seconds=30.0)
            for h_name in timed_out_hosts:
                logger.warning(f"Host '{h_name}' heartbeat timed out (>30s) -> marking OFFLINE.")
                last_hb = global_state.hosts.get(h_name, {}).get("last_heartbeat")
                safe_db_submit(
                    HeartbeatRepository.update_host_heartbeat,
                    h_name, "OFFLINE", last_hb or datetime.now(timezone.utc).isoformat()
                )
                ws_msg = {
                    "type": "HEARTBEAT_UPDATE",
                    "hostname": h_name,
                    "status": "OFFLINE",
                    "last_heartbeat": last_hb
                }
                broadcast_ws_message(ws_msg)
        except Exception as e:
            logger.error(f"Heartbeat monitor worker error: {e}")
        time.sleep(1.0)

def start_heartbeat_monitor():
    """Launches the 1-second heartbeat timeout monitor daemon thread."""
    t = threading.Thread(target=_heartbeat_monitor_worker, daemon=True, name="HeartbeatMonitor")
    t.start()
    return t

def start_gateway_thread():
    """Starts the Windows FastAPI Command Gateway in a daemon thread."""
    try:
        from windows_listen.command_gateway import start_gateway
        start_gateway()
    except Exception as e:
        logger.error(f"Failed to start Command Gateway: {e}")

def main():
    logger.info("Starting HomeOps Windows Telemetry Service...")
    
    # Initialize PostgreSQL Database schema
    init_db()

    # Start 24h retention cleanup daemon thread
    start_retention_daemon()

    # Start background heartbeat offline monitor thread
    start_heartbeat_monitor()

    # Run TCP Listener thread
    tcp_thread = threading.Thread(target=start_tcp_listener, daemon=True)
    tcp_thread.start()

    # Run HTTP/WebSocket Server thread
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()

    # Run FastAPI Command Gateway thread
    gateway_thread = threading.Thread(target=start_gateway_thread, daemon=True)
    gateway_thread.start()

    try:
        while True:
            tcp_thread.join(timeout=1.0)
            web_thread.join(timeout=1.0)
            gateway_thread.join(timeout=1.0)
    except KeyboardInterrupt:
        logger.info("Windows Service shutting down...")
    finally:
        db_executor.shutdown(wait=False)

if __name__ == "__main__":
    main()
