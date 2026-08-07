import React from 'react';
import { useTelemetry } from '../../context/TelemetryContext';
import { useAuth } from '../../auth/AuthContext';

export function Header() {
  const { telemetry, isConnected, mode } = useTelemetry();
  const { user, logout } = useAuth();

  const isAgentOnline = telemetry.agent_status === 'ONLINE' || isConnected;
  const alertCount = telemetry.alerts ? telemetry.alerts.length : 0;
  const formattedLastUpdated = telemetry.last_updated
    ? new Date(telemetry.last_updated).toLocaleTimeString()
    : 'Real-time (Active)';

  const avatarInitials = user?.username
    ? user.username.slice(0, 2).toUpperCase()
    : 'US';

  const displayRole = user?.role ? user.role.toUpperCase() : 'VIEWER';

  return (
    <header className="noc-header">
      <div className="header-left">
        <div className="brand-logo">
          <span className="logo-icon">⚡</span>
          <div className="brand-text">
            <span className="brand-title">HomeOps</span>
            <span className="brand-badge">NOC CONSOLE</span>
          </div>
        </div>

        <div className="host-info-pill">
          <span className="host-icon">🖥️</span>
          <div className="host-details">
            <span className="host-label">Monitored Target</span>
            <span className="host-name">{telemetry.hostname || 'Kali-Linux-VM'}</span>
          </div>
        </div>
      </div>

      <div className="header-right">
        {/* Connection Status Pill */}
        <div className={`status-pill ${isAgentOnline ? 'online' : 'offline'}`}>
          <span className="pulse-dot"></span>
          <span className="status-text">
            {isAgentOnline ? 'AGENT ONLINE' : 'DISCONNECTED'}
          </span>
        </div>

        {/* Protocol Indicator */}
        <div className="protocol-badge font-mono">
          <span className="protocol-dot"></span>
          {mode || 'WebSocket'}
        </div>

        {/* Last Updated Timestamp */}
        <div className="last-updated text-xs font-mono">
          <span className="text-dim">Updated:</span>{' '}
          <span className="text-main">{formattedLastUpdated}</span>
        </div>

        {/* Action Widgets */}
        <div className="header-actions">
          {/* Notification Bell */}
          <div className="icon-btn-wrapper" title={`${alertCount} Active Alerts`}>
            <button className="header-icon-btn">
              🔔
              {alertCount > 0 && <span className="notification-badge">{alertCount}</span>}
            </button>
          </div>

          {/* Current User Profile Badge */}
          {user && (
            <div className="user-profile-badge">
              <div className="avatar font-mono">{avatarInitials}</div>
              <div className="user-info">
                <span className="user-name">{user.username}</span>
                <span className="user-role">{displayRole}</span>
              </div>
            </div>
          )}

          {/* Logout Button */}
          <button
            className="btn btn-secondary text-xs"
            onClick={logout}
            title="Sign Out of HomeOps"
            id="header-logout-button"
          >
            Sign Out 🚪
          </button>
        </div>
      </div>
    </header>
  );
}
