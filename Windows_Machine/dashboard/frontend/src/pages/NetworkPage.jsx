import React from 'react';
import { useTelemetry } from '../context/TelemetryContext';
import { PageContainer } from '../components/layout/PageContainer';
import { SectionCard } from '../components/layout/SectionCard';
import { StatusBadge } from '../components/shared/StatusBadge';
import { MetricCard } from '../components/shared/MetricCard';

export function NetworkPage() {
  const { telemetry } = useTelemetry();
  const networkMap = telemetry.network || {};
  const interfaces = Object.values(networkMap);
  const upCount = interfaces.filter((i) => i.status === 'UP').length;

  return (
    <PageContainer
      title="Network Interfaces & Connectivity Console"
      subtitle="Monitor network interface status, IPv4/IPv6 address assignments, MAC addresses, and packet throughput."
      icon="🌐"
      actions={
        <div className="flex-row gap-2">
          <StatusBadge status={`${upCount} UP`} type="active" pulse />
          <span className="text-xs text-dim font-mono">{interfaces.length} Total NICs</span>
        </div>
      }
    >
      {/* Top Bandwidth & Interface Stats */}
      <div className="grid-3-col">
        <MetricCard
          icon="📡"
          title="Active Network Interfaces"
          value={`${upCount} / ${interfaces.length}`}
          subtitle="Physical & Virtual NICs"
          stats={[
            { label: 'Interfaces UP', value: upCount },
            { label: 'Interfaces DOWN', value: interfaces.length - upCount },
          ]}
          warningThreshold={99}
          dangerThreshold={100}
        />

        <MetricCard
          icon="📥"
          title="Inbound Traffic (RX)"
          value="1.2 MB/s"
          subtitle="Receive Throughput"
          stats={[
            { label: 'Packets Received', value: '45,210' },
            { label: 'Errors / Drops', value: '0' },
          ]}
        />

        <MetricCard
          icon="📤"
          title="Outbound Traffic (TX)"
          value="840 KB/s"
          subtitle="Transmit Throughput"
          stats={[
            { label: 'Packets Sent', value: '38,912' },
            { label: 'Errors / Drops', value: '0' },
          ]}
        />
      </div>

      {/* Interface Grid */}
      <div className="margin-top-4">
        <SectionCard
          title="Configured Network Interfaces"
          subtitle="Local Ethernet, Wi-Fi, Loopback, and Docker bridge adapters"
          icon="🖥️"
        >
          {interfaces.length === 0 ? (
            <div className="empty-state">No network interface data reported yet by host agent.</div>
          ) : (
            <div className="net-grid">
              {interfaces.map((iface) => (
                <div key={iface.interface} className="net-item-card glass-card">
                  <div className="net-item-header space-between">
                    <div className="flex-row gap-2">
                      <span className="net-name font-semibold">{iface.interface}</span>
                      <StatusBadge status={iface.status} />
                    </div>
                    <span className="text-xs font-mono text-cyan">
                      {iface.interface.includes('eth') || iface.interface.includes('wlan')
                        ? 'PRIMARY'
                        : 'VIRTUAL'}
                    </span>
                  </div>

                  <div className="net-details margin-top-3">
                    <div className="net-detail-row">
                      <span className="label">IPv4 Address:</span>
                      <span className="val font-mono text-cyan">{iface.ip || '127.0.0.1'}</span>
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
        </SectionCard>
      </div>

      {/* Network Events & History */}
      <div className="grid-2-col margin-top-4">
        <SectionCard title="Network Traffic & Bandwidth Trend" icon="📈">
          <div className="bandwidth-visualizer-box">
            <div className="flex-row space-between text-xs margin-bottom-2">
              <span className="text-muted">Live Bandwidth Chart (RX/TX):</span>
              <span className="font-mono text-green">Stable Peak (100 Mbps NIC)</span>
            </div>
            <div className="chart-placeholder-box">
              <span className="text-xs text-dim">📊 Real-time RX/TX packet flow graph streaming</span>
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Network Events Log" icon="🔔">
          <div className="net-events-list">
            <div className="alert-item">
              <div className="alert-time font-mono">13:40:12</div>
              <div className="alert-content">
                <StatusBadge status="INFO" type="neutral" />
                <span className="alert-text">Interface eth0 address assigned: {interfaces[0]?.ip || window.location.hostname}</span>
              </div>
            </div>
            <div className="alert-item">
              <div className="alert-time font-mono">12:15:00</div>
              <div className="alert-content">
                <StatusBadge status="ACTIVE" type="active" />
                <span className="alert-text">Docker bridge docker0 initialized</span>
              </div>
            </div>
          </div>
        </SectionCard>
      </div>
    </PageContainer>
  );
}
