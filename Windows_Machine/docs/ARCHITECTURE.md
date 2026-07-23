# HomeOps Telemetry & Monitoring System Architecture

## Overview
HomeOps is an enterprise-grade infrastructure monitoring solution designed for host-only Virtual Machine telemetry streaming. It enables real-time metrics collection from a **Kali Linux Agent VM (192.168.2.2)** to a **Windows Host Listener Server (192.168.2.1)** and displays interactive metrics in a modern Web dashboard.

---

## High-Level Data Flow

```
+------------------------------------+                +---------------------------------------+
|        Kali Linux VM               |                |             Windows Host              |
|        (192.168.2.2)               |                |             (192.168.2.1)             |
|                                    |                |                                       |
|  [Collectors: CPU, RAM, Disk, Net] |                |  [TCP Listener Server (Port 5003)]   |
|                 |                  |                |                  |                    |
|  [Monitors: Net & Process Events]  |                |          [State Manager]              |
|                 |                  |                |                  |                    |
|   [Sender Agent TCP Client]        | === TCP Socket ===>  [WebSocket & HTTP Bridge (8000)]|
|   (Length-Prefixed Binary Header)  |                |                  |                    |
+------------------------------------+                +------------------|--------------------+
                                                                         | WebSocket / REST
                                                                         v
                                                      +---------------------------------------+
                                                      |           React Live Dashboard        |
                                                      |         (http://localhost:5173)       |
                                                      +---------------------------------------+
```

---

## Framing & Communication Protocol
- **Transport Layer**: TCP Sockets (`socket.AF_INET`, `socket.SOCK_STREAM`).
- **Framing**: Each JSON telemetry payload is prefixed with a 4-byte big-endian unsigned integer header specifying message byte length (`struct.pack("!I", len(payload))`).
- **Resilience**: The Kali sender features an infinite loop with auto-reconnection and exponential backoff retry. The Windows listener features socket context management and safe JSON exception handling.

---

## Component Breakdown

### 1. Kali Linux Agent (`Kali_Machine/`)
- **`config.py`**: Centralized configuration management.
- **`collector/`**:
  - `cpu.py`: Non-blocking CPU frequency, core counts, load averages.
  - `ram.py`: Virtual memory and Swap memory utilization.
  - `disk.py`: Disk partition mount points, free space, and standardized `fstype` schema.
  - `network.py`: Cross-platform link layer interface detection and IPv4/MAC mappings.
  - `process.py`: Safe process snapshot iterators catching `NoSuchProcess`, `AccessDenied`, and `ZombieProcess`.
- **`monitor/`**:
  - `network_monitor.py`: Interface state change detection.
  - `process_monitor.py`: Fixed resource spike detection (`HIGH_CPU`, `HIGH_MEMORY`) and process lifecycle events (`PROCESS_STARTED`, `PROCESS_STOPPED`).
- **`agent/sender.py`**: Main background agent connecting to Windows.

### 2. Windows Listener & Web Server (`Windows_Machine/`)
- **`config.py`**: Config for TCP IP/Port (`0.0.0.0:5003`) and WebSocket/HTTP Server (`0.0.0.0:8000`).
- **`agent/listener.py`**: Multi-threaded service hosting:
  - **TCP Server**: Collects and ingests metric payloads from agents.
  - **State Manager**: Thread-safe in-memory cache maintaining system state and 50-item rolling alert history.
  - **WebSocket / REST Server**: Streams state changes live to browser clients over WebSockets with HTTP GET `/api/state` fallback.

### 3. Frontend Dashboard (`Windows_Machine/dashboard/frontend/`)
- **React + Vite**: Built with vanilla CSS glassmorphism, responsive grid layouts, custom hooks (`useWebSocket.js`), searchable process explorer, hardware gauges, and real-time security alert ticker.
