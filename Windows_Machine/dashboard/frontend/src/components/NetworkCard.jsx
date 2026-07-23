import React from 'react';

export function NetworkCard({ network = {} }) {
  const interfaces = Object.values(network);

  return (
    <div className="glass-card full-width-card">
      <div className="card-header">
        <span className="card-icon">🌐</span>
        <h3>Network Interfaces</h3>
        <span className="count-badge">{interfaces.length} Interfaces</span>
      </div>

      {interfaces.length === 0 ? (
        <div className="empty-state">No network interface data reported yet.</div>
      ) : (
        <div className="net-grid">
          {interfaces.map((iface) => (
            <div key={iface.interface} className="net-item-card">
              <div className="net-item-header">
                <span className="net-name">{iface.interface}</span>
                <span className={`net-status-badge ${iface.status === 'UP' ? 'up' : 'down'}`}>
                  {iface.status}
                </span>
              </div>
              <div className="net-details">
                <div className="net-detail-row">
                  <span className="label">IPv4 Address:</span>
                  <span className="val font-mono">{iface.ip || '127.0.0.1'}</span>
                </div>
                <div className="net-detail-row">
                  <span className="label">MAC Address:</span>
                  <span className="val font-mono">{iface.mac || 'N/A'}</span>
                </div>
                <div className="net-detail-row">
                  <span className="label">Subnet Mask:</span>
                  <span className="val font-mono">{iface.netmask || '255.255.255.0'}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
