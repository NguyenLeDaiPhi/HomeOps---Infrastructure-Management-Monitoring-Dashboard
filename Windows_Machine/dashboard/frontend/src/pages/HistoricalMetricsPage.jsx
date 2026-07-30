import React, { useState } from 'react';
import { PageContainer } from '../components/layout/PageContainer';
import { SectionCard } from '../components/layout/SectionCard';
import { StatusBadge } from '../components/shared/StatusBadge';

export function HistoricalMetricsPage() {
  const [timeRange, setTimeRange] = useState('1h');

  return (
    <PageContainer
      title="Historical Metrics & Time-Series Analysis"
      subtitle="Analyze resource consumption trends over time to detect anomalies, memory leaks, and peak traffic periods."
      icon="📈"
      actions={
        <div className="flex-row gap-2">
          {['1h', '6h', '24h', '7d'].map((range) => (
            <button
              key={range}
              className={`btn ${timeRange === range ? 'btn-primary' : 'btn-secondary'} text-xs`}
              onClick={() => setTimeRange(range)}
            >
              {range}
            </button>
          ))}
        </div>
      }
    >
      <div className="grid-2-col">
        <SectionCard
          title={`CPU Processor History (${timeRange})`}
          subtitle="Time-series chart for total CPU utilization %"
          icon="🧠"
        >
          <div className="chart-placeholder-card">
            <div className="flex-row space-between text-xs margin-bottom-3">
              <span className="text-muted">Avg Utilization: 14.2%</span>
              <span className="text-cyan font-mono">Peak: 78.4%</span>
            </div>
            <div className="simulated-chart-bars">
              <div className="bar" style={{ height: '30%' }}></div>
              <div className="bar" style={{ height: '45%' }}></div>
              <div className="bar" style={{ height: '25%' }}></div>
              <div className="bar danger" style={{ height: '85%' }}></div>
              <div className="bar" style={{ height: '40%' }}></div>
              <div className="bar" style={{ height: '35%' }}></div>
              <div className="bar" style={{ height: '20%' }}></div>
              <div className="bar" style={{ height: '50%' }}></div>
            </div>
            <span className="text-xs text-dim margin-top-3 block text-center">
              Historical telemetry window: Last {timeRange}
            </span>
          </div>
        </SectionCard>

        <SectionCard
          title={`RAM Memory Trend (${timeRange})`}
          subtitle="Physical memory allocation and cached memory"
          icon="⚡"
        >
          <div className="chart-placeholder-card">
            <div className="flex-row space-between text-xs margin-bottom-3">
              <span className="text-muted">Avg Memory: 3.4 GB</span>
              <span className="text-cyan font-mono">Max Allocated: 4.8 GB</span>
            </div>
            <div className="simulated-chart-bars">
              <div className="bar" style={{ height: '60%' }}></div>
              <div className="bar" style={{ height: '62%' }}></div>
              <div className="bar" style={{ height: '65%' }}></div>
              <div className="bar" style={{ height: '64%' }}></div>
              <div className="bar" style={{ height: '70%' }}></div>
              <div className="bar" style={{ height: '68%' }}></div>
              <div className="bar" style={{ height: '65%' }}></div>
              <div className="bar" style={{ height: '66%' }}></div>
            </div>
            <span className="text-xs text-dim margin-top-3 block text-center">
              Historical telemetry window: Last {timeRange}
            </span>
          </div>
        </SectionCard>
      </div>

      <div className="grid-2-col margin-top-4">
        <SectionCard
          title={`Disk I/O & Storage Trend (${timeRange})`}
          subtitle="Read/Write throughput and disk space usage"
          icon="💾"
        >
          <div className="chart-placeholder-card">
            <div className="flex-row space-between text-xs margin-bottom-3">
              <span className="text-muted">Write Rate: 2.1 MB/s</span>
              <span className="text-cyan font-mono">Free Space: 18.4 GB</span>
            </div>
            <div className="simulated-chart-bars">
              <div className="bar" style={{ height: '20%' }}></div>
              <div className="bar" style={{ height: '22%' }}></div>
              <div className="bar" style={{ height: '21%' }}></div>
              <div className="bar" style={{ height: '30%' }}></div>
              <div className="bar" style={{ height: '25%' }}></div>
              <div className="bar" style={{ height: '20%' }}></div>
              <div className="bar" style={{ height: '22%' }}></div>
              <div className="bar" style={{ height: '23%' }}></div>
            </div>
          </div>
        </SectionCard>

        <SectionCard
          title={`Docker Container Lifecycle History (${timeRange})`}
          subtitle="Container start/stop events and runtime density"
          icon="🐳"
        >
          <div className="chart-placeholder-card">
            <div className="flex-row space-between text-xs margin-bottom-3">
              <span className="text-muted">Containers Active: 4</span>
              <span className="text-cyan font-mono">Restarts: 0</span>
            </div>
            <div className="simulated-chart-bars">
              <div className="bar active" style={{ height: '80%' }}></div>
              <div className="bar active" style={{ height: '80%' }}></div>
              <div className="bar active" style={{ height: '80%' }}></div>
              <div className="bar active" style={{ height: '80%' }}></div>
              <div className="bar active" style={{ height: '80%' }}></div>
              <div className="bar active" style={{ height: '80%' }}></div>
              <div className="bar active" style={{ height: '80%' }}></div>
              <div className="bar active" style={{ height: '80%' }}></div>
            </div>
          </div>
        </SectionCard>
      </div>
    </PageContainer>
  );
}
