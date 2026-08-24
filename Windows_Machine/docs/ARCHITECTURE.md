# Architecture Documentation

The canonical architecture document is [../../docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md). This file remains as a local entry point for readers browsing the Windows component. The implementation consists of `agent/windows_listen/listener.py`, the FastAPI gateway on `8500`, the raw WebSocket bridge on `8000`, PostgreSQL, and the React/Nginx Compose services.