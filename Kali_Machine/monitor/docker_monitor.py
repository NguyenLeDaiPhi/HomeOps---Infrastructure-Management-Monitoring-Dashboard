"""
Docker container state change monitor.
Follows the same delta-detection pattern as NetworkMonitor and ProcessMonitor.
Compares previous container snapshot to current, emitting lifecycle events.
"""

import logging
from typing import List, Dict, Any
from collector.docker_collector import list_containers, DockerException

logger = logging.getLogger("DockerMonitor")


class DockerMonitor:
    """
    Monitors Docker container lifecycle events:
    - CONTAINER_CREATED: New container appeared
    - CONTAINER_REMOVED: Container disappeared
    - CONTAINER_STARTED: Container transitioned to 'running'
    - CONTAINER_STOPPED: Container transitioned from 'running' to stopped state
    - CONTAINER_STATUS_CHANGED: Any other status transition
    """

    def __init__(self):
        self.previous_snapshot: Dict[str, Dict[str, Any]] = {}
        try:
            containers = list_containers(include_stopped=True)
            self.previous_snapshot = {c["container_id"]: c for c in containers}
        except DockerException:
            logger.warning("Docker daemon unavailable at monitor init — starting with empty snapshot.")
        except Exception as e:
            logger.error(f"Unexpected error during DockerMonitor init: {e}")

    def check_changes(self) -> List[Dict[str, Any]]:
        """
        Compares current container state to previous snapshot.
        Returns a list of change events. Updates internal snapshot.
        """
        events: List[Dict[str, Any]] = []

        try:
            current_containers = list_containers(include_stopped=True)
        except DockerException:
            logger.warning("Docker daemon unavailable during change check — skipping cycle.")
            return events
        except Exception as e:
            logger.error(f"Unexpected error collecting containers: {e}")
            return events

        current_snapshot = {c["container_id"]: c for c in current_containers}

        previous_ids = set(self.previous_snapshot.keys())
        current_ids = set(current_snapshot.keys())

        # Detect newly created containers
        for cid in current_ids - previous_ids:
            container = current_snapshot[cid]
            events.append({
                "event": "CONTAINER_CREATED",
                "container_id": cid,
                "name": container["name"],
                "image": container["image"],
                "status": container["status"],
            })

        # Detect removed containers
        for cid in previous_ids - current_ids:
            container = self.previous_snapshot[cid]
            events.append({
                "event": "CONTAINER_REMOVED",
                "container_id": cid,
                "name": container["name"],
                "image": container["image"],
                "previous_status": container["status"],
            })

        # Detect status changes in existing containers
        for cid in current_ids & previous_ids:
            prev = self.previous_snapshot[cid]
            curr = current_snapshot[cid]

            if prev["status"] != curr["status"]:
                # Determine specific event type
                if curr["status"] == "running" and prev["status"] != "running":
                    event_type = "CONTAINER_STARTED"
                elif prev["status"] == "running" and curr["status"] != "running":
                    event_type = "CONTAINER_STOPPED"
                else:
                    event_type = "CONTAINER_STATUS_CHANGED"

                events.append({
                    "event": event_type,
                    "container_id": cid,
                    "name": curr["name"],
                    "image": curr["image"],
                    "old_status": prev["status"],
                    "new_status": curr["status"],
                })

        self.previous_snapshot = current_snapshot
        return events
