import React, { useState, useEffect, useCallback } from 'react';
import { PageContainer } from '../components/layout/PageContainer';
import { SectionCard } from '../components/layout/SectionCard';
import { StatusBadge } from '../components/shared/StatusBadge';
import { MetricCard } from '../components/shared/MetricCard';

const API_BASE = import.meta.env.VITE_DOCKER_API_URL || 'http://localhost:8500/api/v1/docker';
const HISTORY_BASE = API_BASE.replace('/docker', '/history');

export function HistoricalMetricsPage() {
  const [timeRange, setTimeRange] = useState('1h');
  const [hostFilter, setHostFilter] = useState('');
  const [containerFilter, setContainerFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [summary, setSummary] = useState({
    average_cpu: 0,
    average_ram: 0,
    average_disk: 0,
    docker_samples_count: 0,
    latest_timestamp: null,
  });

  const [hardwareHistory, setHardwareHistory] = useState([]);
  const [dockerHistory, setDockerHistory] = useState([]);

  // Pagination state
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const fetchHistoricalData = useCallback(async () => {
    setLoading(true);
    setError(null);

    // Calculate ISO start timestamp based on timeRange
    const now = new Date();
    let startTime = null;
    if (timeRange === '1h') startTime = new Date(now.getTime() - 60 * 60 * 1000);
    else if (timeRange === '6h') startTime = new Date(now.getTime() - 6 * 60 * 60 * 1000);
    else if (timeRange === '24h') startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    else if (timeRange === '7d') startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

    const startIso = startTime ? startTime.toISOString() : undefined;

    try {
      // 1. Fetch Summary
      const sumUrl = new URL(`${HISTORY_BASE}/summary`);
      if (hostFilter) sumUrl.searchParams.append('host', hostFilter);
      const sumRes = await fetch(sumUrl.toString());
      if (sumRes.ok) {
        const sumData = await sumRes.json();
        if (sumData.summary) setSummary(sumData.summary);
      }

      // 2. Fetch Hardware History
      const hwUrl = new URL(`${HISTORY_BASE}/hardware`);
      if (hostFilter) hwUrl.searchParams.append('host', hostFilter);
      if (startIso) hwUrl.searchParams.append('start', startIso);
      hwUrl.searchParams.append('limit', '200');

      const hwRes = await fetch(hwUrl.toString());
      if (hwRes.ok) {
        const hwData = await hwRes.json();
        setHardwareHistory(hwData.data || []);
      }

      // 3. Fetch Docker History
      const docUrl = new URL(`${HISTORY_BASE}/docker`);
      if (hostFilter) docUrl.searchParams.append('host', hostFilter);
      if (containerFilter) docUrl.searchParams.append('container', containerFilter);
      if (startIso) docUrl.searchParams.append('start', startIso);
      docUrl.searchParams.append('limit', '200');

      const docRes = await fetch(docUrl.toString());
      if (docRes.ok) {
        const docData = await docRes.json();
        setDockerHistory(docData.data || []);
      }
    } catch (err) {
      logger_err(err);
      setError(`Failed to load historical data from PostgreSQL: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [timeRange, hostFilter, containerFilter]);

  function logger_err(err) {
    console.error('Error fetching historical metrics:', err);
  }

  useEffect(() => {
    fetchHistoricalData();
  }, [fetchHistoricalData]);

  // Paginated Hardware History slice
  const totalPages = Math.ceil(hardwareHistory.length / pageSize) || 1;
  const paginatedHardware = hardwareHistory.slice((page - 1) * pageSize, page * pageSize);

  // Compute Peak CPU / Max RAM / Free Disk from returned data
  const peakCpu = hardwareHistory.reduce((max, d) => (d.cpu_percent > max ? d.cpu_percent : max), 0);
  const maxRam = hardwareHistory.reduce((max, d) => ((d.ram_used_mb || 0) > max ? d.ram_used_mb : max), 0);

  return (
    <PageContainer
      title="Historical Telemetry & PostgreSQL Analysis"
      subtitle="Query time-series hardware metrics, RAM allocation, and Docker container samples stored in PostgreSQL database."
      icon="📈"
      actions={
        <div className="flex-row gap-2">
          {['1h', '6h', '24h', '7d', 'all'].map((range) => (
            <button
              key={range}
              className={`btn ${timeRange === range ? 'btn-primary' : 'btn-secondary'} text-xs`}
              onClick={() => {
                setTimeRange(range);
                setPage(1);
              }}
            >
              {range.toUpperCase()}
            </button>
          ))}
        </div>
      }
    >
      {/* Top Historical Summary Metrics Cards */}
      <div className="grid-4-col">
        <MetricCard
          icon="🧠"
          title="Historical Avg CPU"
          subtitle={`Window: ${timeRange}`}
          percentage={summary.average_cpu}
          stats={[{ label: 'Peak CPU', value: `${peakCpu.toFixed(1)}%` }]}
        />

        <MetricCard
          icon="⚡"
          title="Historical Avg RAM"
          subtitle="Memory Usage"
          percentage={summary.average_ram}
          stats={[{ label: 'Peak Memory', value: `${(maxRam / 1024).toFixed(2)} GB` }]}
        />

        <MetricCard
          icon="💾"
          title="Historical Avg Disk"
          subtitle="Storage Capacity"
          percentage={summary.average_disk}
          stats={[{ label: 'Status', value: summary.average_disk > 85 ? 'HIGH' : 'NORMAL' }]}
        />

        <MetricCard
          icon="🐳"
          title="Docker Database Samples"
          subtitle="Stored Container Metric Rows"
          value={summary.docker_samples_count}
          stats={[{ label: 'Latest Audit', value: summary.latest_timestamp ? summary.latest_timestamp.split('T')[1]?.slice(0, 8) : 'N/A' }]}
          warningThreshold={99999}
          dangerThreshold={100000}
        />
      </div>

      {error && (
        <div className="action-error-banner margin-top-4">
          <span>⚠️ {error}</span>
        </div>
      )}

      {/* Dynamic Simulated Time-Series Visualizer Charts */}
      <div className="grid-2-col margin-top-4">
        <SectionCard
          title={`CPU Processor Utilization History (${timeRange})`}
          subtitle={`${hardwareHistory.length} total PostgreSQL metric points`}
          icon="🧠"
        >
          <div className="chart-placeholder-card">
            <div className="flex-row space-between text-xs margin-bottom-3">
              <span className="text-muted">Avg Utilization: {summary.average_cpu}%</span>
              <span className="text-cyan font-mono">Peak: {peakCpu}%</span>
            </div>
            <div className="simulated-chart-bars">
              {hardwareHistory.length === 0 ? (
                <div className="empty-state text-xs w-full text-center py-8">
                  No historical CPU metric samples recorded in selected time window.
                </div>
              ) : (
                hardwareHistory.slice(-16).map((item, idx) => (
                  <div
                    key={idx}
                    className={`bar ${item.cpu_percent > 80 ? 'danger' : ''}`}
                    style={{ height: `${Math.min(item.cpu_percent || 5, 100)}%` }}
                    title={`${item.timestamp}: ${item.cpu_percent}% CPU`}
                  ></div>
                ))
              )}
            </div>
            <span className="text-xs text-dim margin-top-3 block text-center">
              PostgreSQL `hardware_metrics` time-series timeline ({timeRange})
            </span>
          </div>
        </SectionCard>

        <SectionCard
          title={`RAM Memory Allocation History (${timeRange})`}
          subtitle="Physical memory allocation stored in database"
          icon="⚡"
        >
          <div className="chart-placeholder-card">
            <div className="flex-row space-between text-xs margin-bottom-3">
              <span className="text-muted">Avg Memory %: {summary.average_ram}%</span>
              <span className="text-cyan font-mono">Max Used: {(maxRam / 1024).toFixed(2)} GB</span>
            </div>
            <div className="simulated-chart-bars">
              {hardwareHistory.length === 0 ? (
                <div className="empty-state text-xs w-full text-center py-8">
                  No historical RAM metric samples recorded in selected time window.
                </div>
              ) : (
                hardwareHistory.slice(-16).map((item, idx) => (
                  <div
                    key={idx}
                    className="bar"
                    style={{ height: `${Math.min(item.ram_percent || 5, 100)}%` }}
                    title={`${item.timestamp}: ${item.ram_percent}% RAM`}
                  ></div>
                ))
              )}
            </div>
            <span className="text-xs text-dim margin-top-3 block text-center">
              PostgreSQL `hardware_metrics` memory trend
            </span>
          </div>
        </SectionCard>
      </div>

      {/* Historical Data Table with Pagination & Filters */}
      <div className="margin-top-4">
        <SectionCard
          title="Historical Hardware Metrics Audit Log"
          subtitle={`Displaying page ${page} of ${totalPages} (${hardwareHistory.length} total records)`}
          icon="📋"
          actions={
            <div className="flex-row gap-2">
              <button
                className="btn btn-secondary text-xs"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
              >
                ◀ Prev
              </button>
              <span className="text-xs font-mono text-cyan">
                Page {page} / {totalPages}
              </span>
              <button
                className="btn btn-secondary text-xs"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
              >
                Next ▶
              </button>
            </div>
          }
        >
          <div className="table-responsive">
            <table className="proc-table">
              <thead>
                <tr>
                  <th>Record ID</th>
                  <th>Timestamp (UTC)</th>
                  <th>Hostname</th>
                  <th>CPU %</th>
                  <th>RAM %</th>
                  <th>RAM Used (MB)</th>
                  <th>Disk %</th>
                  <th>Free Disk (GB)</th>
                </tr>
              </thead>
              <tbody>
                {paginatedHardware.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="empty-state">
                      {loading ? 'Querying PostgreSQL database...' : 'No historical metrics found for this query.'}
                    </td>
                  </tr>
                ) : (
                  paginatedHardware.map((row) => (
                    <tr key={row.id}>
                      <td className="font-mono text-cyan">{row.id}</td>
                      <td className="font-mono text-xs">{row.timestamp || 'N/A'}</td>
                      <td className="font-semibold text-main">{row.hostname}</td>
                      <td>
                        <span className={`usage-badge ${row.cpu_percent > 80 ? 'high' : 'normal'}`}>
                          {row.cpu_percent !== null ? `${row.cpu_percent}%` : 'NULL'}
                        </span>
                      </td>
                      <td>
                        <span className={`usage-badge ${row.ram_percent > 80 ? 'high' : 'normal'}`}>
                          {row.ram_percent !== null ? `${row.ram_percent}%` : 'NULL'}
                        </span>
                      </td>
                      <td className="font-mono text-xs">
                        {row.ram_used_mb !== null ? `${row.ram_used_mb} MB` : 'NULL'}
                      </td>
                      <td>
                        <span className={`usage-badge ${row.disk_percent > 85 ? 'high' : 'normal'}`}>
                          {row.disk_percent !== null ? `${row.disk_percent}%` : 'NULL'}
                        </span>
                      </td>
                      <td className="font-mono text-xs text-green">
                        {row.disk_free_gb !== null ? `${row.disk_free_gb} GB` : 'NULL'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </SectionCard>
      </div>

      {/* Docker Historical Metrics Table */}
      <div className="margin-top-4">
        <SectionCard
          title="Historical Docker Container Samples"
          subtitle={`${dockerHistory.length} container samples retrieved from PostgreSQL`}
          icon="🐳"
        >
          <div className="table-responsive">
            <table className="proc-table">
              <thead>
                <tr>
                  <th>Record ID</th>
                  <th>Timestamp (UTC)</th>
                  <th>Container Name</th>
                  <th>Container ID</th>
                  <th>Image</th>
                  <th>Status</th>
                  <th>CPU %</th>
                  <th>Memory (MB)</th>
                </tr>
              </thead>
              <tbody>
                {dockerHistory.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="empty-state">
                      {loading ? 'Querying PostgreSQL database...' : 'No historical Docker metric samples found.'}
                    </td>
                  </tr>
                ) : (
                  dockerHistory.slice(0, 15).map((d) => (
                    <tr key={d.id}>
                      <td className="font-mono text-cyan">{d.id}</td>
                      <td className="font-mono text-xs">{d.timestamp}</td>
                      <td className="font-semibold text-main">{d.container_name || 'N/A'}</td>
                      <td className="font-mono text-xs text-cyan">{d.container_id || 'N/A'}</td>
                      <td className="font-mono text-xs text-muted">{d.image || 'N/A'}</td>
                      <td>
                        <StatusBadge status={d.status || 'unknown'} />
                      </td>
                      <td>
                        <span className="usage-badge normal">{d.cpu_percent !== null ? `${d.cpu_percent}%` : 'NULL'}</span>
                      </td>
                      <td className="font-mono text-xs">{d.memory_mb !== null ? `${d.memory_mb} MB` : 'NULL'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </SectionCard>
      </div>
    </PageContainer>
  );
}
