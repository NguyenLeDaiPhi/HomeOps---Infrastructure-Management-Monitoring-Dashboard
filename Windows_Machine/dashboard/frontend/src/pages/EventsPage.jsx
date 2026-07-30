import React, { useState } from 'react';
import { useTelemetry } from '../context/TelemetryContext';
import { PageContainer } from '../components/layout/PageContainer';
import { SectionCard } from '../components/layout/SectionCard';
import { SearchBar } from '../components/shared/SearchBar';
import { StatusBadge } from '../components/shared/StatusBadge';

export function EventsPage() {
  const { telemetry } = useTelemetry();
  const rawAlerts = telemetry.alerts || [];

  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [acknowledgedSet, setAcknowledgedSet] = useState(new Set());

  const toggleAcknowledge = (idx) => {
    setAcknowledgedSet((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) {
        next.delete(idx);
      } else {
        next.add(idx);
      }
      return next;
    });
  };

  const getEventCategory = (item) => {
    const details = item.details || {};
    const evtStr = String(details.event || details.alert || item.event || '').toLowerCase();
    if (evtStr.includes('docker') || details.container) return 'DOCKER';
    if (evtStr.includes('proc') || details.pid || details.name) return 'PROCESS';
    if (evtStr.includes('net') || details.interface) return 'NETWORK';
    return 'SYSTEM';
  };

  const filtered = rawAlerts.filter((item, idx) => {
    const term = searchTerm.toLowerCase();
    const details = item.details || {};
    const textStr = JSON.stringify(item).toLowerCase();
    const matchesSearch = textStr.includes(term);

    if (categoryFilter === 'ALL') return matchesSearch;
    const cat = getEventCategory(item);
    return matchesSearch && cat === categoryFilter;
  });

  return (
    <PageContainer
      title="Infrastructure Events & Security Alerts"
      subtitle="Real-time event stream from Kali Agent and Windows telemetry listener."
      icon="🔔"
      actions={
        <div className="flex-row gap-2">
          <StatusBadge status={`${rawAlerts.length} Events`} type="warning" pulse />
          <span className="text-xs text-dim font-mono">
            {acknowledgedSet.size} Acknowledged
          </span>
        </div>
      }
    >
      <SectionCard
        title="Real-Time Telemetry Event Log"
        subtitle="Security events, hardware threshold warnings, process spawns, and container lifecycles."
        icon="⚡"
        actions={
          <div className="flex-row gap-2">
            <select
              className="tail-select text-xs"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <option value="ALL">All Categories</option>
              <option value="SYSTEM">System & Hardware</option>
              <option value="DOCKER">Docker Containers</option>
              <option value="PROCESS">Process Spawns</option>
              <option value="NETWORK">Network Events</option>
            </select>

            <SearchBar
              value={searchTerm}
              onChange={setSearchTerm}
              placeholder="Search event details, PIDs, containers..."
            />
          </div>
        }
      >
        <div className="alerts-scroll-area max-h-600">
          {filtered.length === 0 ? (
            <div className="empty-state">No telemetry events match your search or filter selection.</div>
          ) : (
            filtered.map((item, idx) => {
              const details = item.details || {};
              const eventName = details.event || details.alert || item.event || 'EVENT';
              const isAcked = acknowledgedSet.has(idx);
              const category = getEventCategory(item);

              let badgeType = 'neutral';
              if (eventName.includes('HIGH_') || eventName.includes('STOPPED')) badgeType = 'idle';
              if (eventName.includes('STARTED') || eventName.includes('ADDED')) badgeType = 'active';

              return (
                <div
                  key={idx}
                  className={`alert-item ${isAcked ? 'opacity-50' : ''}`}
                >
                  <div className="alert-time font-mono">
                    <span className="text-xs text-cyan">[{category}]</span>{' '}
                    {item.timestamp || 'Just now'}
                  </div>

                  <div className="alert-content space-between flex-1">
                    <div className="flex-row gap-2">
                      <StatusBadge status={eventName} type={badgeType} />
                      <span className="alert-text font-mono text-xs">
                        {details.name ? `Process: ${details.name} (PID: ${details.pid || 'N/A'})` : ''}
                        {details.interface ? ` Interface: ${details.interface}` : ''}
                        {details.old && details.new ? ` [${details.old} ➔ ${details.new}]` : ''}
                        {details.cpu ? ` CPU Spiked to ${details.cpu}%` : ''}
                        {details.memory ? ` RAM Spiked to ${details.memory}%` : ''}
                        {!details.name && !details.interface && !details.cpu && JSON.stringify(details)}
                      </span>
                    </div>

                    <button
                      className={`btn ${isAcked ? 'btn-secondary' : 'btn-primary'} text-xs`}
                      onClick={() => toggleAcknowledge(idx)}
                    >
                      {isAcked ? '✓ Acked' : 'Acknowledge'}
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </SectionCard>
    </PageContainer>
  );
}
