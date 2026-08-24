# Kali Machine Agent

## Overview

The Kali component is a Python process that collects local telemetry, sends it to `WINDOWS_HOST:PORT`, and starts a FastAPI command receiver in a daemon thread. It is external to the Windows Docker Compose network.

## Components

| Component | Source | Behavior |
|---|---|---|
| Sender | `agent/sender.py` | Connects, sends snapshots, then loops on metrics and changes. |
| CPU/RAM/disk/network/process collectors | `collector/` | Read local system statistics through Python system libraries. |
| Network/process/Docker monitors | `monitor/` | Detect changes and produce event lists. Docker is optional. |
| Command receiver | `agent/command_receiver.py` | Binds `0.0.0.0:8501` and performs local Docker operations. |

## Configuration

Required: `WINDOWS_HOST`, `HOMEOPS_API_KEY`, `JWT_SECRET`. Defaults: `PORT=5003`, `METRIC_INTERVAL=5`, `HEARTBEAT_INTERVAL=5`, `RECONNECT_DELAY=3`, `DOCKER_TELEMETRY_INTERVAL=10`, `COMMAND_API_HOST=0.0.0.0`, `COMMAND_API_PORT=8501`, `CPU_THRESHOLD=20`, `MEM_THRESHOLD=5`, and `JWT_ALGORITHM=HS256`.

`0.0.0.0` is a bind address, not the Windows destination. The configured API key is not used by the active command-receiver authentication path.

## Telemetry and Lifecycle

Messages are UTF-8 JSON preceded by a 4-byte network-order unsigned length. Initial messages are `INITIAL_NETWORK_SNAPSHOT`, `INITIAL_PROCESS_SNAPSHOT`, and optional `DOCKER_TELEMETRY`. The loop sends `HARDWARE_METRICS` every `METRIC_INTERVAL`; heartbeats run every `HEARTBEAT_INTERVAL`; Docker telemetry runs every `DOCKER_TELEMETRY_INTERVAL`; event messages are sent when changes exist.

The sender uses a 10-second connect timeout, resets to blocking mode after connection, and retries after refusal, timeout, reset, broken pipe, or another loop exception. The default retry delay is 3 seconds. Windows marks a host offline after more than 30 seconds without a heartbeat. See [../docs/TELEMETRY_PROTOCOL.md](../docs/TELEMETRY_PROTOCOL.md).

## Command Receiver

`GET /health` is unauthenticated. Docker list/get/log/stats and start/stop/restart routes require a JWT with role `admin` or `operator`. API-key fallback is not implemented in the receiver. A service definition is not present, so running as a system service is not verified.

## Installation and Running

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export WINDOWS_HOST=<WINDOWS_HOST>
python agent/sender.py
```

Run from `Kali_Machine`. Docker telemetry is disabled when the Docker SDK or local daemon is unavailable. Missing required variables fail at import time outside test mode.

## Limitations and Troubleshooting

There is no TLS, telemetry authentication, payload-size limit, or repository firewall rule. The receiver binds all interfaces by default. For connection failures verify `WINDOWS_HOST`, Windows port `5003`, listener startup, and firewall rules. For command failures verify `KALI_COMMAND_URL`, receiver port `8501`, and the forwarded JWT role.
