HomeOps — Infrastructure Management & Monitoring Dashboard

Overview
- Purpose: Centralized monitoring and control for Linux (Kali) and Windows hosts using lightweight agents that stream telemetry to a Windows-based listener + FastAPI gateway and a React/Vite dashboard.
- Key Components:
  - Kali agent: collects system metrics and exposes a local command receiver for Docker control.
  - Windows monitoring server: TCP listener for framed JSON telemetry, WebSocket/HTTP bridge for dashboard real-time updates, FastAPI command gateway, and PostgreSQL persistence.
  - Frontend: React + Vite dashboard that connects via WebSocket (real-time) and falls back to polling `/api/state`.
  - Orchestration: Docker Compose for local development with `nginx` reverse proxy.

Quick start (local dev)
1. Copy example env files and edit as needed:

   - Kali dev `.env` sample: `Kali_Machine/.env.example`
   - Windows dev `.env` sample: `Windows_Machine/.env.example`

   Example (recommended local values):
   - Windows host IP: your local ip
   - Kali host IP: your local ip

2. From `Windows_Machine/` run (requires Docker):

```powershell
# from Windows_Machine directory
docker compose up --build
```

3. Open the dashboard in your browser via the host running `nginx` (default http://localhost).

Configuration (env-driven)
- All environment-specific configuration is provided via environment variables or `.env` files (12‑factor).
- Primary env files and keys (see docs/CONFIGURATION.md for full matrix):
  - `Windows_Machine/.env` (or env injection in compose): `DATABASE_URL`, `JWT_SECRET`, `HOMEOPS_API_KEY`, `KALI_COMMAND_URL`, `PORT`, `WEBSOCKET_PORT`, etc.
  - `Kali_Machine/.env`: `WINDOWS_HOST`, `PORT`, `COMMAND_API_PORT`, `HOMEOPS_API_KEY`, `JWT_SECRET`, etc.
- Runtime validation: services validate presence of required env vars on startup; tests set `SKIP_ENV_VALIDATION=1` when needed.

Testing
- Unit tests are in `Windows_Machine/agent/tests/` and use an in-memory SQLite DB by setting `DATABASE_URL="sqlite:///:memory:"`.
- To run tests locally (example from repository root):

```powershell
# from Windows_Machine/agent
setx SKIP_ENV_VALIDATION 1
pytest -q
```

Notes & next steps
- Security: the repo now centralizes secrets in env files; review `docs/SECURITY.md` for hardening recommendations (TLS, remove default admin seeding, API-key mismatch).
- Deployment: see `docs/DEPLOYMENT.md` for production deployment suggestions (TLS termination, secret management, migrations).

Files created by this guide
- `docs/CONFIGURATION.md` — env variables and examples
- `docs/DEPLOYMENT.md` — deployment and docker-compose notes
- `docs/SECURITY.md` — security findings and recommendations

If you'd like, I can now (select one):
- Convert this generated README into the primary `README.md` (overwrite), or
- Add a short `README` inside `Windows_Machine/` and `Kali_Machine/` as per your repo layout.
