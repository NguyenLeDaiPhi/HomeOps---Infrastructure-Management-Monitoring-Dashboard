"""
HTTP Request Monitoring Middleware for FastAPI.

Intercepts every HTTP request, measures latency, extracts metadata,
persists the record to PostgreSQL asynchronously, and broadcasts the
event to connected WebSocket dashboard clients.

Performance target: < 5ms additional latency per request.
"""

import uuid
import time
import asyncio
import logging
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("HttpMonitorMiddleware")


def extract_client_ip(request: Request) -> str:
    """Extracts client IP with proxy-aware priority.

    Priority:
        1. X-Forwarded-For (first IP in comma-separated list)
        2. X-Real-IP
        3. request.client.host
    """
    # X-Forwarded-For: may contain multiple IPs (client, proxy1, proxy2, ...)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    if request.client:
        return request.client.host

    return "unknown"


class HttpMonitorMiddleware(BaseHTTPMiddleware):
    """Middleware that logs every HTTP request/response cycle.

    For each request it:
    1. Generates a unique request ID (UUID4)
    2. Records the request start time
    3. Calls the downstream endpoint
    4. Measures latency
    5. Extracts client IP, method, path, status code, user-agent, sizes
    6. Fires an async background task to persist + broadcast (non-blocking)
    7. Returns the original response unmodified
    """

    def __init__(self, app, save_fn=None, broadcast_fn=None):
        """
        Args:
            app: The ASGI application.
            save_fn: Callable to persist a request log dict. Runs in executor.
            broadcast_fn: Callable to broadcast a WebSocket message dict.
        """
        super().__init__(app)
        self._save_fn = save_fn
        self._broadcast_fn = broadcast_fn

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate unique request ID and record start time
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()
        timestamp = datetime.now(timezone.utc)

        # Call the downstream endpoint
        response = await call_next(request)

        # Compute latency
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Extract request metadata
        client_ip = extract_client_ip(request)
        method = request.method
        path = request.url.path
        status_code = response.status_code
        user_agent = request.headers.get("user-agent", "")

        # Bytes in: Content-Length header from request (may be absent)
        bytes_in = None
        content_length_in = request.headers.get("content-length")
        if content_length_in:
            try:
                bytes_in = int(content_length_in)
            except (ValueError, TypeError):
                pass

        # Bytes out: Content-Length header from response (may be absent)
        bytes_out = None
        content_length_out = response.headers.get("content-length")
        if content_length_out:
            try:
                bytes_out = int(content_length_out)
            except (ValueError, TypeError):
                pass

        # Build the log record
        log_record = {
            "request_id": request_id,
            "timestamp": timestamp.isoformat(),
            "client_ip": client_ip,
            "method": method,
            "path": path,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "user_agent": user_agent,
            "bytes_in": bytes_in,
            "bytes_out": bytes_out,
        }

        # Fire-and-forget async task for persistence + broadcast
        asyncio.create_task(self._process_log(log_record))

        return response

    async def _process_log(self, log_record: dict):
        """Persists the log record and broadcasts to WebSocket clients.

        Runs DB write in a thread executor to avoid blocking the event loop.
        All exceptions are caught and logged — never crashes the server.
        """
        # Persist to PostgreSQL in a thread executor (synchronous DB call)
        if self._save_fn:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._save_fn, log_record)
            except Exception as e:
                logger.error(f"Failed to persist HTTP request log: {e}")

        # Broadcast to WebSocket clients
        if self._broadcast_fn:
            try:
                ws_message = {
                    "type": "HTTP_REQUEST_EVENT",
                    "request_id": log_record["request_id"],
                    "timestamp": log_record["timestamp"],
                    "client_ip": log_record["client_ip"],
                    "method": log_record["method"],
                    "path": log_record["path"],
                    "status_code": log_record["status_code"],
                    "latency_ms": log_record["latency_ms"],
                }
                self._broadcast_fn(ws_message)
            except Exception as e:
                logger.error(f"Failed to broadcast HTTP request event: {e}")
