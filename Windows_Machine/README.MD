# HomeOps - Infrastructure Management & Monitoring Dashboard

An infrastructure monitoring platform designed for real-time telemetry streaming between a **Kali Linux Virtual Machine (192.168.2.2)** and a **Windows Host Machine (192.168.2.1)** over host-only networking.

---

## Key Features

- ⚡ **Real-Time Web Dashboard**: High-tech glassmorphism UI with live hardware gauges (CPU, RAM, Disk), network interface status cards, searchable active process manager, and real-time security event feed.
- 🔁 **Auto-Reconnecting Agent**: Kali Linux telemetry agent auto-reconnects with backoff retries when connection is interrupted.
- 🔒 **Safe TCP Framing & Resilience**: 4-byte big-endian binary length header framing to prevent TCP message chunk fragmentation; safe JSON parsing keeps server running during corrupt packets.
- 🌐 **Dual Protocol Bridge**: Windows listener provides both real-time WebSocket broadcasting (`ws://localhost:8000`) and REST API fallback (`http://localhost:8000/api/state`).
- 🛠️ **Production Best Practices**: Modular Python package structure, `logging` system, thread-safe in-memory state manager, type hints, and centralized configuration.

---

## Directory Structure

```
HomeOps/
├── Kali_Machine/              # Kali Linux VM Agent
│   ├── config.py              # Configuration (Windows IP, Port, Thresholds)
│   ├── agent/
│   │   └── sender.py          # Telemetry client agent
│   ├── collector/             # Hardware & system collectors (CPU, RAM, Disk, Net, Proc)
│   └── monitor/               # Delta change monitors (Process & Network)
│
└── Windows_Machine/           # Windows Host Server & Dashboard
    ├── config.py              # Windows listener configuration
    ├── agent/
    │   └── listener.py        # Multi-threaded TCP Listener & WebSocket Bridge
    ├── dashboard/
    │   └── frontend/          # React + Vite Glassmorphism Live Dashboard
    └── docs/
        └── ARCHITECTURE.md    # System Architecture Document
```

---

## Quick Start Guide

### 1. Run Windows Telemetry Service (Windows Machine)
```powershell
cd d:\Management-Infra\HomeOps---Infrastructure-Management-Monitoring-Dashboard\Windows_Machine
python agent/listener.py
```
*Listens for Kali TCP metrics on port `5003` and starts WebSocket server on port `8000`.*

### 2. Run Kali Telemetry Agent (Kali Linux VM)
```bash
cd Kali_Machine
python3 agent/sender.py
```
*Connects to `192.168.2.1:5003` and starts transmitting telemetry.*

### 3. Launch React Dashboard (Windows Machine)
```powershell
cd Windows_Machine/dashboard/frontend
npm install
npm run dev
```
Open browser at `http://localhost:5173`.

---

## Future Roadmap

1. **Persistent Time-Series Database**: Integrate SQLite or TimescaleDB to record 24-hour metric history and interactive graphs.
2. **TLS Encryption**: Add SSL/TLS certificates over TCP socket framing for secure cross-network deployment.
3. **Multi-Host Agent Monitoring**: Add unique host identifiers and token authentication to monitor multiple Linux VMs simultaneously.
