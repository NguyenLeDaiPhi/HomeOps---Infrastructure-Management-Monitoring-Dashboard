import React from 'react';

export function StatusBadge({ status, label, type, pulse = false }) {
  const statusStr = String(status || label || '').toLowerCase();
  
  let variant = type;
  if (!variant) {
    if (['online', 'running', 'active', 'up', 'success', 'ok'].includes(statusStr)) {
      variant = 'active';
    } else if (['offline', 'stopped', 'exited', 'down', 'critical', 'danger', 'failed'].includes(statusStr)) {
      variant = 'idle';
    } else if (['warning', 'paused', 'connecting', 'restarting'].includes(statusStr)) {
      variant = 'warning';
    } else {
      variant = 'neutral';
    }
  }

  return (
    <span className={`status-tag status-${variant}`}>
      {pulse && <span className="pulse-dot-sm"></span>}
      {label || status || 'UNKNOWN'}
    </span>
  );
}
