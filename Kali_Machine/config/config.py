import os

class KaliConfig:
    """Configuration settings for the Kali Linux telemetry agent."""
    WINDOWS_IP: str = os.getenv("WINDOWS_IP", "192.168.2.1")
    PORT: int = int(os.getenv("PORT", "5003"))
    METRIC_INTERVAL: float = float(os.getenv("METRIC_INTERVAL", "5.0"))
    RECONNECT_DELAY: float = float(os.getenv("RECONNECT_DELAY", "3.0"))
    
    # Process monitoring thresholds
    CPU_THRESHOLD: float = float(os.getenv("CPU_THRESHOLD", "20.0"))
    MEM_THRESHOLD: float = float(os.getenv("MEM_THRESHOLD", "5.0"))

    # Docker telemetry collection interval (seconds)
    # Separate from METRIC_INTERVAL because Docker stats collection is heavier
    DOCKER_TELEMETRY_INTERVAL: float = float(os.getenv("DOCKER_TELEMETRY_INTERVAL", "10.0"))

    # Command Receiver API (FastAPI server accepting commands from Windows)
    COMMAND_API_HOST: str = os.getenv("COMMAND_API_HOST", "0.0.0.0")
    COMMAND_API_PORT: int = int(os.getenv("COMMAND_API_PORT", "8501"))

    # API Key for authenticating incoming commands (shared secret with Windows)
    API_KEY: str = os.getenv("HOMEOPS_API_KEY", "homeops-dev-key-2026")

    # Allowed command origin IPs (comma-separated). Empty = allow all.
    ALLOWED_COMMAND_ORIGINS: str = os.getenv("ALLOWED_COMMAND_ORIGINS", "192.168.2.1")
