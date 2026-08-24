# Deployment

## Prerequisites

Docker Desktop with Compose is required for the Windows stack. Kali requires Python and its requirements; Docker SDK access is required for Docker telemetry/control. The two hosts must route to each other on the telemetry and command ports.

## Environment

Create `Windows_Machine/.env` from its example and set `HOMEOPS_API_KEY`, `JWT_SECRET`, `DATABASE_URL`, and `KALI_COMMAND_URL`; optional Windows bind, port, timeout, and JWT settings are documented in [CONFIGURATION.md](CONFIGURATION.md). Create `Kali_Machine/.env` with `WINDOWS_HOST`, `HOMEOPS_API_KEY`, and `JWT_SECRET`, plus optional interval/threshold settings. Use `<WINDOWS_HOST>` and `<KALI_HOST>` placeholders in shared instructions and keep secrets out of source control.

Compose hard-codes the PostgreSQL database name/user/password as `homeops` and uses `DATABASE_URL` for the monitoring process. The repository does not provide a production secret override for those Compose values.

## Compose

From `Windows_Machine`:

```powershell
docker compose up --build
docker compose ps
docker compose logs -f monitoring-server
```

Services are `postgres`, `monitoring-server`, `frontend`, and `nginx`, all on bridge network `homeops`. Volume `postgres_data` stores PostgreSQL data. Host ports are `80:80` and `5003:5003`; ports `8000` and `8500` are exposed only inside the network. PostgreSQL uses `postgres:5432` internally. Compose waits for PostgreSQL health before starting monitoring-server, but frontend/Nginx wait only for service start. Monitoring health checks only TCP `5003`.

## Kali Connectivity

Run the sender from `Kali_Machine` after setting `WINDOWS_HOST` to the reachable Windows host name/address. The Windows firewall and Docker Desktop networking must allow inbound TCP `5003`. For remote Docker control, `KALI_COMMAND_URL` must reach the Kali receiver at port `8501`.

## Development

Run the Windows listener directly with `python windows_listen/listener.py` from `Windows_Machine/agent`; run the sender with `python agent/sender.py`; run the frontend with `npm run dev`. The old path `python agent/listener.py` is invalid. A Windows service definition is not present.

## Production Considerations

The current files do not establish TLS, authenticated telemetry, restricted CORS, firewall rules, secret rotation, migration execution, complete health checks, or end-to-end deployment tests. Do not treat the Compose configuration as production-ready without addressing these gaps.
