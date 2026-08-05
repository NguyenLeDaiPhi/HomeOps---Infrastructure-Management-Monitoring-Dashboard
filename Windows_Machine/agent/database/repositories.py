import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, delete, func
from database.connection import get_db_session
from database.models import Host, HardwareMetric, DockerMetric, ConnectionEvent, HttpRequestLog, HostHeartbeat

logger = logging.getLogger("MetricsRepository")

def parse_timestamp(ts_val: Any) -> datetime:
    """Parses timestamp into UTC datetime. Defaults to current UTC time if missing/invalid."""
    if not ts_val:
        return datetime.now(timezone.utc)
    if isinstance(ts_val, datetime):
        if ts_val.tzinfo is None:
            return ts_val.replace(tzinfo=timezone.utc)
        return ts_val.astimezone(timezone.utc)
    if isinstance(ts_val, (int, float)):
        return datetime.fromtimestamp(ts_val, tz=timezone.utc)
    if isinstance(ts_val, str):
        try:
            clean_ts = ts_val.strip()
            if clean_ts.endswith('Z'):
                clean_ts = clean_ts[:-1] + '+00:00'
            dt = datetime.fromisoformat(clean_ts)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


class MetricsRepository:
    @staticmethod
    def get_or_create_host(session, hostname: str, ip_address: Optional[str] = None, operating_system: Optional[str] = "Linux") -> Host:
        stmt = select(Host).where(Host.hostname == hostname)
        host = session.scalar(stmt)
        if not host:
            host = Host(hostname=hostname, ip_address=ip_address, operating_system=operating_system)
            session.add(host)
            session.flush()
        return host

    @classmethod
    def save_hardware_metrics(cls, payload: Dict[str, Any]) -> Optional[HardwareMetric]:
        """Saves hardware telemetry metrics safely. Accepts partial payloads (missing fields -> NULL)."""
        if not isinstance(payload, dict):
            logger.warning("Skipping invalid hardware payload: not a dict")
            return None

        try:
            hostname = payload.get("hostname", "Unknown")
            ts = parse_timestamp(payload.get("timestamp"))

            cpu_data = payload.get("cpu") if isinstance(payload.get("cpu"), dict) else {}
            ram_data = payload.get("ram") if isinstance(payload.get("ram"), dict) else {}
            disk_data = payload.get("disk")

            # Extract CPU percent
            cpu_percent = cpu_data.get("total_cpu")
            if cpu_percent is None:
                cpu_percent = cpu_data.get("usage")

            # Extract RAM
            ram_percent = ram_data.get("percent")
            ram_used_mb = None
            if "used_gb" in ram_data and ram_data["used_gb"] is not None:
                ram_used_mb = int(ram_data["used_gb"] * 1024)
            elif "used_mb" in ram_data:
                ram_used_mb = int(ram_data["used_mb"])

            ram_total_mb = None
            if "total_gb" in ram_data and ram_data["total_gb"] is not None:
                ram_total_mb = int(ram_data["total_gb"] * 1024)
            elif "total_mb" in ram_data:
                ram_total_mb = int(ram_data["total_mb"])

            # Extract Disk (may be list of disks or dict)
            main_disk = {}
            if isinstance(disk_data, list) and len(disk_data) > 0:
                main_disk = disk_data[0] if isinstance(disk_data[0], dict) else {}
            elif isinstance(disk_data, dict):
                main_disk = disk_data

            disk_percent = main_disk.get("usage_percent")
            if disk_percent is None:
                disk_percent = main_disk.get("percent")
            disk_used_gb = main_disk.get("used_gb")
            disk_free_gb = main_disk.get("free_gb")

            with get_db_session() as session:
                host = cls.get_or_create_host(session, hostname)
                metric = HardwareMetric(
                    host_id=host.id,
                    timestamp=ts,
                    cpu_percent=cpu_percent,
                    ram_percent=ram_percent,
                    ram_used_mb=ram_used_mb,
                    ram_total_mb=ram_total_mb,
                    disk_percent=disk_percent,
                    disk_used_gb=disk_used_gb,
                    disk_free_gb=disk_free_gb,
                )
                session.add(metric)
                session.flush()
                session.refresh(metric)
                return metric
        except Exception as e:
            logger.error(f"Error persisting hardware metrics: {e}")
            return None

    @classmethod
    def save_docker_metrics(cls, payload: Dict[str, Any]) -> List[DockerMetric]:
        """Saves docker container telemetry records."""
        if not isinstance(payload, dict):
            logger.warning("Skipping invalid docker payload: not a dict")
            return []

        saved_metrics = []
        try:
            hostname = payload.get("hostname", "Unknown")
            ts = parse_timestamp(payload.get("timestamp"))
            containers = payload.get("containers", [])
            if not isinstance(containers, list):
                return []

            with get_db_session() as session:
                host = cls.get_or_create_host(session, hostname)
                for c in containers:
                    if not isinstance(c, dict):
                        continue
                    stats = c.get("stats") if isinstance(c.get("stats"), dict) else {}
                    net_rx = stats.get("network_rx_bytes") or stats.get("network_rx")
                    net_tx = stats.get("network_tx_bytes") or stats.get("network_tx")

                    metric = DockerMetric(
                        host_id=host.id,
                        timestamp=ts,
                        container_id=c.get("container_id") or c.get("id"),
                        container_name=c.get("name") or c.get("container_name"),
                        image=c.get("image"),
                        status=c.get("status"),
                        cpu_percent=stats.get("cpu_percent") or c.get("cpu_percent"),
                        memory_mb=stats.get("memory_usage_mb") or c.get("memory_mb"),
                        network_rx=net_rx,
                        network_tx=net_tx,
                    )
                    session.add(metric)
                    saved_metrics.append(metric)
                session.flush()
                return saved_metrics
        except Exception as e:
            logger.error(f"Error persisting docker metrics: {e}")
            return []

    @classmethod
    def save_connection_event(cls, hostname: str, event_type: str, message: str, timestamp_val: Any = None) -> Optional[ConnectionEvent]:
        try:
            ts = parse_timestamp(timestamp_val)
            with get_db_session() as session:
                host = cls.get_or_create_host(session, hostname)
                event = ConnectionEvent(
                    host_id=host.id,
                    event_type=event_type,
                    timestamp=ts,
                    message=message
                )
                session.add(event)
                session.flush()
                session.refresh(event)
                return event
        except Exception as e:
            logger.error(f"Error persisting connection event: {e}")
            return None

    @staticmethod
    def query_hardware_history(
        hostname: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        with get_db_session() as session:
            stmt = select(HardwareMetric, Host.hostname).join(Host, HardwareMetric.host_id == Host.id)
            if hostname:
                stmt = stmt.where(Host.hostname == hostname)
            if start_time:
                stmt = stmt.where(HardwareMetric.timestamp >= start_time)
            if end_time:
                stmt = stmt.where(HardwareMetric.timestamp <= end_time)

            stmt = stmt.order_by(HardwareMetric.timestamp.asc()).limit(limit)
            results = session.execute(stmt).all()

            output = []
            for row, host_name in results:
                output.append({
                    "id": row.id,
                    "hostname": host_name,
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                    "cpu_percent": float(row.cpu_percent) if row.cpu_percent is not None else None,
                    "ram_percent": float(row.ram_percent) if row.ram_percent is not None else None,
                    "ram_used_mb": row.ram_used_mb,
                    "ram_total_mb": row.ram_total_mb,
                    "disk_percent": float(row.disk_percent) if row.disk_percent is not None else None,
                    "disk_used_gb": float(row.disk_used_gb) if row.disk_used_gb is not None else None,
                    "disk_free_gb": float(row.disk_free_gb) if row.disk_free_gb is not None else None,
                })
            return output

    @staticmethod
    def query_docker_history(
        hostname: Optional[str] = None,
        container: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        with get_db_session() as session:
            stmt = select(DockerMetric, Host.hostname).join(Host, DockerMetric.host_id == Host.id)
            if hostname:
                stmt = stmt.where(Host.hostname == hostname)
            if container:
                stmt = stmt.where(
                    (DockerMetric.container_id == container) | (DockerMetric.container_name == container)
                )
            if start_time:
                stmt = stmt.where(DockerMetric.timestamp >= start_time)
            if end_time:
                stmt = stmt.where(DockerMetric.timestamp <= end_time)

            stmt = stmt.order_by(DockerMetric.timestamp.asc()).limit(limit)
            results = session.execute(stmt).all()

            output = []
            for row, host_name in results:
                output.append({
                    "id": row.id,
                    "hostname": host_name,
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                    "container_id": row.container_id,
                    "container_name": row.container_name,
                    "image": row.image,
                    "status": row.status,
                    "cpu_percent": float(row.cpu_percent) if row.cpu_percent is not None else None,
                    "memory_mb": float(row.memory_mb) if row.memory_mb is not None else None,
                    "network_rx": row.network_rx,
                    "network_tx": row.network_tx,
                })
            return output

    @staticmethod
    def query_summary_metrics(hostname: Optional[str] = None) -> Dict[str, Any]:
        with get_db_session() as session:
            hw_stmt = select(
                func.avg(HardwareMetric.cpu_percent).label("avg_cpu"),
                func.avg(HardwareMetric.ram_percent).label("avg_ram"),
                func.avg(HardwareMetric.disk_percent).label("avg_disk"),
                func.max(HardwareMetric.timestamp).label("latest_ts")
            ).join(Host, HardwareMetric.host_id == Host.id)

            if hostname:
                hw_stmt = hw_stmt.where(Host.hostname == hostname)

            hw_row = session.execute(hw_stmt).one_or_none()

            docker_stmt = select(func.count(DockerMetric.id)).join(Host, DockerMetric.host_id == Host.id)
            if hostname:
                docker_stmt = docker_stmt.where(Host.hostname == hostname)
            docker_count = session.scalar(docker_stmt) or 0

            avg_cpu = float(hw_row.avg_cpu) if hw_row and hw_row.avg_cpu is not None else 0.0
            avg_ram = float(hw_row.avg_ram) if hw_row and hw_row.avg_ram is not None else 0.0
            avg_disk = float(hw_row.avg_disk) if hw_row and hw_row.avg_disk is not None else 0.0
            latest_ts = hw_row.latest_ts.isoformat() if hw_row and hw_row.latest_ts else None

            return {
                "average_cpu": round(avg_cpu, 2),
                "average_ram": round(avg_ram, 2),
                "average_disk": round(avg_disk, 2),
                "docker_samples_count": docker_count,
                "latest_timestamp": latest_ts,
            }

    @staticmethod
    def purge_old_metrics(retention_days: int) -> Dict[str, int]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        with get_db_session() as session:
            del_hw = session.execute(delete(HardwareMetric).where(HardwareMetric.timestamp < cutoff)).rowcount
            del_doc = session.execute(delete(DockerMetric).where(DockerMetric.timestamp < cutoff)).rowcount
            del_ev = session.execute(delete(ConnectionEvent).where(ConnectionEvent.timestamp < cutoff)).rowcount
            del_http = session.execute(delete(HttpRequestLog).where(HttpRequestLog.timestamp < cutoff)).rowcount
            logger.info(
                f"Purged records older than {retention_days} days (cutoff: {cutoff}): "
                f"HW={del_hw}, Docker={del_doc}, Events={del_ev}, HTTP={del_http}"
            )
            return {
                "hardware_deleted": del_hw,
                "docker_deleted": del_doc,
                "events_deleted": del_ev,
                "http_deleted": del_http,
            }


class HttpRequestRepository:
    """Repository for HTTP request log persistence and queries.

    All public methods catch exceptions internally and log errors
    so that database failures never crash the API server.
    """

    @staticmethod
    def save_http_request(data: Dict[str, Any]) -> Optional[HttpRequestLog]:
        """Persists a single HTTP request log record.

        Args:
            data: Dict containing request_id, timestamp, client_ip, method,
                  path, status_code, latency_ms, user_agent, bytes_in, bytes_out.

        Returns:
            The created HttpRequestLog instance, or None on failure.
        """
        if not isinstance(data, dict):
            logger.warning("Skipping invalid HTTP request log payload: not a dict")
            return None

        try:
            ts = parse_timestamp(data.get("timestamp"))

            with get_db_session() as session:
                log_entry = HttpRequestLog(
                    request_id=data.get("request_id", ""),
                    timestamp=ts,
                    client_ip=data.get("client_ip"),
                    method=data.get("method"),
                    path=data.get("path"),
                    status_code=data.get("status_code"),
                    latency_ms=data.get("latency_ms"),
                    user_agent=data.get("user_agent"),
                    bytes_in=data.get("bytes_in"),
                    bytes_out=data.get("bytes_out"),
                )
                session.add(log_entry)
                session.flush()
                session.refresh(log_entry)
                return log_entry
        except Exception as e:
            logger.error(f"Error persisting HTTP request log: {e}")
            return None

    @staticmethod
    def get_recent_requests(limit: int = 100) -> List[Dict[str, Any]]:
        """Returns the most recent HTTP request logs, ordered newest-first.

        Args:
            limit: Maximum number of records to return (default 100).

        Returns:
            List of dicts with request log fields.
        """
        try:
            with get_db_session() as session:
                stmt = (
                    select(HttpRequestLog)
                    .order_by(HttpRequestLog.timestamp.desc())
                    .limit(limit)
                )
                results = session.scalars(stmt).all()
                return [HttpRequestRepository._row_to_dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error querying recent HTTP requests: {e}")
            return []

    @staticmethod
    def get_http_history(
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Returns HTTP request logs within a time range, ordered chronologically.

        Args:
            start: ISO-8601 start timestamp (inclusive). None = no lower bound.
            end: ISO-8601 end timestamp (inclusive). None = no upper bound.
            limit: Maximum number of records to return (default 100).

        Returns:
            List of dicts with request log fields, ordered ascending by timestamp.
        """
        try:
            start_dt = parse_timestamp(start) if start else None
            end_dt = parse_timestamp(end) if end else None

            with get_db_session() as session:
                stmt = select(HttpRequestLog)

                if start_dt:
                    stmt = stmt.where(HttpRequestLog.timestamp >= start_dt)
                if end_dt:
                    stmt = stmt.where(HttpRequestLog.timestamp <= end_dt)

                stmt = stmt.order_by(HttpRequestLog.timestamp.asc()).limit(limit)
                results = session.scalars(stmt).all()
                return [HttpRequestRepository._row_to_dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error querying HTTP history: {e}")
            return []

    @staticmethod
    def _row_to_dict(row: HttpRequestLog) -> Dict[str, Any]:
        """Converts an HttpRequestLog ORM instance to a plain dict."""
        return {
            "id": row.id,
            "request_id": row.request_id,
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            "client_ip": row.client_ip,
            "method": row.method,
            "path": row.path,
            "status_code": row.status_code,
            "latency_ms": float(row.latency_ms) if row.latency_ms is not None else None,
            "user_agent": row.user_agent,
            "bytes_in": row.bytes_in,
            "bytes_out": row.bytes_out,
        }


class HeartbeatRepository:
    """Repository for managing host heartbeat liveness records in PostgreSQL."""

    @staticmethod
    def update_host_heartbeat(hostname: str, status: str = "ONLINE", timestamp_val: Any = None) -> Optional[HostHeartbeat]:
        """Saves or updates the latest heartbeat timestamp and status for a given host."""
        try:
            ts = parse_timestamp(timestamp_val)
            with get_db_session() as session:
                host = MetricsRepository.get_or_create_host(session, hostname)
                stmt = select(HostHeartbeat).where(HostHeartbeat.host_id == host.id)
                hb = session.scalar(stmt)
                if not hb:
                    hb = HostHeartbeat(host_id=host.id, last_heartbeat=ts, status=status)
                    session.add(hb)
                else:
                    hb.last_heartbeat = ts
                    hb.status = status
                session.flush()
                session.refresh(hb)
                return hb
        except Exception as e:
            logger.error(f"Error persisting host heartbeat for {hostname}: {e}")
            return None

    @staticmethod
    def get_host_statuses() -> List[Dict[str, Any]]:
        """Returns the latest status and heartbeat timestamp for all recorded hosts."""
        try:
            with get_db_session() as session:
                stmt = select(HostHeartbeat, Host.hostname).join(Host, HostHeartbeat.host_id == Host.id)
                results = session.execute(stmt).all()
                output = []
                for hb, hostname in results:
                    output.append({
                        "hostname": hostname,
                        "status": hb.status,
                        "last_heartbeat": hb.last_heartbeat.isoformat() if hb.last_heartbeat else None
                    })
                return output
        except Exception as e:
            logger.error(f"Error querying host statuses: {e}")
            return []

