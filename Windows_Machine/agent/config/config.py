import os

class WindowsConfig:
    """Configuration settings for Windows Telemetry Listener & HTTP/WebSocket Server."""
    LISTENER_IP: str = os.getenv("LISTENER_IP", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5003"))
    WEBSOCKET_HOST: str = os.getenv("WEBSOCKET_HOST", "0.0.0.0")
    WEBSOCKET_PORT: int = int(os.getenv("WEBSOCKET_PORT", "8000"))
