import os
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

logger = logging.getLogger("HomeOpsDatabase")

DEFAULT_DB_URL = "postgresql://homeops:homeops@homeops-postgres:5432/homeops"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# Fallback for SQLite in local test environments if postgres driver isn't installed
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)

class Base(DeclarativeBase):
    pass

def init_db():
    """Initializes database tables. Logs warnings if DB is unreachable on startup."""
    try:
        from database.models import Host, HardwareMetric, DockerMetric, ConnectionEvent
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully.")
        return True
    except Exception as e:
        logger.warning(f"Database initialization delayed or failed: {e}. Application will continue in transient mode.")
        return False

@contextmanager
def get_db_session():
    """Context manager for database sessions with automatic commit/rollback."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
