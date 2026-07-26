"""
Windows Command Gateway — FastAPI Application.

Proxies container management commands from the React Dashboard (or external clients)
to the Kali Agent's Command Receiver API (http://192.168.2.2:8501).

Runs on port 8500.

Sequence Flow (e.g. Stop container):
1. User clicks "Stop container" in React Dashboard.
2. React sends POST /api/v1/docker/containers/{id}/stop to Windows API Gateway (:8500).
3. Windows Gateway validates request & authentication.
4. Windows Gateway forwards REST command to Kali Agent (:8501) via HTTP client.
5. Kali executes command using Python Docker SDK locally and returns response.
6. Windows Gateway records the action event in StateManager alerts list.
7. Windows Gateway returns result to React Dashboard.
"""

import os
import sys
import time
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import uvicorn

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import WindowsConfig
from windows_listen.listener import global_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("WindowsCommandGateway")

app = FastAPI(
    title="HomeOps Windows Command Gateway API",
    description="Gateway API proxying container management commands to Kali agent.",
    version="1.0.0",
)

# Enable CORS for React dashboard (Vite default: http://localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper function to forward HTTP request to Kali command receiver
async def _forward_to_kali(
    method: str,
    path: str,
    params: Optional[dict] = None,
    payload: Optional[dict] = None,
) -> dict:
    url = f"{WindowsConfig.KALI_COMMAND_URL}{path}"
    headers = {"X-API-Key": WindowsConfig.API_KEY, "Accept": "application/json"}

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


# Get Cached State
@app.get("/api/v1/docker/state")
async def get_docker_state():
    """Returns current telemetry state including container snapshot."""
    snapshot = global_state.get_snapshot()
    return {
        "status": "success",
        "agent_status": snapshot.get("agent_status"),
        "hostname": snapshot.get("hostname"),
        "last_updated": snapshot.get("last_updated"),
        "docker": snapshot.get("docker", {}),
    }


# Forwarded Docker Endpoints
@app.get("/api/v1/docker/containers")
async def list_containers(all: bool = Query(True)):
    return await _forward_to_kali("GET", "/api/v1/docker/containers", params={"all": all})


@app.get("/api/v1/docker/containers/{container_id}")
async def get_container(container_id: str):
    return await _forward_to_kali("GET", f"/api/v1/docker/containers/{container_id}")


@app.post("/api/v1/docker/containers/{container_id}/start")
async def start_container(container_id: str):
    res = await _forward_to_kali("POST", f"/api/v1/docker/containers/{container_id}/start")
    global_state.add_alerts(
        [
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": "CONTAINER_STARTED_BY_USER",
                "alert": f"User started container {res.get('container_name', container_id)}",
                "container_id": container_id,
            }
        ],
        "DOCKER",
    )
    return res


@app.post("/api/v1/docker/containers/{container_id}/stop")
async def stop_container(container_id: str):
    res = await _forward_to_kali("POST", f"/api/v1/docker/containers/{container_id}/stop")
    global_state.add_alerts(
        [
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": "CONTAINER_STOPPED_BY_USER",
                "alert": f"User stopped container {res.get('container_name', container_id)}",
                "container_id": container_id,
            }
        ],
        "DOCKER",
    )
    return res


@app.post("/api/v1/docker/containers/{container_id}/restart")
async def restart_container(container_id: str):
    res = await _forward_to_kali("POST", f"/api/v1/docker/containers/{container_id}/restart")
    global_state.add_alerts(
        [
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": "CONTAINER_RESTARTED_BY_USER",
                "alert": f"User restarted container {res.get('container_name', container_id)}",
                "container_id": container_id,
            }
        ],
        "DOCKER",
    )
    return res


@app.get("/api/v1/docker/containers/{container_id}/logs")
async def get_logs(
    container_id: str,
    tail: int = Query(100, ge=1, le=5000),
    since: Optional[int] = Query(None),
):
    params = {"tail": tail}
    if since is not None:
        params["since"] = since
    return await _forward_to_kali("GET", f"/api/v1/docker/containers/{container_id}/logs", params=params)


@app.get("/api/v1/docker/containers/{container_id}/stats")
async def get_stats(container_id: str):
    return await _forward_to_kali("GET", f"/api/v1/docker/containers/{container_id}/stats")


def start_gateway():
    logger.info(
        f"Starting Windows Command Gateway on "
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
