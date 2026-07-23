import React from 'react';

export function AlertFeed({ alerts = [] }) {
  const getEventBadgeClass = (eventStr) => {
    if (typeof eventStr !== 'string') return 'event-default';
    if (eventStr.includes('HIGH_') || eventStr.includes('STOPPED')) return 'event-alert';
    if (eventStr.includes('STARTED') || eventStr.includes('ADDED')) return 'event-success';
    if (eventStr.includes('CHANGED')) return 'event-info';
    return 'event-default';
  };

  return (
    <div className="glass-card flex-col-card">
      <div className="card-header">
        <span className="card-icon">🔔</span>
        <h3>Real-Time Event & Alert Log</h3>
        <span className="count-badge">{alerts.length} Events</span>
      </div>

      <div className="alerts-scroll-area">
        {alerts.length === 0 ? (
          <div className="empty-state">No security or system events detected yet.</div>
        ) : (
          alerts.map((item, idx) => {
            const details = item.details || {};
            const eventName = details.event || details.alert || item.event || 'EVENT';

            return (
              <div key={idx} className="alert-item">
                <div className="alert-time font-mono">{item.timestamp || 'Just now'}</div>
                <div className="alert-content">
                  <span className={`event-badge ${getEventBadgeClass(eventName)}`}>
                    {eventName}
                  </span>
                  <span className="alert-text">
                    {details.name ? `Process: ${details.name} (PID: ${details.pid || 'N/A'})` : ''}
                    {details.interface ? ` Interface: ${details.interface}` : ''}
                    {details.old && details.new ? ` [${details.old} ➔ ${details.new}]` : ''}
                    {details.cpu ? ` CPU Spiked to ${details.cpu}%` : ''}
                    {details.memory ? ` RAM Spiked to ${details.memory}%` : ''}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
