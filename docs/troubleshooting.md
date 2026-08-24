# Troubleshooting

## Nginx or Frontend

**Symptoms:** `502`, blank UI, or API failures. **Causes:** `monitoring-server`/`frontend` is stopped, wrong internal route, or gateway/bridge thread failed. **Commands:** `docker compose ps`; `docker compose logs nginx monitoring-server frontend`; `curl http://localhost/`. **Resolution:** rebuild/start Compose, inspect the target service logs, and confirm Nginx routes `/api/` and `/auth/` to `8500`, `/ws` and `/api/state` to `8000`.

## Backend or Database

**Symptoms:** unhealthy monitoring service, history/auth errors. **Causes:** missing required environment values, PostgreSQL unavailable, or schema initialization failure. **Commands:** `docker compose ps`; `docker compose logs postgres monitoring-server`; `docker compose exec postgres pg_isready -U homeops -d homeops`. **Resolution:** create the required `.env`, verify `DATABASE_URL` points to `postgres:5432`, wait for the PostgreSQL health check, and inspect Python startup errors.

**Note:** the Compose health check only tests TCP `5003`; it does not prove the gateway, WebSocket bridge, or database operations are healthy.

## Kali TCP Connection

**Symptoms:** agent reports connection refused, or host stays offline. **Causes:** incorrect `WINDOWS_HOST`, listener not running, host firewall, wrong port, or Windows container not publishing `5003`. **Commands:** on Windows `docker compose logs monitoring-server`; on Kali `python agent/sender.py`; from Kali use an available TCP test such as `nc -vz <WINDOWS_HOST> 5003`. **Resolution:** use the reachable Windows host value, not `0.0.0.0`, confirm `PORT=5003`, and permit inbound TCP `5003`.

## WebSocket

**Symptoms:** live updates fail while polling works. **Causes:** invalid/missing JWT, Nginx upgrade routing, or a tokenless secondary hook. **Commands:** inspect browser network requests for `/ws`; `docker compose logs nginx monitoring-server`. **Resolution:** use a valid access token, verify the `/ws` proxy, and remember that `useHttpMonitor` and `useHostStatus` currently omit tokens and fall back to polling.

## Authentication

**Symptoms:** login returns `401` or `429`. **Causes:** wrong credentials, inactive user, expired/invalid token, database failure, or five attempts within the five-minute IP window. **Resolution:** verify database connectivity and credentials, wait for rate limiting, and use `/auth/refresh` with a valid refresh token. First-start seeding creates `admin` / `admin123`; change that credential before any exposed use.

## Commands and Docker

**Symptoms:** Docker actions return `502`, `504`, `401`, or `403`. **Causes:** Kali receiver unreachable, command timeout, missing bearer role, Docker daemon unavailable, or broken API-key fallback. **Resolution:** verify `KALI_COMMAND_URL` reaches `<KALI_HOST>:8501`, receiver logs and Docker access, a valid `admin`/`operator` JWT, and `COMMAND_TIMEOUT`. API-key fallback is not a working alternative.

## Data and Agent State

**Symptoms:** no Docker data, malformed packet logs, or stale state. **Causes:** Docker SDK/daemon unavailable, invalid JSON, agent disconnect, or database write failure. **Resolution:** inspect sender and monitoring logs, verify the agent reconnects after the default 3-second delay, and check PostgreSQL separately. Live state can continue in memory while asynchronous database writes fail and log errors.

## Docker DNS and Ports

**Symptoms:** `postgres` or `monitoring-server` cannot resolve. **Causes:** services are not on network `homeops`, wrong service name, or Compose project not started from `Windows_Machine`. **Commands:** `docker network inspect homeops`; `docker compose ps`. **Resolution:** use service names `postgres`, `monitoring-server`, and `frontend`, recreate the Compose stack, and keep internal ports distinct from published ports.
