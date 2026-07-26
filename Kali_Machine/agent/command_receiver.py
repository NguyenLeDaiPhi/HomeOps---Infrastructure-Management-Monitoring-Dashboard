"""
Kali Linux Docker Command Receiver — FastAPI Application.

Accepts management commands from the Windows gateway and executes them
against the local Docker daemon via Docker SDK. Runs on port 8501.

Flow: React Dashboard → Windows Gateway :8500 → This Server :8501 → Docker SDK → Docker Daemon

Security:
  - X-API-Key header validation
  - Optional IP allowlist
"""

import os
import sys
import time
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Request, Query
from fastapi.responses import JSONResponse
import uvicorn

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import KaliConfig
from collector.docker import (
    list_containers,
    get_container_detail,
    get_container_stats,
    get_container_logs,
    start_container,
    stop_container,
    restart_container,
    reset_client,
)
from docker.errors import DockerException, NotFound, APIError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("KaliCommandReceiver")

# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="HomeOps Kali Docker Command API",
    description="Receives container management commands from Windows gateway.",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Middleware — API Key Validation
# ---------------------------------------------------------------------------

@app.middleware("http")
async def validate_api_key(request: Request, call_next):
    """Validates X-API-Key header on all /api/ routes."""
    # Skip auth for health check
    if request.url.path == "/health":
        return await call_next(request)

    api_key = request.headers.get("X-API-Key")
    if api_key != KaliConfig.API_KEY:
        logger.warning(f"Unauthorized request from {request.client.host}: invalid API key")
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "error_code": "UNAUTHORIZED",
                "message": "Invalid or missing API key.",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        )

    return await call_next(request)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    """Returns service health and Docker daemon connectivity status."""
    docker_ok = False
    try:
        from collector.docker import _get_client
        _get_client()
        docker_ok = True
    except Exception:
        pass

    return {
        "service": "kali-command-receiver",
        "status": "healthy",
        "docker_daemon": "connected" if docker_ok else "unavailable",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


# ---------------------------------------------------------------------------
# Container List & Detail
# ---------------------------------------------------------------------------

@app.get("/api/v1/docker/containers")
async def api_list_containers(all: bool = Query(True, description="Include stopped containers")):
    """Lists all Docker containers with metadata."""
    try:
        containers = list_containers(include_stopped=all)
        return {
            "status": "success",
            "containers": containers,
            "count": len(containers),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    except DockerException as e:
        logger.error(f"Docker daemon unavailable: {e}")
        reset_client()
        raise HTTPException(status_code=503, detail={
            "status": "error",
            "error_code": "DOCKER_DAEMON_UNAVAILABLE",
            "message": "Cannot connect to Docker daemon. Is Docker running?",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })


@app.get("/api/v1/docker/containers/{container_id}")
async def api_get_container(container_id: str):
    """Returns detailed information for a single container."""
    try:
        detail = get_container_detail(container_id)
        return {"status": "success", "container": detail}
    except NotFound:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "error_code": "CONTAINER_NOT_FOUND",
            "message": f"Container '{container_id}' not found.",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
    except DockerException as e:
        logger.error(f"Docker daemon unavailable: {e}")
        reset_client()
        raise HTTPException(status_code=503, detail={
            "status": "error",
            "error_code": "DOCKER_DAEMON_UNAVAILABLE",
            "message": "Cannot connect to Docker daemon.",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })


# ---------------------------------------------------------------------------
# Container Commands: Start / Stop / Restart
# ---------------------------------------------------------------------------

@app.post("/api/v1/docker/containers/{container_id}/start")
async def api_start_container(container_id: str):
    """Starts a stopped container."""
    try:
        result = start_container(container_id)
        if result["status"] == "error":
            raise HTTPException(status_code=409, detail=result)
        return result
    except NotFound:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "action": "start",
            "container_id": container_id,
            "error_code": "CONTAINER_NOT_FOUND",
            "message": f"Container '{container_id}' not found.",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
    except APIError as e:
        logger.error(f"Docker API error starting container {container_id}: {e}")
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "action": "start",
            "container_id": container_id,
            "error_code": "DOCKER_API_ERROR",
            "message": str(e),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
    except DockerException as e:
        reset_client()
        raise HTTPException(status_code=503, detail={
            "status": "error",
            "error_code": "DOCKER_DAEMON_UNAVAILABLE",
            "message": "Cannot connect to Docker daemon.",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })


@app.post("/api/v1/docker/containers/{container_id}/stop")
async def api_stop_container(container_id: str):
    """Stops a running container."""
    try:
        result = stop_container(container_id)
        if result["status"] == "error":
            raise HTTPException(status_code=409, detail=result)
        return result
    except NotFound:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "action": "stop",
            "container_id": container_id,
            "error_code": "CONTAINER_NOT_FOUND",
            "message": f"Container '{container_id}' not found.",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
    except APIError as e:
        logger.error(f"Docker API error stopping container {container_id}: {e}")
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "action": "stop",
            "container_id": container_id,
            "error_code": "DOCKER_API_ERROR",
            "message": str(e),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
    except DockerException as e:
        reset_client()
        raise HTTPException(status_code=503, detail={
            "status": "error",
            "error_code": "DOCKER_DAEMON_UNAVAILABLE",
            "message": "Cannot connect to Docker daemon.",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })


@app.post("/api/v1/docker/containers/{container_id}/restart")
async def api_restart_container(container_id: str):
    """Restarts a container."""
    try:
        result = restart_container(container_id)
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result)
        return result
    except NotFound:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "action": "restart",
            "container_id": container_id,
            "error_code": "CONTAINER_NOT_FOUND",
            "message": f"Container '{container_id}' not found.",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
    except APIError as e:
        logger.error(f"Docker API error restarting container {container_id}: {e}")
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "action": "restart",
            "container_id": container_id,
            "error_code": "DOCKER_API_ERROR",
            "message": str(e),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
    except DockerException as e:
        reset_client()
        raise HTTPException(status_code=503, detail={
            "status": "error",
            "error_code": "DOCKER_DAEMON_UNAVAILABLE",
            "message": "Cannot connect to Docker daemon.",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })


# ---------------------------------------------------------------------------
# Container Logs & Stats
# ---------------------------------------------------------------------------

@app.get("/api/v1/docker/containers/{container_id}/logs")
async def api_get_logs(
    container_id: str,
    tail: int = Query(100, ge=1, le=5000, description="Number of log lines to return"),
    since: Optional[int] = Query(None, description="Unix timestamp to fetch logs from"),
):
    """Returns container log output."""
    try:
        logs = get_container_logs(container_id, tail=tail, since=since)
        return {
            "status": "success",
            "container_id": container_id,
            "logs": logs,
            "tail": tail,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    except NotFound:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "error_code": "CONTAINER_NOT_FOUND",
            "message": f"Container '{container_id}' not found.",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
    except DockerException as e:
        reset_client()
        raise HTTPException(status_code=503, detail={
            "status": "error",
            "error_code": "DOCKER_DAEMON_UNAVAILABLE",
            "message": "Cannot connect to Docker daemon.",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })


@app.get("/api/v1/docker/containers/{container_id}/stats")
async def api_get_stats(container_id: str):
    """Returns a single-shot stats snapshot for a container."""
    try:
        stats = get_container_stats(container_id)
        return {
            "status": "success",
            "container_id": container_id,
            "stats": stats,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    except NotFound:
        raise HTTPException(status_code=404, detail={
            "status": "error",
            "error_code": "CONTAINER_NOT_FOUND",
            "message": f"Container '{container_id}' not found.",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
    except DockerException as e:
        reset_client()
        raise HTTPException(status_code=503, detail={
            "status": "error",
            "error_code": "DOCKER_DAEMON_UNAVAILABLE",
            "message": "Cannot connect to Docker daemon.",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })


# ---------------------------------------------------------------------------
# Standalone Entrypoint
# ---------------------------------------------------------------------------

def start_command_receiver():
    """Starts the FastAPI command receiver server."""
    logger.info(
        f"Starting Kali Command Receiver on "
        f"{KaliConfig.COMMAND_API_HOST}:{KaliConfig.COMMAND_API_PORT}"
    )
    uvicorn.run(
        app,
        host=KaliConfig.COMMAND_API_HOST,
        port=KaliConfig.COMMAND_API_PORT,
        log_level="info",
        access_log=False,
    )


if __name__ == "__main__":
    start_command_receiver()
