# API

All paths below are implemented by the FastAPI gateway on internal port `8500` unless noted. Protected routes require `Authorization: Bearer <access-token>`.

## Authentication

| Method | Path | Request | Auth | Response/errors |
|---|---|---|---|---|
| POST | `/auth/login` | `{username,password}` | public | access/refresh token and user; `401`, `429` |
| POST | `/auth/refresh` | `{refresh_token}` | public | rotated token pair; `401` |
| POST | `/auth/logout` | optional refresh token | optional bearer | success; invalid body/auth behavior follows route dependencies |
| GET | `/auth/me` | none | bearer | current user; `401`/`404` |
| GET | `/auth/users` | none | admin | user list; `401`/`403` |
| POST | `/auth/users` | username, password, role, optional profile fields | admin | created user; `400` |
| PUT | `/auth/users/{user_id}` | optional role/status/profile/password | admin | updated user; `400`/`404` |
| DELETE | `/auth/users/{user_id}` | none | admin | success; `400` self-delete or `404` |

## Monitoring and History

| Method | Path | Query/body | Auth |
|---|---|---|---|
| GET | `/health` | none | public |
| GET | `/api/v1/history/hardware` | `host,start,end,limit` (1-1000) | bearer |
| GET | `/api/v1/history/docker` | `host,container,start,end,limit` | bearer |
| GET | `/api/v1/history/summary` | `host` | bearer |
| GET | `/api/v1/http/recent` | `limit` (1-1000) | bearer |
| GET | `/api/v1/http/history` | `start,end,limit` | bearer |
| GET | `/api/v1/hosts/status` | none | bearer |
| GET | `/api/v1/docker/state` | none | bearer |

History responses use `status`, `count` where applicable, filters, and `data`; summary returns `summary`. Exact metric fields derive from the database repositories and collector payloads.

## Docker Proxy

`GET /api/v1/docker/containers?all=true`, `GET /api/v1/docker/containers/{container_id}`, `GET .../logs?tail=100&since=<unix>`, and `GET .../stats` require a bearer token and forward to Kali. `POST` to `/start`, `/stop`, or `/restart` requires `admin` or `operator`; gateway errors include `502` for connection failure, `504` for timeout, and `500` for unexpected gateway errors.

## WebSocket and State

- WebSocket: `/ws` on internal port `8000`, proxied by Nginx. JWT is accepted from `?token=` or `Authorization: Bearer` during upgrade. Server sends unmasked text frames containing state snapshots and event objects.
- State fallback: exact `/api/state` on port `8000`, returns a JSON snapshot from the raw bridge. Its bridge path has no verified auth check.

No other API or WebSocket path was verified from the source.
