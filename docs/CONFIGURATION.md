# Configuration

Configuration is read with `python-dotenv` and environment variables. The active source configuration is authoritative; `.env` files are not committed.

## Windows (`Windows_Machine/.env`)

Required at startup: `HOMEOPS_API_KEY`, `JWT_SECRET`, `DATABASE_URL`, and `KALI_COMMAND_URL`. Defaults: `LISTENER_IP=0.0.0.0`, `PORT=5003`, `WEBSOCKET_HOST=0.0.0.0`, `WEBSOCKET_PORT=8000`, `COMMAND_API_HOST=0.0.0.0`, `COMMAND_API_PORT=8500`, `COMMAND_TIMEOUT=30.0`, `ACCESS_TOKEN_EXPIRE_MINUTES=15`, `REFRESH_TOKEN_EXPIRE_DAYS=7`, and `JWT_ALGORITHM=HS256`.

## Kali (`Kali_Machine/.env`)

Required at startup: `WINDOWS_HOST`, `HOMEOPS_API_KEY`, and `JWT_SECRET`. Defaults: `PORT=5003`, `METRIC_INTERVAL=5.0`, `HEARTBEAT_INTERVAL=5.0`, `RECONNECT_DELAY=3.0`, `DOCKER_TELEMETRY_INTERVAL=10.0`, `CPU_THRESHOLD=20.0`, `MEM_THRESHOLD=5.0`, `COMMAND_API_HOST=0.0.0.0`, `COMMAND_API_PORT=8501`, and `JWT_ALGORITHM=HS256`.

## Frontend Vite Variables

`VITE_API_URL` defaults to same-origin `/api/state`; `VITE_WS_URL` defaults to same-origin `/ws`; `VITE_DOCKER_API_URL` defaults to same-origin `/api/v1/docker`; and `VITE_KALI_TARGET` defaults to the browser hostname. These are build-time frontend values, not backend secrets.

## Example

```env
DATABASE_URL=postgresql://homeops:<PASSWORD>@postgres:5432/homeops
JWT_SECRET=<RANDOM_SECRET>
HOMEOPS_API_KEY=<RANDOM_KEY>
KALI_COMMAND_URL=http://<KALI_HOST>:8501
WINDOWS_HOST=<WINDOWS_HOST>
```

Compose hard-codes the PostgreSQL database name/user/password as `homeops`; production secret handling is not provided. `SKIP_ENV_VALIDATION=1` is used only where tests intentionally bypass import-time checks.