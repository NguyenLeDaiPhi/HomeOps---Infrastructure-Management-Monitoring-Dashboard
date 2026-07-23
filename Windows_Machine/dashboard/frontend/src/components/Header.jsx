import React from 'react';

export function Header({ telemetry, isConnected, mode }) {
  const isAgentOnline = telemetry.agent_status === 'ONLINE';

  return (
    <header className="dashboard-header">
      <div className="header-brand">
        <div className="logo-icon">⚡</div>
        <div>
          <h1>HomeOps Monitoring Console</h1>
          <p className="subtitle">Infrastructure & Host Telemetry System • Windows & Kali Linux Host-Only VM</p>
        </div>
      </div>

      <div className="header-meta">
        <div className="meta-badge">
          <span className="meta-label">Target Host:</span>
          <span className="meta-value font-mono">{telemetry.hostname || 'kali-vm'}</span>
        </div>

        <div className="meta-badge">
          <span className="meta-label">Protocol:</span>
          <span className="meta-value text-blue">{mode}</span>
        </div>

        <div className={`status-pill ${isAgentOnline ? 'online' : 'offline'}`}>
          <span className="pulse-dot"></span>
          {isAgentOnline ? 'KALI AGENT ONLINE' : 'AGENT DISCONNECTED'}
        </div>
      </div>
    </header>
  );
}
