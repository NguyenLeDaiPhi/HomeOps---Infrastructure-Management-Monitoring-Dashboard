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
