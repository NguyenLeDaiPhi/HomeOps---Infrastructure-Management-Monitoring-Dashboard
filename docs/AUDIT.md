# Repository Audit

Audit basis: source code, Compose/Nginx configuration, frontend routes/hooks, database models, environment examples, and focused tests. Existing prose was treated as non-authoritative.

## Findings

- **Architecture:** external Kali sender and command receiver; Windows Python process with TCP listener, raw WebSocket/state bridge, FastAPI gateway, background workers, PostgreSQL; React/Vite frontend and Nginx in Compose.
- **Implemented:** framed telemetry ingestion, collectors and change monitors, in-memory state, heartbeat timeout, selected asynchronous persistence, JWT/RBAC, bcrypt, refresh rotation, REST history/status/Docker APIs, frontend routes, Nginx routing.
- **Partial:** WebSocket consumers, retention reporting, multi-host behavior, Compose health verification, command flow.
- **Broken/inconsistent:** gateway fallback references `WindowsConfig.API_KEY` instead of `HOMEOPS_API_KEY`; old Windows startup path is wrong; older docs used `0.0.0.0` as a destination and reported retry delay 5 seconds.
- **Security concerns:** unauthenticated plaintext telemetry, no TLS, unrestricted CORS with credentials, localStorage/query-string tokens, default seeded credentials, unrestricted bind addresses, no payload-size limit.
- **Deployment concerns:** `.env` is required but not committed; PostgreSQL credentials are Compose literals; only TCP 5003 is health-checked; no service/firewall/TLS/migration deployment artifacts.
- **Test gaps:** no verified Compose, Nginx, PostgreSQL, TCP interoperability, authenticated WebSocket, gateway-to-Kali, Docker daemon, or frontend runtime end-to-end coverage.

## Documentation Improvements Applied

Canonical root, Kali, Windows, architecture, networking, security, API, telemetry protocol, deployment, troubleshooting, and configuration documents now use service names `postgres`, `monitoring-server`, `frontend`, `nginx`, ports `80`, `5003`, `8000`, `8500`, and `8501`, and placeholders `<WINDOWS_HOST>` / `<KALI_HOST>` for environment-specific addresses.
