import os
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config.config import WindowsConfig

logger = logging.getLogger("HomeOpsDatabase")

DATABASE_URL = os.getenv("DATABASE_URL", WindowsConfig.DATABASE_URL)

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
    """Initializes database tables and seeds default admin user if none exist."""
    try:
        from database.models import (
            Host, HardwareMetric, DockerMetric, ConnectionEvent,
            HttpRequestLog, HostHeartbeat, User, RefreshToken, AuditLog
        )
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully.")

        # Seed default admin user if missing
        try:
            with get_db_session() as session:
                existing_admin = session.query(User).filter(User.username == "admin").first()
                if not existing_admin:
                    from auth.password import hash_password
                    default_admin = User(
                        username="admin",
                        password_hash=hash_password("admin123"),
                        full_name="System Administrator",
                        email="admin@homeops.local",
                        role="admin",
                        is_active=True
                    )
                    session.add(default_admin)
                    logger.info("Seeded default Super Admin user ('admin' / 'admin123').")
        except Exception as seed_err:
            logger.warning(f"Default admin user seeding warning: {seed_err}")

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
