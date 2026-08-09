import os
from dotenv import load_dotenv

load_dotenv()


class WindowsConfig:
    """Configuration settings for Windows Telemetry Listener & HTTP/WebSocket Server.

    Environment variables are used for all configuration. Sensitive values and remote
    targets are required and validated at startup to prevent accidental leaks.
    """

    # Bind addresses and ports (safe development defaults)
    LISTENER_IP: str = os.getenv("LISTENER_IP", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5003"))
    WEBSOCKET_HOST: str = os.getenv("WEBSOCKET_HOST", "0.0.0.0")
    WEBSOCKET_PORT: int = int(os.getenv("WEBSOCKET_PORT", "8000"))

    # Command Gateway API (FastAPI proxy to Kali command receiver)
    COMMAND_API_HOST: str = os.getenv("COMMAND_API_HOST", "0.0.0.0")
    COMMAND_API_PORT: int = int(os.getenv("COMMAND_API_PORT", "8500"))

    # Kali agent command receiver URL (REQUIRED)
    KALI_COMMAND_URL: str = os.getenv("KALI_COMMAND_URL")

    # Shared API key for authenticating with Kali agent (REQUIRED)
    HOMEOPS_API_KEY: str = os.getenv("HOMEOPS_API_KEY")

    # Timeout (seconds) for forwarding commands to Kali
    COMMAND_TIMEOUT: float = float(os.getenv("COMMAND_TIMEOUT", "30.0"))

    # Database connection to PostgreSQL (REQUIRED)
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # JWT Authentication Settings (secret REQUIRED)
    JWT_SECRET: str = os.getenv("JWT_SECRET")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")


# Startup validation: required secrets and remote targets
_REQUIRED = [
    "HOMEOPS_API_KEY",
    "JWT_SECRET",
    "DATABASE_URL",
    "KALI_COMMAND_URL",
]

_SKIP_VALIDATION = os.getenv("PYTEST_CURRENT_TEST") or os.getenv("SKIP_ENV_VALIDATION")
if not _SKIP_VALIDATION:
    for key in _REQUIRED:
        if not os.getenv(key):
            raise RuntimeError(f"Missing required environment variable: {key}")
