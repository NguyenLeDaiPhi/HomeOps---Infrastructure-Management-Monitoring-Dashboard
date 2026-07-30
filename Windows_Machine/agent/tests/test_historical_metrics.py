import os
import sys
import pytest
from datetime import datetime, timezone, timedelta

# Ensure agent directory is in Python path for test execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set SQLite in-memory database URL for fast, isolated test execution
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from database.connection import init_db, get_db_session
from database.repositories import MetricsRepository, parse_timestamp
from database.retention import run_retention_now
from database.models import HardwareMetric, DockerMetric, Host


@pytest.fixture(autouse=True)
def setup_test_db():
    """Initializes a fresh in-memory database before each test run."""
    init_db()
    yield
    # Clean up session/tables after test
    with get_db_session() as session:
        session.query(DockerMetric).delete()
        session.query(HardwareMetric).delete()
        session.query(Host).delete()


def test_ac81_metrics_stored_in_database():
    """AC-8.1: Metrics stored in database -> Database record created."""
    payload = {
        "hostname": "kali-test-host",
        "timestamp": "2026-07-30T12:00:00Z",
        "cpu": {"total_cpu": 45.5, "logical_cores": 4},
        "ram": {"percent": 68.2, "used_gb": 3.4, "total_gb": 8.0},
        "disk": [{"mountpoint": "/", "usage_percent": 55.0, "used_gb": 22.0, "free_gb": 18.0}],
    }

    metric = MetricsRepository.save_hardware_metrics(payload)
    assert metric is not None
    assert metric.id is not None
    assert float(metric.cpu_percent) == 45.5
    assert float(metric.ram_percent) == 68.2
    assert metric.ram_used_mb == int(3.4 * 1024)

    # Verify query returns created record
    records = MetricsRepository.query_hardware_history(hostname="kali-test-host")
    assert len(records) == 1
    assert records[0]["hostname"] == "kali-test-host"


def test_ac82_timestamp_recorded():
    """AC-8.2: Timestamp recorded -> Accurate timestamp in UTC."""
    raw_timestamp = "2026-07-30T10:15:30+00:00"
    payload = {
        "hostname": "kali-timestamp-host",
        "timestamp": raw_timestamp,
        "cpu": {"total_cpu": 12.0},
    }

    metric = MetricsRepository.save_hardware_metrics(payload)
    assert metric is not None

    parsed_utc = parse_timestamp(raw_timestamp)
    assert metric.timestamp.year == 2026
    assert metric.timestamp.month == 7
    assert metric.timestamp.day == 30
    assert metric.timestamp.hour == 10
    assert metric.timestamp.minute == 15
    assert metric.timestamp.second == 30


def test_ac83_historical_query_supported():
    """AC-8.3: Historical query supported -> Time range querying & chronological ordering."""
    base_time = datetime(2026, 7, 30, 8, 0, 0, tzinfo=timezone.utc)

    # Insert 3 records spaced 1 hour apart
    for i in range(3):
        ts = base_time + timedelta(hours=i)
        payload = {
            "hostname": "chronos-host",
            "timestamp": ts.isoformat(),
            "cpu": {"total_cpu": 10.0 * (i + 1)},
        }
        MetricsRepository.save_hardware_metrics(payload)

    # Query with start and end range
    start_filter = base_time
    end_filter = base_time + timedelta(hours=1, minutes=30)

    results = MetricsRepository.query_hardware_history(
        hostname="chronos-host",
        start_time=start_filter,
        end_time=end_filter,
        limit=10,
    )

    assert len(results) == 2
    # Verify chronological ordering (ASC)
    assert results[0]["cpu_percent"] == 10.0
    assert results[1]["cpu_percent"] == 20.0


def test_ac84_missing_data_handled_gracefully():
    """AC-8.4: Missing data handled gracefully -> Null values stored, no application crash."""
    incomplete_payload = {
        "hostname": "partial-host",
        "timestamp": "2026-07-30T14:00:00Z",
        "cpu": {"usage": 22.5},
        # RAM and Disk intentionally missing!
    }

    # Should not throw any exception
    metric = MetricsRepository.save_hardware_metrics(incomplete_payload)
    assert metric is not None
    assert float(metric.cpu_percent) == 22.5
    assert metric.ram_percent is None
    assert metric.ram_used_mb is None
    assert metric.disk_percent is None

    # Completely malformed payload
    assert MetricsRepository.save_hardware_metrics(None) is None
    assert MetricsRepository.save_docker_metrics("invalid string") == []


def test_ac85_data_retention_policy_enforced():
    """AC-8.5: Data retention policy enforced -> Old records cleaned up, recent records preserved."""
    now_utc = datetime.now(timezone.utc)
    old_time = now_utc - timedelta(days=40)  # 40 days old (> 30 days retention policy)
    recent_time = now_utc - timedelta(days=5)  # 5 days old (< 30 days)

    # Insert old record
    old_payload = {
        "hostname": "retention-host",
        "timestamp": old_time.isoformat(),
        "cpu": {"total_cpu": 99.0},
    }
    MetricsRepository.save_hardware_metrics(old_payload)

    # Insert recent record
    recent_payload = {
        "hostname": "retention-host",
        "timestamp": recent_time.isoformat(),
        "cpu": {"total_cpu": 15.0},
    }
    MetricsRepository.save_hardware_metrics(recent_payload)

    # Confirm 2 records before purge
    all_before = MetricsRepository.query_hardware_history(hostname="retention-host", limit=100)
    assert len(all_before) == 2

    # Execute 30-day retention purge
    purged_counts = run_retention_now(retention_days=30)
    assert purged_counts["hardware_deleted"] == 1

    # Confirm only the recent record remains
    all_after = MetricsRepository.query_hardware_history(hostname="retention-host", limit=100)
    assert len(all_after) == 1
    assert all_after[0]["cpu_percent"] == 15.0
