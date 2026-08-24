# Security

## Implemented

- HS256 JWT access tokens, default expiry 15 minutes.
- Refresh tokens, default expiry 7 days, rotated and stored as SHA-256 hashes.
- bcrypt password hashing.
- Roles `admin`, `operator`, and `viewer`; admin-only user management; admin/operator Docker mutations.
- In-memory login rate limit of five attempts per IP in five minutes.
- Audit rows for authentication and administrative actions.
- WebSocket JWT validation when a token is supplied by query string or bearer header.
- Environment-based required secrets at startup.

## Partial or Not Implemented

- Raw TCP telemetry on `5003` accepts clients without authentication, source validation, encryption, or a maximum payload length.
- HTTP and WebSocket traffic is plaintext; TLS/certificates are not configured.
- CORS uses `allow_origins=["*"]` with credentials enabled.
- Browser tokens are stored in `localStorage`; WebSocket query-string tokens can enter proxy logs.
- The default database initialization creates `admin` with password `admin123` if absent.
- Kali's configured API key is not accepted by its active receiver, and the gateway fallback references nonexistent `WindowsConfig.API_KEY`.
- Docker receiver binds `0.0.0.0:8501`; repository firewall restrictions are absent.
- `/api/state` is served by the raw bridge without a verified auth check.

## Attack Surface

Exposed host ports are Nginx `80` and telemetry TCP `5003`; Kali exposes command receiver `8501` according to its bind configuration. The gateway, raw bridge, database, Docker SDK, environment secrets, and browser storage are additional trust boundaries. Treat telemetry injection and command forwarding as risks until network restrictions and transport authentication are added.

## Recommended Future Improvements

Use TLS or a private authenticated channel for all cross-host traffic; authenticate and authorize the telemetry handshake; enforce payload size and schema validation; restrict CORS and ingress; remove default credentials; use secure, short-lived cookie or memory-based token handling; replace query-string WebSocket tokens; implement migrations; and add firewall rules, secret rotation, and end-to-end security tests.
