import React from 'react';
import { useTelemetry } from '../../context/TelemetryContext';

export function Footer() {
  const { mode, isConnected } = useTelemetry();

  return (
    <footer className="noc-footer">
      <div className="footer-col">
        <span className="footer-brand font-semibold">HomeOps Infrastructure NOC</span>
        <span className="footer-version">v2.4.0 Enterprise Build</span>
      </div>

      <div className="footer-center font-mono text-xs">
        <span className="status-item">
          <span className={`status-dot ${isConnected ? 'active' : 'inactive'}`}></span>
          <span>WS: {mode}</span>
        </span>
        <span className="divider">•</span>
        <span className="status-item">
          <span className="status-dot active"></span>
          <span>REST Gateway: HTTP/8500</span>
        </span>
        <span className="divider">•</span>
        <span className="status-item">
          <span className="status-dot active"></span>
          <span>Kali Agent: v1.2.0</span>
        </span>
      </div>

      <div className="footer-col text-right text-xs text-muted">
        <span>© 2026 HomeOps NOC • Production Infrastructure Monitoring</span>
      </div>
    </footer>
  );
}
