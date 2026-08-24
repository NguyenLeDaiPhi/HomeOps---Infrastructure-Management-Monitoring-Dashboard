# Windows Monitoring Platform

## Overview

The Windows side is a Python service plus React dashboard deployment. `agent/windows_listen/listener.py` initializes the database, starts retention and heartbeat workers, then runs the TCP telemetry listener, raw HTTP/WebSocket bridge, and FastAPI command gateway in daemon threads.

## Runtime Architecture

| Service | Bind/port | Role |
|---|---|---|
| TCP listener | `LISTENER_IP:PORT`, default `0.0.0.0:5003` | Receives Kali framed telemetry. |
| Web bridge | `WEBSOCKET_HOST:WEBSOCKET_PORT`, default `0.0.0.0:8000` | Manual WebSocket `/ws` and state `/api/state`. |
| FastAPI gateway | `COMMAND_API_HOST:COMMAND_API_PORT`, default `0.0.0.0:8500` | Auth, history, monitoring, and Docker proxy APIs. |
| PostgreSQL | `postgres:5432` | Persistent storage; not published to host. |
| Nginx | host `80` | Browser entry point and reverse proxy. |

Compose services are `postgres`, `monitoring-server`, `frontend`, and `nginx`; container names are `homeops-postgres`, `monitoring-server`, `homeops-frontend`, and `homeops-nginx`.

## Backend and Data

Telemetry updates locked in-memory state, broadcasts WebSocket snapshots, and queues selected writes through a five-worker executor. A one-second worker marks hosts offline after 30 seconds. Retention runs every 24 hours and defaults to 30 days for hardware, Docker, connection events, and HTTP logs. Schema initialization uses SQLAlchemy `create_all()`; no migration scripts were found.

Nginx sends `/auth/` and `/api/` to `monitoring-server:8500`, `/ws` and exact `/api/state` to `monitoring-server:8000`, and other paths to `frontend:80`. The gateway forwards Docker commands over HTTP to `KALI_COMMAND_URL`.

## Frontend

Vite builds the React SPA. Routes are `/login`, `/dashboard`, `/infrastructure`, `/docker`, `/network`, `/processes`, `/events`, `/history`, `/http-monitor`, `/settings`, and `/users`. Docker requires `admin` or `operator`; settings and users require `admin`. The main WebSocket hook supplies a token, while `useHttpMonitor` and `useHostStatus` create tokenless sockets and rely on polling when rejected.

## Deployment

From this directory, create `.env` from the supplied examples and run:

```powershell
docker compose up --build
docker compose ps
```

PostgreSQL health gates monitoring-server startup; frontend and Nginx only wait for service start. The monitoring health check probes only TCP `5003`. No Windows service definition, TLS configuration, or host firewall configuration is present. See [../docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md) and [../docs/TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md).

## Security Limitations

JWT access/refresh tokens, bcrypt, RBAC, rate limiting, and audit records are implemented. Current risks include seeded `admin` / `admin123`, wildcard CORS with credentials, plaintext transport, localStorage tokens, query-string WebSocket tokens, unauthenticated telemetry TCP, and the broken gateway API-key fallback (`WindowsConfig.API_KEY` does not exist).
