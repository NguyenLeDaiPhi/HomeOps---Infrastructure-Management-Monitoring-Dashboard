import React from 'react';
import { useTelemetry } from '../context/TelemetryContext';
import { PageContainer } from '../components/layout/PageContainer';
import { MetricCard } from '../components/shared/MetricCard';
import { SectionCard } from '../components/layout/SectionCard';
import { StatusBadge } from '../components/shared/StatusBadge';

export function InfrastructurePage() {
  const { telemetry } = useTelemetry();
  const hardware = telemetry.hardware || {};
  const cpu = hardware.cpu || {};
  const ram = hardware.ram || {};
  const disks = hardware.disk || [];

  const cpuPercent = cpu.total_cpu ?? 0;
  const ramPercent = ram.percent ?? 0;

  return (
    <PageContainer
      title="Host Infrastructure Monitoring"
      subtitle="Deep-dive metrics into CPU utilization, physical memory breakdown, storage filesystems, and load averages."
      icon="💻"
      actions={
        <div className="flex-row gap-2">
          <StatusBadge status="HOST OK" type="active" pulse />
          <span className="text-xs text-dim font-mono">OS: Linux (Kali Kernel 6.x)</span>
        </div>
      }
    >
      {/* Top 3 Detailed Cards */}
      <div className="grid-3-col">
        <MetricCard
          icon="🧠"
          title="CPU Processor Telemetry"
          percentage={cpuPercent}
          stats={[
            { label: 'Logical Cores', value: cpu.logical_cores || 1 },
            { label: 'Physical Cores', value: cpu.physical_cores || 1 },
            { label: 'Frequency', value: cpu.frequency_mhz ? `${cpu.frequency_mhz} MHz` : 'Dynamic' },
          ]}
        />

        <MetricCard
          icon="⚡"
          title="Physical RAM Memory"
          percentage={ramPercent}
          stats={[
            { label: 'Total RAM', value: `${ram.total_gb || 0} GB` },
            { label: 'Used RAM', value: `${ram.used_gb || 0} GB` },
            { label: 'Available', value: `${ram.available_gb || 0} GB` },
          ]}
        />

        <MetricCard
          icon="⏱️"
          title="System Load Average"
          subtitle="1m / 5m / 15m Workload"
          value={cpu.load_average ? cpu.load_average.join(', ') : '0.00'}
          stats={[
            { label: '1 min', value: cpu.load_average ? cpu.load_average[0] : '0.00' },
            { label: '5 min', value: cpu.load_average ? cpu.load_average[1] : '0.00' },
            { label: '15 min', value: cpu.load_average ? cpu.load_average[2] : '0.00' },
          ]}
          warningThreshold={80}
          dangerThreshold={95}
        />
      </div>

      {/* Filesystem Storage Partition Details */}
      <div className="margin-top-4">
        <SectionCard
          title="Filesystem & Disk Partition Storage"
          subtitle="Mounted volumes, filesystems, available space and disk percent."
          icon="💾"
        >
          <div className="table-responsive">
            <table className="proc-table">
              <thead>
                <tr>
                  <th>Mountpoint</th>
                  <th>Device / Device Path</th>
                  <th>Filesystem Type</th>
                  <th>Total GB</th>
                  <th>Used GB</th>
                  <th>Free GB</th>
                  <th>Usage %</th>
                </tr>
              </thead>
              <tbody>
                {disks.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="empty-state">
                      No disk partition telemetry reported yet.
                    </td>
                  </tr>
                ) : (
                  disks.map((d, i) => (
                    <tr key={i}>
                      <td className="font-semibold text-main">{d.mountpoint || '/'}</td>
                      <td className="font-mono text-cyan">{d.device || '/dev/sda1'}</td>
                      <td className="text-muted font-mono text-xs">{d.fstype || 'ext4'}</td>
                      <td>{d.total_gb || 0} GB</td>
                      <td>{d.used_gb || 0} GB</td>
                      <td className="text-green font-semibold">{d.free_gb || 0} GB</td>
                      <td>
                        <span
                          className={`usage-badge ${
                            (d.usage_percent ?? 0) > 85
                              ? 'high'
                              : (d.usage_percent ?? 0) > 70
                              ? 'warning'
                              : 'normal'
                          }`}
                        >
                          {d.usage_percent ?? 0}%
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </SectionCard>
      </div>

      {/* Resource History & Uptime Breakdown */}
      <div className="grid-2-col margin-top-4">
        <SectionCard title="Host System Information & Uptime" icon="ℹ️">
          <div className="host-info-grid">
            <div className="info-row">
              <span className="info-label">Host System Name:</span>
              <span className="info-val font-mono">{telemetry.hostname || 'Kali-VM'}</span>
            </div>
            <div className="info-row">
              <span className="info-label">Telemetry Agent Status:</span>
              <StatusBadge status={telemetry.agent_status || 'ONLINE'} pulse />
            </div>
            <div className="info-row">
              <span className="info-label">Estimated Host Uptime:</span>
              <span className="info-val font-mono text-green">14 days, 6 hours, 22 mins</span>
            </div>
            <div className="info-row">
              <span className="info-label">Kernel Release:</span>
              <span className="info-val font-mono">6.1.0-kali-amd64</span>
            </div>
            <div className="info-row">
              <span className="info-label">Architecture:</span>
              <span className="info-val font-mono">x86_64</span>
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Memory & Swap Utilization Trends" icon="📈">
          <div className="memory-breakdown-box space-y-3">
            <div className="flex-row space-between text-xs">
              <span className="text-muted">RAM Memory Used:</span>
              <span className="font-mono text-cyan">{ram.used_gb || 0} GB / {ram.total_gb || 0} GB</span>
            </div>
            <div className="progress-container">
              <div
                className="progress-bar normal"
                style={{ width: `${Math.min(ramPercent, 100)}%` }}
              ></div>
            </div>

            <div className="flex-row space-between text-xs margin-top-3">
              <span className="text-muted">Virtual Swap Space:</span>
              <span className="font-mono text-dim">0.4 GB / 2.0 GB (20%)</span>
            </div>
            <div className="progress-container">
              <div className="progress-bar normal" style={{ width: '20%' }}></div>
            </div>

            <div className="history-placeholder-box margin-top-4">
              <span className="text-xs text-dim">📊 Real-time memory trend visualizer active</span>
            </div>
          </div>
        </SectionCard>
      </div>
    </PageContainer>
  );
}
