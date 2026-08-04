import os

class WindowsConfig:
    """Configuration settings for Windows Telemetry Listener & HTTP/WebSocket Server."""
    LISTENER_IP: str = os.getenv("LISTENER_IP", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5003"))
    WEBSOCKET_HOST: str = os.getenv("WEBSOCKET_HOST", "0.0.0.0")
    WEBSOCKET_PORT: int = int(os.getenv("WEBSOCKET_PORT", "8000"))

    # Command Gateway API (FastAPI proxy to Kali command receiver)
    COMMAND_API_HOST: str = os.getenv("COMMAND_API_HOST", "0.0.0.0")
    COMMAND_API_PORT: int = int(os.getenv("COMMAND_API_PORT", "8500"))

    # Kali agent command receiver URL
    KALI_COMMAND_URL: str = os.getenv("KALI_COMMAND_URL", "http://192.168.2.2:8501")

    # Shared API key for authenticating with Kali agent
    API_KEY: str = os.getenv("HOMEOPS_API_KEY", "homeops-dev-key-2026")

    # Timeout (seconds) for forwarding commands to Kali
    COMMAND_TIMEOUT: float = float(os.getenv("COMMAND_TIMEOUT", "30.0"))

    # Database connection from Windows agent to database PostgreSQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://homeops:homeops@homeops-postgres:5432/homeops")
