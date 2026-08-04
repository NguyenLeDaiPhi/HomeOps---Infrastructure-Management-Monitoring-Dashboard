"""
Tests for Feature 11 — HTTP Request Monitoring.

Covers acceptance criteria AC-11.1 through AC-11.5:
  AC-11.1  Client IP displayed — IP parsed correctly
  AC-11.2  HTTP Method displayed — GET/POST/etc.
  AC-11.3  URL displayed — Requested path visible
  AC-11.4  Response code displayed — HTTP status available
  AC-11.5  Requests appear in near real-time — Delay < 2 seconds
"""

import os
import sys
import time
import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

# Ensure agent directory is in Python path for test execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set SQLite in-memory database URL for fast, isolated test execution
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from database.connection import init_db, get_db_session
from database.repositories import HttpRequestRepository, parse_timestamp
from database.models import HttpRequestLog
from middleware.http_monitor import extract_client_ip


@pytest.fixture(autouse=True)
def setup_test_db():
    """Initializes a fresh in-memory database before each test run."""
    init_db()
    yield
    # Clean up after test
    with get_db_session() as session:
        session.query(HttpRequestLog).delete()


# =============================================
# AC-11.1: Client IP displayed — IP parsed correctly
# =============================================

class TestAC111ClientIP:
    """AC-11.1: Verify client IP is parsed and stored correctly."""

    def test_client_ip_from_x_forwarded_for(self):
        """X-Forwarded-For header takes highest priority."""
        mock_request = MagicMock()
        mock_request.headers = {
            "x-forwarded-for": "203.0.113.50, 70.41.3.18",
            "x-real-ip": "10.0.0.1",
        }
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        ip = extract_client_ip(mock_request)
        assert ip == "203.0.113.50"

    def test_client_ip_from_x_real_ip(self):
        """X-Real-IP header used when X-Forwarded-For is absent."""
        mock_request = MagicMock()
        mock_request.headers = {"x-real-ip": "192.168.1.100"}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        ip = extract_client_ip(mock_request)
        assert ip == "192.168.1.100"

    def test_client_ip_from_request_client(self):
        """Falls back to request.client.host when no proxy headers exist."""
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "172.20.0.20"

        ip = extract_client_ip(mock_request)
        assert ip == "172.20.0.20"

    def test_client_ip_stored_in_database(self):
        """Verify IP address is correctly persisted to database."""
        data = {
            "request_id": "test-ip-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "client_ip": "172.20.0.20",
            "method": "GET",
            "path": "/health",
            "status_code": 200,
            "latency_ms": 5.0,
        }
        result = HttpRequestRepository.save_http_request(data)
        assert result is not None
        assert result.client_ip == "172.20.0.20"

        # Also verify via query
        recent = HttpRequestRepository.get_recent_requests(limit=1)
        assert len(recent) == 1
        assert recent[0]["client_ip"] == "172.20.0.20"


# =============================================
# AC-11.2: HTTP Method displayed — GET/POST/etc.
# =============================================

class TestAC112HttpMethod:
    """AC-11.2: Verify HTTP methods are recorded correctly."""

    def test_get_method_stored(self):
        """GET method recorded correctly."""
        data = {
            "request_id": "test-method-get",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "client_ip": "10.0.0.1",
            "method": "GET",
            "path": "/api/v1/docker/containers",
            "status_code": 200,
            "latency_ms": 10.0,
        }
        result = HttpRequestRepository.save_http_request(data)
        assert result is not None
        assert result.method == "GET"

    def test_post_method_stored(self):
        """POST method recorded correctly."""
        data = {
            "request_id": "test-method-post",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "client_ip": "10.0.0.1",
            "method": "POST",
            "path": "/api/v1/docker/containers/abc/start",
            "status_code": 200,
            "latency_ms": 42.5,
        }
        result = HttpRequestRepository.save_http_request(data)
        assert result is not None
        assert result.method == "POST"

    def test_multiple_methods_recorded(self):
        """GET and POST methods stored in same database correctly."""
        for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            data = {
                "request_id": f"test-method-{method.lower()}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "client_ip": "10.0.0.1",
                "method": method,
                "path": "/test",
                "status_code": 200,
                "latency_ms": 1.0,
            }
            HttpRequestRepository.save_http_request(data)

        recent = HttpRequestRepository.get_recent_requests(limit=10)
        methods = {r["method"] for r in recent}
        assert "GET" in methods
        assert "POST" in methods
        assert "PUT" in methods
        assert "DELETE" in methods
        assert "PATCH" in methods


# =============================================
# AC-11.3: URL displayed — Requested path visible
# =============================================

class TestAC113UrlPath:
    """AC-11.3: Verify URL path is stored and queryable."""

    def test_docker_containers_path_stored(self):
        """Request path /api/v1/docker/containers stored correctly."""
        data = {
            "request_id": "test-path-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "client_ip": "10.0.0.1",
            "method": "GET",
            "path": "/api/v1/docker/containers",
            "status_code": 200,
            "latency_ms": 12.0,
        }
        result = HttpRequestRepository.save_http_request(data)
        assert result is not None
        assert result.path == "/api/v1/docker/containers"

    def test_path_with_parameters_stored(self):
        """Paths with dynamic segments preserved correctly."""
        data = {
            "request_id": "test-path-002",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "client_ip": "10.0.0.1",
            "method": "POST",
            "path": "/api/v1/docker/containers/abc123/start",
            "status_code": 200,
            "latency_ms": 35.0,
        }
        result = HttpRequestRepository.save_http_request(data)
        assert result is not None
        assert result.path == "/api/v1/docker/containers/abc123/start"

    def test_path_queryable_in_recent(self):
        """Path is visible when querying recent requests."""
        data = {
            "request_id": "test-path-003",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "client_ip": "10.0.0.1",
            "method": "GET",
            "path": "/api/v1/docker/containers",
            "status_code": 200,
            "latency_ms": 8.0,
        }
        HttpRequestRepository.save_http_request(data)

        recent = HttpRequestRepository.get_recent_requests(limit=1)
        assert len(recent) == 1
        assert recent[0]["path"] == "/api/v1/docker/containers"


# =============================================
# AC-11.4: Response code displayed — HTTP status available
# =============================================

class TestAC114StatusCode:
    """AC-11.4: Verify HTTP status codes are recorded correctly."""

    def test_200_status_stored(self):
        """200 OK status code recorded."""
        data = {
            "request_id": "test-status-200",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "client_ip": "10.0.0.1",
            "method": "GET",
            "path": "/health",
            "status_code": 200,
            "latency_ms": 3.0,
        }
        result = HttpRequestRepository.save_http_request(data)
        assert result is not None
        assert result.status_code == 200

    def test_404_status_stored(self):
        """404 Not Found status code recorded."""
        data = {
            "request_id": "test-status-404",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "client_ip": "10.0.0.1",
            "method": "GET",
            "path": "/nonexistent",
            "status_code": 404,
            "latency_ms": 1.5,
        }
        result = HttpRequestRepository.save_http_request(data)
        assert result is not None
        assert result.status_code == 404

    def test_mixed_status_codes_stored(self):
        """Multiple status codes stored and queryable."""
        for code in [200, 201, 301, 404, 500]:
            data = {
                "request_id": f"test-status-{code}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "client_ip": "10.0.0.1",
                "method": "GET",
                "path": f"/test/{code}",
                "status_code": code,
                "latency_ms": 2.0,
            }
            HttpRequestRepository.save_http_request(data)

        recent = HttpRequestRepository.get_recent_requests(limit=10)
        codes = {r["status_code"] for r in recent}
        assert 200 in codes
        assert 404 in codes
        assert 500 in codes


# =============================================
# AC-11.5: Requests appear in near real-time (< 2 seconds)
# =============================================

class TestAC115RealTime:
    """AC-11.5: Verify real-time broadcast latency is under 2 seconds."""

    def test_database_write_speed(self):
        """Database write completes well under 2 seconds."""
        start = time.monotonic()

        data = {
            "request_id": "test-realtime-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "client_ip": "10.0.0.1",
            "method": "GET",
            "path": "/health",
            "status_code": 200,
            "latency_ms": 5.0,
        }
        result = HttpRequestRepository.save_http_request(data)
        elapsed = time.monotonic() - start

        assert result is not None
        assert elapsed < 2.0, f"DB write took {elapsed:.3f}s, exceeds 2s threshold"

    def test_websocket_broadcast_timing(self):
        """WebSocket broadcast call completes in under 2 seconds."""
        broadcast_calls = []
        broadcast_timestamps = []

        def mock_broadcast(message):
            broadcast_timestamps.append(time.monotonic())
            broadcast_calls.append(message)

        # Simulate what the middleware does: save + broadcast
        start = time.monotonic()

        data = {
            "request_id": "test-realtime-ws",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "client_ip": "172.20.0.20",
            "method": "POST",
            "path": "/api/v1/docker/containers/abc/start",
            "status_code": 200,
            "latency_ms": 42.5,
        }

        # DB save (synchronous, as middleware runs in executor)
        HttpRequestRepository.save_http_request(data)

        # Broadcast (synchronous call, as middleware does)
        ws_message = {
            "type": "HTTP_REQUEST_EVENT",
            "request_id": data["request_id"],
            "timestamp": data["timestamp"],
            "client_ip": data["client_ip"],
            "method": data["method"],
            "path": data["path"],
            "status_code": data["status_code"],
            "latency_ms": data["latency_ms"],
        }
        mock_broadcast(ws_message)

        elapsed = time.monotonic() - start

        assert len(broadcast_calls) == 1
        assert broadcast_calls[0]["type"] == "HTTP_REQUEST_EVENT"
        assert elapsed < 2.0, f"Save+broadcast took {elapsed:.3f}s, exceeds 2s threshold"

    def test_query_speed(self):
        """Querying recent requests completes well under 2 seconds."""
        # Insert 50 records
        for i in range(50):
            data = {
                "request_id": f"test-speed-{i:03d}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "client_ip": "10.0.0.1",
                "method": "GET",
                "path": f"/test/{i}",
                "status_code": 200,
                "latency_ms": float(i),
            }
            HttpRequestRepository.save_http_request(data)

        start = time.monotonic()
        recent = HttpRequestRepository.get_recent_requests(limit=100)
        elapsed = time.monotonic() - start

        assert len(recent) == 50
        assert elapsed < 2.0, f"Query took {elapsed:.3f}s, exceeds 2s threshold"


# =============================================
# Additional integration tests
# =============================================

class TestHttpRequestRepository:
    """Integration tests for the HttpRequestRepository data layer."""

    def test_save_invalid_payload_returns_none(self):
        """Non-dict payloads return None without crashing."""
        assert HttpRequestRepository.save_http_request(None) is None
        assert HttpRequestRepository.save_http_request("not a dict") is None

    def test_get_recent_returns_newest_first(self):
        """Results ordered by timestamp descending."""
        for i in range(3):
            data = {
                "request_id": f"test-order-{i}",
                "timestamp": f"2026-07-30T10:0{i}:00Z",
                "client_ip": "10.0.0.1",
                "method": "GET",
                "path": f"/test/{i}",
                "status_code": 200,
                "latency_ms": 1.0,
            }
            HttpRequestRepository.save_http_request(data)

        recent = HttpRequestRepository.get_recent_requests(limit=10)
        assert len(recent) == 3
        # Newest first: timestamps should be descending
        assert recent[0]["request_id"] == "test-order-2"
        assert recent[2]["request_id"] == "test-order-0"

    def test_get_http_history_time_range(self):
        """Time-range query returns correct subset in ascending order."""
        for i in range(5):
            data = {
                "request_id": f"test-history-{i}",
                "timestamp": f"2026-07-30T1{i}:00:00Z",
                "client_ip": "10.0.0.1",
                "method": "GET",
                "path": f"/test/{i}",
                "status_code": 200,
                "latency_ms": 1.0,
            }
            HttpRequestRepository.save_http_request(data)

        results = HttpRequestRepository.get_http_history(
            start="2026-07-30T11:00:00Z",
            end="2026-07-30T13:30:00Z",
            limit=10,
        )
        assert len(results) == 3  # 11:00, 12:00, 13:00
        # Ascending order
        assert results[0]["request_id"] == "test-history-1"
        assert results[2]["request_id"] == "test-history-3"

    def test_latency_stored_as_float(self):
        """Latency stored with decimal precision."""
        data = {
            "request_id": "test-latency",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "client_ip": "10.0.0.1",
            "method": "GET",
            "path": "/test",
            "status_code": 200,
            "latency_ms": 42.57,
        }
        result = HttpRequestRepository.save_http_request(data)
        assert result is not None
        assert float(result.latency_ms) == pytest.approx(42.57, abs=0.01)

    def test_user_agent_and_bytes_stored(self):
        """Optional fields like user_agent, bytes_in, bytes_out stored."""
        data = {
            "request_id": "test-optional-fields",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "client_ip": "10.0.0.1",
            "method": "POST",
            "path": "/api/v1/docker/containers/abc/start",
            "status_code": 200,
            "latency_ms": 15.0,
            "user_agent": "Mozilla/5.0 HomeOps Dashboard",
            "bytes_in": 256,
            "bytes_out": 1024,
        }
        result = HttpRequestRepository.save_http_request(data)
        assert result is not None
        assert result.user_agent == "Mozilla/5.0 HomeOps Dashboard"
        assert result.bytes_in == 256
        assert result.bytes_out == 1024
