"""
Windows Command Gateway — FastAPI Application.

Proxies container management commands from the React Dashboard to Kali Agent
and exposes Historical Metrics REST API endpoints for PostgreSQL time-series queries.
"""

from fastapi import Depends
from auth import dependencies
import os
import sys
import time
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Header, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import uvicorn

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import WindowsConfig
from windows_listen.listener import global_state, broadcast_ws_message
from database.repositories import MetricsRepository, HttpRequestRepository, HeartbeatRepository, parse_timestamp
from middleware.http_monitor import HttpMonitorMiddleware
from auth.routes import router as auth_router
from auth.dependencies import get_current_user, require_role

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("WindowsCommandGateway")

app = FastAPI(
    title="HomeOps Windows Command & Historical Metrics Gateway API",
    description="Gateway API proxying container management commands & querying PostgreSQL historical metrics.",
    version="2.0.0",
)

# Enable CORS for React dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP Request Monitoring Middleware — logs every request to PostgreSQL & broadcasts via WebSocket
app.add_middleware(
    HttpMonitorMiddleware,
    save_fn=HttpRequestRepository.save_http_request,
    broadcast_fn=broadcast_ws_message,
)

# Mount Authentication & User Management Router
app.include_router(auth_router)


# Helper function to forward HTTP request to Kali command receiver
async def _forward_to_kali(
    method: str,
    path: str,
    params: Optional[dict] = None,
    payload: Optional[dict] = None,
    auth_token: Optional[str] = None,
) -> dict:
    url = f"{WindowsConfig.KALI_COMMAND_URL}{path}"
    headers = {"Accept": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}" if not auth_token.startswith("Bearer ") else auth_token
    else:
        headers["X-API-Key"] = WindowsConfig.API_KEY

    try:
        async with httpx.AsyncClient(timeout=WindowsConfig.COMMAND_TIMEOUT) as client:
            response = await client.request(
                method=method, url=url, headers=headers, params=params, json=payload
            )

            try:
                data = response.json()
            except Exception:
                data = {"raw_text": response.text}

            if response.status_code >= 400:
                detail = data.get("detail", data)
                raise HTTPException(status_code=response.status_code, detail=detail)

            return data

    except httpx.ConnectError:
        logger.error(f"Failed to connect to Kali command receiver at {url}")
        raise HTTPException(
            status_code=502,
            detail={
                "status": "error",
                "error_code": "KALI_AGENT_UNREACHABLE",
                "message": f"Cannot reach Kali command receiver at {url}. Is Kali agent running?",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        )
    except httpx.TimeoutException:
        logger.error(f"Command timed out when connecting to Kali at {url}")
        raise HTTPException(
            status_code=504,
            detail={
                "status": "error",
                "error_code": "COMMAND_TIMEOUT",
                "message": f"Command timed out after {WindowsConfig.COMMAND_TIMEOUT}s.",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error forwarding command to Kali: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error_code": "GATEWAY_ERROR",
                "message": str(e),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        )


# Health Check
@app.get("/health")
async def health():
    return {
        "service": "windows-command-gateway",
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


# ==========================================
# HISTORICAL METRICS REST API ENDPOINTS
# ==========================================

@app.get("/api/v1/history/hardware")
async def get_hardware_history(
    host: Optional[str] = Query(None, description="Filter by hostname"),
    start: Optional[str] = Query(None, description="ISO-8601 start timestamp"),
    end: Optional[str] = Query(None, description="ISO-8601 end timestamp"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Returns historical hardware telemetry records from PostgreSQL."""
    start_dt = parse_timestamp(start) if start else None
    end_dt = parse_timestamp(end) if end else None

    metrics = MetricsRepository.query_hardware_history(
        hostname=host, start_time=start_dt, end_time=end_dt, limit=limit
    )
    return {
        "status": "success",
        "count": len(metrics),
        "host_filter": host,
        "data": metrics,
    }


@app.get("/api/v1/history/docker")
async def get_docker_history(
    host: Optional[str] = Query(None, description="Filter by hostname"),
    container: Optional[str] = Query(None, description="Filter by container name or ID"),
    start: Optional[str] = Query(None, description="ISO-8601 start timestamp"),
    end: Optional[str] = Query(None, description="ISO-8601 end timestamp"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Returns historical docker container telemetry records from PostgreSQL."""
    start_dt = parse_timestamp(start) if start else None
    end_dt = parse_timestamp(end) if end else None

    metrics = MetricsRepository.query_docker_history(
        hostname=host, container=container, start_time=start_dt, end_time=end_dt, limit=limit
    )
    return {
        "status": "success",
        "count": len(metrics),
        "host_filter": host,
        "container_filter": container,
        "data": metrics,
    }


@app.get("/api/v1/history/summary")
async def get_historical_summary(
    host: Optional[str] = Query(None, description="Filter by hostname"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Returns historical summary stats (averages, latest timestamp, docker sample count)."""
    summary = MetricsRepository.query_summary_metrics(hostname=host)
    return {
        "status": "success",
        "host_filter": host,
        "summary": summary,
    }


# ==========================================
# HTTP REQUEST MONITORING API ENDPOINTS
# ==========================================

@app.get("/api/v1/http/recent")
async def get_recent_http_requests(
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Returns the most recent HTTP request logs, ordered newest-first."""
    requests = HttpRequestRepository.get_recent_requests(limit=limit)
    return {
        "status": "success",
        "count": len(requests),
        "data": requests,
    }


@app.get("/api/v1/http/history")
async def get_http_request_history(
    start: Optional[str] = Query(None, description="ISO-8601 start timestamp"),
    end: Optional[str] = Query(None, description="ISO-8601 end timestamp"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Returns HTTP request logs within a time range, ordered chronologically."""
    requests = HttpRequestRepository.get_http_history(start=start, end=end, limit=limit)
    return {
        "status": "success",
        "count": len(requests),
        "data": requests,
    }


# ==========================================
# HEARTBEAT & HOST STATUS API ENDPOINTS
# ==========================================

@app.get("/api/v1/hosts/status")
async def get_host_statuses(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns the current status (ONLINE/OFFLINE) and last heartbeat timestamp for all hosts."""
    state_hosts = global_state.get_host_statuses()
    if state_hosts:
        return state_hosts

    db_hosts = HeartbeatRepository.get_host_statuses()
    if db_hosts:
        return db_hosts

    snapshot = global_state.get_snapshot()
    return [
        {
            "hostname": snapshot.get("hostname", "kali-vm"),
            "status": snapshot.get("agent_status", "OFFLINE"),
            "last_heartbeat": snapshot.get("last_updated")
        }
    ]


# Get Cached Docker State
@app.get("/api/v1/docker/state")
async def get_docker_state(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns current telemetry state including container snapshot."""
    snapshot = global_state.get_snapshot()
    return {
        "status": "success",
        "agent_status": snapshot.get("agent_status"),
        "hostname": snapshot.get("hostname"),
        "last_updated": snapshot.get("last_updated"),
        "docker": snapshot.get("docker", {}),
    }


# Forwarded Docker Control Endpoints
@app.get("/api/v1/docker/containers")
async def list_containers(
    all: bool = Query(True),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    return await _forward_to_kali(
        "GET", "/api/v1/docker/containers",
        params={"all": all},
        auth_token=current_user.get("raw_token")
    )


@app.get("/api/v1/docker/containers/{container_id}")
async def get_container(
    container_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    return await _forward_to_kali(
        "GET", f"/api/v1/docker/containers/{container_id}",
        auth_token=current_user.get("raw_token")
    )


@app.post("/api/v1/docker/containers/{container_id}/start")
async def start_container(
    container_id: str,
    current_user: Dict[str, Any] = Depends(require_role(["admin", "operator"])),
):
    res = await _forward_to_kali(
        "POST", f"/api/v1/docker/containers/{container_id}/start",
        auth_token=current_user.get("raw_token")
    )
    global_state.add_alerts(
        [
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": "CONTAINER_STARTED_BY_USER",
                "alert": f"User '{current_user.get('username')}' started container {res.get('container_name', container_id)}",
                "container_id": container_id,
            }
        ],
        "DOCKER",
    )
    MetricsRepository.save_connection_event(
        global_state.state.get("hostname", "Unknown"),
        "CONTAINER_START",
        f"Container {container_id} started by user '{current_user.get('username')}'",
    )
    return res


@app.post("/api/v1/docker/containers/{container_id}/stop")
async def stop_container(
    container_id: str,
    current_user: Dict[str, Any] = Depends(require_role(["admin", "operator"])),
):
    res = await _forward_to_kali(
        "POST", f"/api/v1/docker/containers/{container_id}/stop",
        auth_token=current_user.get("raw_token")
    )
    global_state.add_alerts(
        [
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": "CONTAINER_STOPPED_BY_USER",
                "alert": f"User '{current_user.get('username')}' stopped container {res.get('container_name', container_id)}",
                "container_id": container_id,
            }
        ],
        "DOCKER",
    )
    MetricsRepository.save_connection_event(
        global_state.state.get("hostname", "Unknown"),
        "CONTAINER_STOP",
        f"Container {container_id} stopped by user '{current_user.get('username')}'",
    )
    return res


@app.post("/api/v1/docker/containers/{container_id}/restart")
async def restart_container(
    container_id: str,
    current_user: Dict[str, Any] = Depends(require_role(["admin", "operator"])),
):
    res = await _forward_to_kali(
        "POST", f"/api/v1/docker/containers/{container_id}/restart",
        auth_token=current_user.get("raw_token")
    )
    global_state.add_alerts(
        [
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": "CONTAINER_RESTARTED_BY_USER",
                "alert": f"User '{current_user.get('username')}' restarted container {res.get('container_name', container_id)}",
                "container_id": container_id,
            }
        ],
        "DOCKER",
    )
    MetricsRepository.save_connection_event(
        global_state.state.get("hostname", "Unknown"),
        "CONTAINER_RESTART",
        f"Container {container_id} restarted by user '{current_user.get('username')}'",
    )
    return res


@app.get("/api/v1/docker/containers/{container_id}/logs")
async def get_logs(
    container_id: str,
    tail: int = Query(100, ge=1, le=5000),
    since: Optional[int] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    params = {"tail": tail}
    if since is not None:
        params["since"] = since
    return await _forward_to_kali(
        "GET", f"/api/v1/docker/containers/{container_id}/logs",
        params=params,
        auth_token=current_user.get("raw_token")
    )


@app.get("/api/v1/docker/containers/{container_id}/stats")
async def get_stats(
    container_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    return await _forward_to_kali(
        "GET", f"/api/v1/docker/containers/{container_id}/stats",
        auth_token=current_user.get("raw_token")
    )


def start_gateway():
    logger.info(
        f"Starting Windows Command Gateway & Historical API on "
        f"{WindowsConfig.COMMAND_API_HOST}:{WindowsConfig.COMMAND_API_PORT}"
    )
    uvicorn.run(
        app,
        host=WindowsConfig.COMMAND_API_HOST,
        port=WindowsConfig.COMMAND_API_PORT,
        log_level="info",
        access_log=False,
    )


if __name__ == "__main__":
    start_gateway()
