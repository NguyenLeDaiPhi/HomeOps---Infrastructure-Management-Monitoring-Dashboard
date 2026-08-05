import React, { memo, useEffect, useMemo, useRef, useState } from 'react';

const SEVERITY_MAP = {
  alert: ['HIGH_', 'STOPPED', 'FAILED', 'ERROR'],
  success: ['STARTED', 'ADDED', 'CREATED', 'UP'],
  info: ['CHANGED', 'UPDATED', 'DETECTED', 'NOTIFIED'],
};

function getEventCategory(eventName) {
  if (typeof eventName !== 'string') return 'default';
  const normalized = eventName.toUpperCase();
  if (SEVERITY_MAP.alert.some((token) => normalized.includes(token))) return 'alert';
  if (SEVERITY_MAP.success.some((token) => normalized.includes(token))) return 'success';
  if (SEVERITY_MAP.info.some((token) => normalized.includes(token))) return 'info';
  return 'default';
}

function normalizeEventName(item) {
  const details = item.details || {};
  return details.event || details.alert || item.event || item.message || 'EVENT';
}

function buildAlertSummary(item) {
  const details = item.details || {};
  const parts = [];

  if (details.name) parts.push(`Process: ${details.name}${details.pid ? ` (PID ${details.pid})` : ''}`);
  if (details.interface) parts.push(`Interface: ${details.interface}`);
  if (details.ip) parts.push(`IP: ${details.ip}`);
  if (details.old && details.new) parts.push(`Change: ${details.old} → ${details.new}`);
  if (details.cpu) parts.push(`CPU: ${details.cpu}%`);
  if (details.memory) parts.push(`RAM: ${details.memory}%`);
  if (details.service) parts.push(`Service: ${details.service}`);
  if (details.container) parts.push(`Container: ${details.container}`);

  return parts.length > 0 ? parts.join(' · ') : item.message || details.message || 'No additional details available.';
}

function getAlertKey(item, idx) {
  if (item.id) return item.id;
  if (item.timestamp) return `${item.timestamp}-${normalizeEventName(item)}-${idx}`;
  return idx;
}

function AlertFeedComponent({ alerts = [], showFilters = false, fullWidth = false }) {
  const [filterQuery, setFilterQuery] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [autoScrollEnabled, setAutoScrollEnabled] = useState(true);
  const scrollRef = useRef(null);

  const filteredAlerts = useMemo(() => {
    const query = filterQuery.trim().toLowerCase();

    return alerts
      .slice()
      .sort((a, b) => {
        const aTime = new Date(a.timestamp || '').getTime() || 0;
        const bTime = new Date(b.timestamp || '').getTime() || 0;
        return bTime - aTime;
      })
      .filter((item) => {
        const eventName = normalizeEventName(item).toLowerCase();
        const summary = buildAlertSummary(item).toLowerCase();
        const matchesQuery = !query || eventName.includes(query) || summary.includes(query);
        const category = getEventCategory(eventName);
        const matchesSeverity = filterSeverity === 'all' || category === filterSeverity;
        return matchesQuery && matchesSeverity;
      });
  }, [alerts, filterQuery, filterSeverity]);

  useEffect(() => {
    if (!autoScrollEnabled || !scrollRef.current) return;
    scrollRef.current.scrollTop = 0;
  }, [filteredAlerts, autoScrollEnabled]);

  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    setAutoScrollEnabled(el.scrollTop <= 20);
  };

  return (
    <div className={`glass-card flex-col-card ${fullWidth ? 'full-width-card' : ''}`}>
      <div className="card-header">
        <span className="card-icon">🔔</span>
        <div>
          <h3>Real-Time Event & Alert Log</h3>
          <p className="section-subtitle">Search, filter, and review the latest system alerts without losing your read position.</p>
        </div>
        <span className="count-badge">{filteredAlerts.length} Events</span>
      </div>

      {showFilters && (
        <div className="alert-filters">
          <input
            type="search"
            className="alert-filter-input"
            placeholder="Search process, interface, event type..."
            value={filterQuery}
            onChange={(event) => setFilterQuery(event.target.value)}
          />
          <select
            className="alert-filter-select"
            value={filterSeverity}
            onChange={(event) => setFilterSeverity(event.target.value)}
          >
            <option value="all">All Severities</option>
            <option value="alert">Alerts</option>
            <option value="info">Info</option>
            <option value="success">Success</option>
            <option value="default">Other</option>
          </select>
        </div>
      )}

      <div className="alerts-scroll-area" ref={scrollRef} onScroll={handleScroll}>
        {filteredAlerts.length === 0 ? (
          <div className="empty-state">No matching alerts found.</div>
        ) : (
          filteredAlerts.map((item, idx) => {
            const eventName = normalizeEventName(item);
            const summary = buildAlertSummary(item);
            const severityClass = `event-badge event-${getEventCategory(eventName)}`;

            return (
              <div key={getAlertKey(item, idx)} className="alert-item">
                <div className="alert-time font-mono">{item.timestamp || 'Just now'}</div>
                <div className="alert-content">
                  <div className="alert-header-row">
                    <span className={severityClass}>{eventName}</span>
                    <span className="alert-meta-item">{item.source || item.type || 'Telemetry'}</span>
                  </div>
                  <div className="alert-text">{summary}</div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

export const AlertFeed = memo(AlertFeedComponent);
