"""
Docker container data collector using Docker SDK for Python.
Runs locally on Kali Linux — communicates with the Docker daemon via unix socket.
Never exposes the Docker socket to the network.
"""

import time
import logging
import docker
from docker.errors import DockerException, NotFound, APIError
from typing import Dict, Any, List, Optional

logger = logging.getLogger("DockerCollector")

# Module-level client (lazy-initialized)
_client: Optional[docker.DockerClient] = None

def _get_client() -> docker.DockerClient:
    """
    Returns a cached Docker client instance.
    Raises DockerException if the daemon is unavailable.
    """
    global _client
    if _client is None:
        _client = docker.from_env(timeout=10)
    # Verify connectivity with a lightweight ping
    _client.ping()
    return _client


def reset_client() -> None:
    """Resets the cached Docker client (used after daemon reconnection)."""
    global _client
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
    _client = None


def _parse_port_bindings(ports: dict) -> List[Dict[str, Any]]:
    """
    Parses Docker container port bindings into a clean list.
    Input format: {'80/tcp': [{'HostIp': '0.0.0.0', 'HostPort': '8080'}]}
    """
    parsed = []
    if not ports:
        return parsed

    for container_port_proto, host_bindings in ports.items():
        parts = container_port_proto.split("/")
        container_port = int(parts[0])
        protocol = parts[1] if len(parts) > 1 else "tcp"

        if host_bindings:
            for binding in host_bindings:
                parsed.append({
                    "host_ip": binding.get("HostIp", "0.0.0.0"),
                    "host_port": int(binding.get("HostPort", 0)),
                    "container_port": container_port,
                    "protocol": protocol,
                })
        else:
            # Exposed but not published
            parsed.append({
                "host_ip": None,
                "host_port": None,
                "container_port": container_port,
                "protocol": protocol,
            })

    return parsed


def _parse_mounts(mounts: list) -> List[Dict[str, str]]:
    """Parses container mount information into clean dicts."""
    parsed = []
    if not mounts:
        return parsed

    for mount in mounts:
        parsed.append({
            "type": mount.get("Type", "unknown"),
            "source": mount.get("Source", ""),
            "destination": mount.get("Destination", ""),
            "mode": mount.get("Mode", "rw"),
            "read_only": mount.get("RW", True) is False,
        })

    return parsed


def _parse_networks(network_settings: dict) -> List[str]:
    """Extracts network names from container network settings."""
    if not network_settings or "Networks" not in network_settings:
        return []
    return list(network_settings["Networks"].keys())


def _calculate_cpu_percent(stats: dict) -> float:
    """
    Calculates CPU usage percentage from Docker stats snapshot.
    Uses the delta method: (container_delta / system_delta) * num_cpus * 100
    """
    try:
        cpu_stats = stats.get("cpu_stats", {})
        precpu_stats = stats.get("precpu_stats", {})

        cpu_delta = (
            cpu_stats.get("cpu_usage", {}).get("total_usage", 0)
            - precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
        )
        system_delta = (
            cpu_stats.get("system_cpu_usage", 0)
            - precpu_stats.get("system_cpu_usage", 0)
        )

        if system_delta > 0 and cpu_delta >= 0:
            num_cpus = cpu_stats.get("online_cpus") or len(
                cpu_stats.get("cpu_usage", {}).get("percpu_usage", [1])
            )
            return round((cpu_delta / system_delta) * num_cpus * 100.0, 2)
    except (KeyError, TypeError, ZeroDivisionError):
        pass

    return 0.0


def _parse_stats(stats: dict) -> Dict[str, Any]:
    """Parses a Docker stats snapshot into a clean metrics dict."""
    # Memory
    memory_stats = stats.get("memory_stats", {})
    memory_usage = memory_stats.get("usage", 0)
    memory_limit = memory_stats.get("limit", 1)
    # Subtract cache from usage for accurate reporting
    cache = memory_stats.get("stats", {}).get("cache", 0)
    actual_memory = memory_usage - cache if memory_usage > cache else memory_usage

    memory_usage_mb = round(actual_memory / (1024 * 1024), 2)
    memory_limit_mb = round(memory_limit / (1024 * 1024), 2)
    memory_percent = round((actual_memory / memory_limit) * 100.0, 2) if memory_limit > 0 else 0.0

    # Network I/O
    network_rx = 0
    network_tx = 0
    networks = stats.get("networks", {})
    for iface_stats in networks.values():
        network_rx += iface_stats.get("rx_bytes", 0)
        network_tx += iface_stats.get("tx_bytes", 0)

    # Block I/O
    block_read = 0
    block_write = 0
    blkio_stats = stats.get("blkio_stats", {})
    for entry in blkio_stats.get("io_service_bytes_recursive", []) or []:
        op = entry.get("op", "").lower()
        if op == "read":
            block_read += entry.get("value", 0)
        elif op == "write":
            block_write += entry.get("value", 0)

    return {
        "cpu_percent": _calculate_cpu_percent(stats),
        "memory_usage_mb": memory_usage_mb,
        "memory_limit_mb": memory_limit_mb,
        "memory_percent": memory_percent,
        "network_rx_bytes": network_rx,
        "network_tx_bytes": network_tx,
        "block_read_bytes": block_read,
        "block_write_bytes": block_write,
    }


def _container_to_dict(container) -> Dict[str, Any]:
    """Converts a Docker container object to a serializable dict."""
    attrs = container.attrs or {}
    config = attrs.get("Config", {})
    state = attrs.get("State", {})
    host_config = attrs.get("HostConfig", {})
    network_settings = attrs.get("NetworkSettings", {})

    return {
        "container_id": container.short_id,
        "container_id_full": container.id,
        "name": container.name,
        "image": config.get("Image", str(container.image.tags[0] if container.image.tags else container.image.short_id)),
        "status": container.status,
        "state": state.get("Status", container.status),
        "restart_count": state.get("RestartCount", 0),
        "created": attrs.get("Created", ""),
        "started_at": state.get("StartedAt", ""),
        "finished_at": state.get("FinishedAt", ""),
        "ports": _parse_port_bindings(network_settings.get("Ports", {})),
        "mounts": _parse_mounts(attrs.get("Mounts", [])),
        "networks": _parse_networks(network_settings),
        "restart_policy": host_config.get("RestartPolicy", {}).get("Name", "no"),
    }


# ---------------------------------------------------------------------------
# Public API — Data Collection
# ---------------------------------------------------------------------------

def list_containers(include_stopped: bool = True) -> List[Dict[str, Any]]:
    """
    Returns a list of all Docker containers with metadata.
    Set include_stopped=False to list only running containers.
    """
    client = _get_client()
    containers = client.containers.list(all=include_stopped)
    return [_container_to_dict(c) for c in containers]


def get_container_detail(container_id: str) -> Dict[str, Any]:
    """Returns full detail for a single container by ID or name."""
    client = _get_client()
    container = client.containers.get(container_id)
    container.reload()  # Ensure fresh attributes
    return _container_to_dict(container)


def get_container_stats(container_id: str) -> Dict[str, Any]:
    """
    Returns a single stats snapshot for a container.
    Uses stream=False for a one-shot measurement.
    """
    client = _get_client()
    container = client.containers.get(container_id)
    stats = container.stats(stream=False)
    return _parse_stats(stats)


def get_container_logs(
    container_id: str, tail: int = 100, since: Optional[int] = None
) -> str:
    """
    Returns the last N lines of container logs as a string.
    `since` is a Unix timestamp (seconds) to filter logs from that time.
    """
    client = _get_client()
    container = client.containers.get(container_id)

    kwargs = {"tail": tail, "timestamps": True, "stdout": True, "stderr": True}
    if since is not None:
        kwargs["since"] = since

    logs = container.logs(**kwargs)

    if isinstance(logs, bytes):
        return logs.decode("utf-8", errors="replace")
    return str(logs)


def collect_all_container_telemetry() -> Dict[str, Any]:
    """
    Collects container list + per-container stats for telemetry transmission.
    Returns a complete Docker telemetry payload body.
    """
    try:
        client = _get_client()
        raw_containers = client.containers.list(all=True)
    except DockerException as e:
        logger.error(f"Docker daemon unavailable during telemetry collection: {e}")
        return {
            "containers": [],
            "docker_info": {"total_containers": 0, "running": 0, "paused": 0, "stopped": 0},
        }

    containers = []
    running_count = 0
    paused_count = 0
    stopped_count = 0

    for c in raw_containers:
        container_data = _container_to_dict(c)

        # Count by status
        status = c.status
        if status == "running":
            running_count += 1
            # Only collect stats for running containers (stopped containers have no stats)
            try:
                container_data["stats"] = _parse_stats(c.stats(stream=False))
            except Exception as e:
                logger.warning(f"Failed to collect stats for {c.name}: {e}")
                container_data["stats"] = {}
        elif status == "paused":
            paused_count += 1
            container_data["stats"] = {}
        else:
            stopped_count += 1
            container_data["stats"] = {}

        containers.append(container_data)

    return {
        "containers": containers,
        "docker_info": {
            "total_containers": len(containers),
            "running": running_count,
            "paused": paused_count,
            "stopped": stopped_count,
        },
    }


# ---------------------------------------------------------------------------
# Public API — Container Commands
# ---------------------------------------------------------------------------

def start_container(container_id: str) -> Dict[str, Any]:
    """Starts a stopped container. Returns result dict."""
    client = _get_client()
    container = client.containers.get(container_id)
    container.reload()

    if container.status == "running":
        return {
            "status": "error",
            "action": "start",
            "container_id": container.short_id,
            "container_name": container.name,
            "error_code": "ALREADY_RUNNING",
            "message": f"Container '{container.name}' is already running.",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    container.start()
    container.reload()

    return {
        "status": "success",
        "action": "start",
        "container_id": container.short_id,
        "container_name": container.name,
        "message": f"Container '{container.name}' started successfully.",
        "new_state": container.status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def stop_container(container_id: str, timeout: int = 10) -> Dict[str, Any]:
    """Stops a running container. Returns result dict."""
    client = _get_client()
    container = client.containers.get(container_id)
    container.reload()

    if container.status in ("exited", "created", "dead"):
        return {
            "status": "error",
            "action": "stop",
            "container_id": container.short_id,
            "container_name": container.name,
            "error_code": "ALREADY_STOPPED",
            "message": f"Container '{container.name}' is already stopped (status: {container.status}).",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    container.stop(timeout=timeout)
    container.reload()

    return {
        "status": "success",
        "action": "stop",
        "container_id": container.short_id,
        "container_name": container.name,
        "message": f"Container '{container.name}' stopped successfully.",
        "new_state": container.status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def restart_container(container_id: str, timeout: int = 10) -> Dict[str, Any]:
    """Restarts a container. Returns result dict."""
    client = _get_client()
    container = client.containers.get(container_id)

    container.restart(timeout=timeout)
    container.reload()

    return {
        "status": "success",
        "action": "restart",
        "container_id": container.short_id,
        "container_name": container.name,
        "message": f"Container '{container.name}' restarted successfully.",
        "new_state": container.status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }