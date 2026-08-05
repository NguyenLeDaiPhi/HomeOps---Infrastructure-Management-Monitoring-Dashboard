import React from 'react';
import { useTelemetry } from '../context/TelemetryContext';
import { PageContainer } from '../components/layout/PageContainer';
import { AlertFeed } from '../components/AlertFeed';

export function EventsPage() {
  const { telemetry } = useTelemetry();
  const rawAlerts = telemetry.alerts || [];

  return (
    <PageContainer
      title="Infrastructure Events & Security Alerts"
      subtitle="Real-time event stream from Kali Agent and Windows telemetry listener."
      icon="🔔"
      actions={
        <div className="flex-row gap-2">
          <span className="text-xs text-dim font-mono">{rawAlerts.length} Events</span>
        </div>
      }
    >
      <AlertFeed alerts={rawAlerts} showFilters fullWidth />
    </PageContainer>
  );
}
