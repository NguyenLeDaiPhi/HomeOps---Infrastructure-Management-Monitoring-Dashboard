import React from 'react';

export function EmptyState({ icon = '📦', message = 'No data available', description, action }) {
  return (
    <div className="empty-state-box">
      <div className="empty-icon">{icon}</div>
      <h4 className="empty-title">{message}</h4>
      {description && <p className="empty-desc">{description}</p>}
      {action && <div className="empty-action">{action}</div>}
    </div>
  );
}
