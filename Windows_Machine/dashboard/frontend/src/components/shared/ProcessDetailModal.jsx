import React from 'react';

export function ProcessDetailModal({ process, onClose }) {
  if (!process) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content glass-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="flex-row">
            <span className="card-icon">⚙️</span>
            <h3>Process Detail — {process.name} (PID: {process.pid})</h3>
          </div>
          <button className="btn btn-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body space-y-4">
          <div className="detail-grid">
            <div className="detail-box">
              <span className="label">Process ID (PID)</span>
              <span className="val font-mono text-cyan">{process.pid}</span>
            </div>
            <div className="detail-box">
              <span className="label">Executable Name</span>
              <span className="val font-semibold">{process.name}</span>
            </div>
            <div className="detail-box">
              <span className="label">Running User</span>
              <span className="val">{process.username || 'root'}</span>
            </div>
            <div className="detail-box">
              <span className="label">Execution Status</span>
              <span className="val text-green">{process.status || 'running'}</span>
            </div>
            <div className="detail-box">
              <span className="label">CPU Usage</span>
              <span className="val font-mono text-warning">{process.cpu_percent || 0}%</span>
            </div>
            <div className="detail-box">
              <span className="label">RAM Memory Usage</span>
              <span className="val font-mono text-cyan">{process.memory_percent || 0}%</span>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Close Inspector</button>
        </div>
      </div>
    </div>
  );
}
