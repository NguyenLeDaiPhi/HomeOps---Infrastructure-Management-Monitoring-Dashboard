import React, { memo } from 'react';
import { useHostStatus } from '../hooks/useHostStatus';
import { SectionCard } from './layout/SectionCard';

function formatTimestamp(isoStr) {
  if (!isoStr) return 'No heartbeat received';
  try {
    const d = new Date(isoStr);
    return (
      d.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }) +
      '.' +
      String(d.getMilliseconds()).padStart(3, '0') +
      ' (' +
      d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) +
      ')'
    );
  } catch {
    return isoStr;
  }
}

function HostStatusPanelComponent() {
  const { hosts, loading } = useHostStatus();

  return (
    <SectionCard
      title="Heartbeat & Liveness Matrix"
      subtitle="Real-time host heartbeat monitoring and server-side offline detection (>30s timeout)."
      icon="💓"
    >
      <div className="table-responsive">
        <table className="proc-table host-status-table" id="host-heartbeat-table">
          <thead>
            <tr>
              <th>HOST</th>
              <th>STATUS</th>
              <th>LAST HEARTBEAT</th>
            </tr>
          </thead>
          <tbody>
            {loading && hosts.length === 0 ? (
              <tr>
                <td colSpan="3" className="empty-state">
                  Loading heartbeat monitoring data...
                </td>
              </tr>
            ) : hosts.length === 0 ? (
              <tr>
                <td colSpan="3" className="empty-state">
                  No monitored hosts registered yet.
                </td>
              </tr>
            ) : (
              hosts.map((host) => {
                const isOnline = (host.status || 'OFFLINE').toUpperCase() === 'ONLINE';
                return (
                  <tr key={host.hostname} className="host-status-row">
                    <td className="font-semibold text-main">
                      <span className="font-mono text-cyan">{host.hostname}</span>
                    </td>
                    <td>
                      <span
                        className={`status-pill ${isOnline ? 'online' : 'offline'}`}
                        id={`status-pill-${host.hostname}`}
                      >
                        <span className="pulse-dot"></span>
                        {isOnline ? 'ONLINE' : 'OFFLINE'}
                      </span>
                    </td>
                    <td className="font-mono text-xs text-muted">
                      {formatTimestamp(host.last_heartbeat)}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </SectionCard>
  );
}

export const HostStatusPanel = memo(HostStatusPanelComponent);
