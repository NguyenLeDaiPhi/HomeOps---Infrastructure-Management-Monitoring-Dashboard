import React, { useMemo } from 'react';
import { useTelemetry } from '../context/TelemetryContext';
import { PageContainer } from '../components/layout/PageContainer';
import { MetricCard } from '../components/shared/MetricCard';
import { SectionCard } from '../components/layout/SectionCard';
import { AlertFeed } from '../components/AlertFeed';
import { StatusBadge } from '../components/shared/StatusBadge';
import { Link } from 'react-router-dom';
import { HostStatusPanel } from '../components/HostStatusPanel';

export function DashboardPage() {
  const { telemetry } = useTelemetry();

  const hardware = useMemo(() => telemetry.hardware || {}, [telemetry.hardware]);
  const cpu = useMemo(() => hardware.cpu || {}, [hardware.cpu]);
  const ram = useMemo(() => hardware.ram || {}, [hardware.ram]);
  const disks = useMemo(() => hardware.disk || [], [hardware.disk]);
  const mainDisk = disks[0] || {};
  const docker = useMemo(() => telemetry.docker || {}, [telemetry.docker]);
  const dockerInfo = useMemo(() => docker.docker_info || {}, [docker.docker_info]);
  const alerts = telemetry.alerts || [];
  const networkMap = telemetry.network || {};
  const netInterfaces = useMemo(() => Object.values(networkMap), [networkMap]);

  const cpuPercent = cpu.total_cpu ?? 0;
  const ramPercent = ram.percent ?? 0;
  const diskPercent = mainDisk.usage_percent ?? 0;

  // Calculate Overall Host Health Score
  const { healthStatus, healthBadgeType } = useMemo(() => {
    const averageUsage = (cpuPercent + ramPercent + diskPercent) / 3;
    return {
      healthStatus: averageUsage > 85 ? 'DEGRADED' : averageUsage > 60 ? 'WARNING' : 'HEALTHY',
      healthBadgeType: averageUsage > 85 ? 'idle' : averageUsage > 60 ? 'warning' : 'active',
    };
  }, [cpuPercent, ramPercent, diskPercent]);

  return (
    <PageContainer
      title="Executive Overview Dashboard"
      subtitle="Real-time NOC summary across host hardware, docker containers, and active network feeds."
      icon="📊"
      actions={
        <div className="flex-row gap-2">
          <StatusBadge status={healthStatus} type={healthBadgeType} pulse />
          <span className="text-xs text-dim font-mono">Host: {telemetry.hostname || 'Kali VM'}</span>
        </div>
      }
    >
      {/* Top 4 Summary Cards */}
      <div className="grid-4-col">
        <MetricCard
          icon="🧠"
          title="CPU Processor"
          subtitle={`${cpu.logical_cores || 1} Cores`}
          percentage={cpuPercent}
          stats={[
            { label: 'Cores', value: `${cpu.logical_cores || 1} L` },
            { label: 'Load Avg', value: cpu.load_average ? cpu.load_average[0] : '0.0' },
          ]}
        />

        <MetricCard
          icon="⚡"
          title="RAM Memory"
          subtitle={`${ram.total_gb || 0} GB Total`}
          percentage={ramPercent}
          stats={[
            { label: 'Used', value: `${ram.used_gb || 0} GB` },
            { label: 'Free', value: `${ram.available_gb || 0} GB` },
          ]}
        />

        <MetricCard
          icon="💾"
          title="Disk Storage"
          subtitle={mainDisk.mountpoint || '/'}
          percentage={diskPercent}
          stats={[
            { label: 'Used', value: `${mainDisk.used_gb || 0} GB` },
            { label: 'Free', value: `${mainDisk.free_gb || 0} GB` },
          ]}
        />

        <MetricCard
          icon="🐳"
          title="Docker Containers"
          subtitle="Container Engine"
          value={`${dockerInfo.running || 0} / ${dockerInfo.total_containers || 0}`}
          stats={[
            { label: 'Running', value: dockerInfo.running || 0 },
            { label: 'Stopped', value: dockerInfo.stopped || 0 },
          ]}
          warningThreshold={99}
          dangerThreshold={100}
        />
      </div>

      {/* Middle Split: Network Quick Summary & Active Alert Feed */}
      <div className="middle-grid margin-top-4">
        {/* Network & Quick Overview */}
        <div className="flex-col gap-4">
          <SectionCard
            title="Host Status Overview"
            subtitle="Kali & Windows Telemetry Host Matrix"
            icon="🖥️"
            actions={
              <Link to="/infrastructure" className="btn btn-secondary text-xs">
                View Hardware Details →
              </Link>
            }
          >
            <div className="host-quick-grid">
              <div className="quick-info-item">
                <span className="label">Agent Status:</span>
                <StatusBadge status={telemetry.agent_status || 'ONLINE'} pulse />
              </div>
              <div className="quick-info-item">
                <span className="label">Hostname:</span>
                <span className="val font-mono">{telemetry.hostname || 'Kali-VM'}</span>
              </div>
              <div className="quick-info-item">
                <span className="label">Active Interfaces:</span>
                <span className="val font-mono">{netInterfaces.length} NICs</span>
              </div>
              <div className="quick-info-item">
                <span className="label">System Health:</span>
                <span className={`val font-semibold text-${healthBadgeType === 'active' ? 'green' : 'warning'}`}>
                  {healthStatus}
                </span>
              </div>
            </div>
          </SectionCard>

          <SectionCard
            title="Network Summary"
            subtitle="Active network interfaces & IP assignments"
            icon="🌐"
            actions={
              <Link to="/network" className="btn btn-secondary text-xs">
                Network Console →
              </Link>
            }
          >
            <div className="net-summary-list">
              {netInterfaces.slice(0, 3).map((iface) => (
                <div key={iface.interface} className="net-summary-row">
                  <div className="flex-row gap-2">
                    <span className="font-semibold text-main">{iface.interface}</span>
                    <span className="font-mono text-xs text-cyan">{iface.ip || '127.0.0.1'}</span>
                  </div>
                  <StatusBadge status={iface.status} />
                </div>
              ))}
              {netInterfaces.length === 0 && (
                <div className="empty-state text-xs py-2">No interface data available.</div>
              )}
            </div>
          </SectionCard>
        </div>

        {/* Live Alerts Feed */}
        <AlertFeed alerts={alerts} />
      </div>

      {/* Heartbeat Liveness Matrix */}
      <div className="margin-top-4">
        <HostStatusPanel />
      </div>
    </PageContainer>
  );
}
