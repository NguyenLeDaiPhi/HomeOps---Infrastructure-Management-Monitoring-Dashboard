import datetime
import uuid
from typing import Optional, List
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Numeric,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Identity,
    func,
)
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database.connection import Base

# Integer primary key variant compatible with PostgreSQL BIGSERIAL and SQLite AUTOINCREMENT
BigId = BigInteger().with_variant(Integer, "sqlite")

class Host(Base):
    __tablename__ = "hosts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hostname: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    operating_system: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    hardware_metrics: Mapped[List["HardwareMetric"]] = relationship(
        "HardwareMetric", back_populates="host", cascade="all, delete-orphan"
    )
    docker_metrics: Mapped[List["DockerMetric"]] = relationship(
        "DockerMetric", back_populates="host", cascade="all, delete-orphan"
    )
    connection_events: Mapped[List["ConnectionEvent"]] = relationship(
        "ConnectionEvent", back_populates="host", cascade="all, delete-orphan"
    )


class HardwareMetric(Base):
    __tablename__ = "hardware_metrics"

    id: Mapped[int] = mapped_column(BigId, primary_key=True, autoincrement=True)
    host_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("hosts.id", ondelete="CASCADE"), nullable=True
    )
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    cpu_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    ram_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    ram_used_mb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ram_total_mb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    disk_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    disk_used_gb: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    disk_free_gb: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)

    host: Mapped[Optional["Host"]] = relationship("Host", back_populates="hardware_metrics")


class DockerMetric(Base):
    __tablename__ = "docker_metrics"

    id: Mapped[int] = mapped_column(BigId, primary_key=True, autoincrement=True)
    host_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("hosts.id", ondelete="CASCADE"), nullable=True
    )
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    container_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    container_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    image: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    cpu_percent: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    memory_mb: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    network_rx: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    network_tx: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    host: Mapped[Optional["Host"]] = relationship("Host", back_populates="docker_metrics")


class ConnectionEvent(Base):
    __tablename__ = "connection_events"

    id: Mapped[int] = mapped_column(BigId, primary_key=True, autoincrement=True)
    host_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("hosts.id", ondelete="CASCADE"), nullable=True
    )
    event_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    host: Mapped[Optional["Host"]] = relationship("Host", back_populates="connection_events")


class HttpRequestLog(Base):
    """Stores individual HTTP request/response logs captured by the monitoring middleware."""
    __tablename__ = "http_request_logs"

    id: Mapped[int] = mapped_column(BigId, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    client_ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    method: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bytes_in: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bytes_out: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class HostHeartbeat(Base):
    """Stores the latest heartbeat timestamp and current status (ONLINE/OFFLINE) per host."""
    __tablename__ = "host_heartbeat"

    host_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hosts.id", ondelete="CASCADE"), primary_key=True
    )
    last_heartbeat: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ONLINE")
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    host: Mapped[Optional["Host"]] = relationship("Host")


class User(Base):
    """Stores dashboard user accounts and RBAC roles (admin, operator, viewer)."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_login: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="user"
    )


class RefreshToken(Base):
    """Stores hashed JWT refresh tokens for active sessions."""
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")


class AuditLog(Base):
    """Stores audit trail of authentication events and administrative/container actions."""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigId, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    result: Mapped[str] = mapped_column(String(32), nullable=False, default="SUCCESS")

    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

