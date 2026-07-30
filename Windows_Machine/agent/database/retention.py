import os
import time
import threading
import logging
from database.repositories import MetricsRepository

logger = logging.getLogger("MetricsRetention")

RETENTION_DAYS = int(os.getenv("METRICS_RETENTION_DAYS", "30"))
CLEANUP_INTERVAL_SECONDS = 86400  # 24 hours

def run_retention_now(retention_days: int = RETENTION_DAYS) -> dict:
    """Executes immediate cleanup of metrics older than retention_days."""
    try:
        return MetricsRepository.purge_old_metrics(retention_days)
    except Exception as e:
        logger.error(f"Error executing retention purge: {e}")
        return {"hardware_deleted": 0, "docker_deleted": 0, "events_deleted": 0}

def _retention_worker():
    logger.info(f"Retention background worker started. Policy: purge records older than {RETENTION_DAYS} days every 24h.")
    while True:
        try:
            run_retention_now(RETENTION_DAYS)
        except Exception as e:
            logger.error(f"Retention worker loop exception: {e}")
        time.sleep(CLEANUP_INTERVAL_SECONDS)

def start_retention_daemon():
    """Launches the 24-hour retention cleanup thread in daemon mode."""
    t = threading.Thread(target=_retention_worker, daemon=True, name="MetricsRetentionWorker")
    t.start()
    return t
