import os
import sys
import socket
import json
import struct
import logging
import asyncio
import threading
import hashlib
import base64
from typing import Dict, Any, Optional, Set

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import WindowsConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("WindowsListener")

class StateManager:
    """In-memory telemetry state manager with rolling alert logs."""
    def __init__(self):
        self.lock = threading.Lock()
        self.state: Dict[str, Any] = {
            "agent_status": "OFFLINE",
            "hostname": "Unknown",
            "last_updated": None,
            "hardware": {},
            "network": {},
            "process": {},
            "alerts": []
        }

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
    elif msg_type == "INITIAL_NETWORK_SNAPSHOT":
        global_state.update_network(hostname, timestamp, payload.get("network", {}))
    elif msg_type == "INITIAL_PROCESS_SNAPSHOT":
        global_state.update_process(hostname, timestamp, payload.get("process", {}))
    elif msg_type == "NETWORK_EVENT":
        events = payload.get("events_network", [])
        global_state.add_alerts(events, "NETWORK")
        if "network" in payload:
            global_state.update_network(hostname, timestamp, payload["network"])
    elif msg_type == "PROCESS_EVENT":
        events = payload.get("events_process", [])
        global_state.add_alerts(events, "PROCESS")
        if "process" in payload:
            global_state.update_process(hostname, timestamp, payload["process"])
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
            
            try:
                while True:
                    header = recv_exact(client, 4)
                    if not header:
                        logger.info(f"Agent {addr[0]} disconnected cleanly.")
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
                        # Continue inner loop so client connection is NOT dropped
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
        first_line = lines[0] if lines else ""

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

def main():
    logger.info("Starting HomeOps Windows Telemetry Service...")
    
    # Run TCP Listener thread
    tcp_thread = threading.Thread(target=start_tcp_listener, daemon=True)
    tcp_thread.start()

    # Run HTTP/WebSocket Server thread
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()

    try:
        while True:
            tcp_thread.join(timeout=1.0)
            web_thread.join(timeout=1.0)
    except KeyboardInterrupt:
        logger.info("Windows Service shutting down...")

if __name__ == "__main__":
    main()
