import os
from dotenv import load_dotenv

load_dotenv()


class KaliConfig:
    """Configuration settings for the Kali Linux telemetry agent.

    All environment-specific values are read from environment variables.
    Sensitive values (API keys, JWT secrets, remote hosts) are required
    and will cause an import-time error if missing.
    """

    # Remote Windows host that the Kali agent should send telemetry to.
    # This must be explicitly configured in production/dev `.env` files.
    WINDOWS_HOST: str = os.getenv("WINDOWS_HOST", "")

    # Local agent bindings and intervals (safe development defaults)
    PORT: int = int(os.getenv("PORT", "5003"))
    METRIC_INTERVAL: float = float(os.getenv("METRIC_INTERVAL", "5.0"))
    HEARTBEAT_INTERVAL: float = float(os.getenv("HEARTBEAT_INTERVAL", "5.0"))
    RECONNECT_DELAY: float = float(os.getenv("RECONNECT_DELAY", "3.0"))

    # Process monitoring thresholds (safe defaults)
    CPU_THRESHOLD: float = float(os.getenv("CPU_THRESHOLD", "20.0"))
    MEM_THRESHOLD: float = float(os.getenv("MEM_THRESHOLD", "5.0"))

    # Docker telemetry collection interval (seconds)
    DOCKER_TELEMETRY_INTERVAL: float = float(os.getenv("DOCKER_TELEMETRY_INTERVAL", "10.0"))

    # Command Receiver API (FastAPI server accepting commands on Kali)
    COMMAND_API_HOST: str = os.getenv("COMMAND_API_HOST", "0.0.0.0")
    COMMAND_API_PORT: int = int(os.getenv("COMMAND_API_PORT", "8501"))

    # Authentication / secrets - REQUIRED in production
    HOMEOPS_API_KEY: str = os.getenv("HOMEOPS_API_KEY")
    JWT_SECRET: str = os.getenv("JWT_SECRET")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")


# Startup validation: fail fast if required sensitive vars are missing
_REQUIRED = [
    "HOMEOPS_API_KEY",
    "JWT_SECRET",
    "WINDOWS_HOST",
]

_SKIP_VALIDATION = os.getenv("PYTEST_CURRENT_TEST") or os.getenv("SKIP_ENV_VALIDATION")
if not _SKIP_VALIDATION:
    for key in _REQUIRED:
        if not os.getenv(key):
            raise RuntimeError(f"Missing required environment variable: {key}")
