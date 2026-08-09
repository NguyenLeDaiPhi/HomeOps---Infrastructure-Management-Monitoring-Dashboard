# HomeOps Telemetry & Monitoring System Architecture

## Overview
HomeOps is an infrastructure monitoring solution designed to be network-agnostic and deployable using environment-driven configuration. Telemetry is collected by a **Kali Linux Agent** and streamed to a **Windows Host Listener Server**, then visualized in a React dashboard.

---

## High-Level Data Flow

```
+------------------------------------+                    +---------------------------------------+
|        Kali Linux VM               |                    |             Windows Host              |
|                                    |                    |                                       |
|  [Collectors: CPU, RAM, Disk, Net] |                    |  [TCP Listener Server (Port 5003)]    |
|                 |                  |                    |                  |                    |
|  [Monitors: Net & Process Events]  |                    |          [State Manager]              |
|                 |                  |                    |                  |                    |
|   [Sender Agent TCP Client]        | === TCP Socket ===>  [WebSocket & HTTP Bridge (8000)]|
|   (Length-Prefixed Binary Header)  |                    |                  |                    |
+------------------------------------+                    +------------------|--------------------+
                                                                             | WebSocket / REST
                                                                             v
                                                          +---------------------------------------+
                                                          |           React Live Dashboard        |
                                                          |         (development: http://localhost:5173)
                                                          +---------------------------------------+
```

---

## Framing & Communication Protocol
- **Transport Layer**: TCP Sockets (`socket.AF_INET`, `socket.SOCK_STREAM`).
- **Framing**: Each JSON telemetry payload is prefixed with a 4-byte big-endian unsigned integer header specifying message byte length (`struct.pack("!I", len(payload))`).
- **Resilience**: The Kali sender features auto-reconnection and backoff retries. The Windows listener features socket context management and safe JSON exception handling.

---

## Component Breakdown

### 1. Kali Linux Agent (`Kali_Machine/`)
- **`config.py`**: Centralized configuration management using environment variables and `.env` files.
- **`collector/`**:
  - `cpu.py`: Non-blocking CPU frequency, core counts, load averages.
  - `ram.py`: Virtual memory and Swap memory utilization.
  - `disk.py`: Disk partition mount points, free space, and standardized `fstype` schema.
  - `network.py`: Cross-platform link layer interface detection and IPv4/MAC mappings.
  - `process.py`: Safe process snapshot iterators catching `NoSuchProcess`, `AccessDenied`, and `ZombieProcess`.
- **`monitor/`**:
  - `network_monitor.py`: Interface state change detection.
  - `process_monitor.py`: Fixed resource spike detection (`HIGH_CPU`, `HIGH_MEMORY`) and process lifecycle events (`PROCESS_STARTED`, `PROCESS_STOPPED`).
- **`agent/sender.py`**: Main background agent connecting to the Windows listener.

### 2. Windows Listener & Web Server (`Windows_Machine/`)
- **`config.py`**: All runtime configuration is provided through environment variables and loaded with `python-dotenv` in development.
- **`agent/listener.py`**: Multi-threaded service hosting:
  - **TCP Server**: Collects and ingests metric payloads from agents.
  - **State Manager**: Thread-safe in-memory cache maintaining system state and a rolling alert history.
  - **WebSocket / REST Server**: Streams state changes live to browser clients over WebSockets with HTTP GET `/api/state` fallback.

### 3. Frontend Dashboard (`Windows_Machine/dashboard/frontend/`)
- **React + Vite**: Built with vanilla CSS glassmorphism, responsive grid layouts, custom hooks (`useWebSocket.js`), searchable process explorer, hardware gauges, and real-time security alert ticker. The frontend reads runtime endpoints from `import.meta.env` or `window.location.hostname`.

Configuration notes:
- Services and Docker containers should communicate using service names (for example, `monitoring-server`, `kali-agent`, `postgres`) rather than physical IP addresses.
- Sensitive values (API keys, JWT secrets, database URLs) must be supplied as environment variables and not committed to source control. Example `.env.example` files are provided under each machine folder.
