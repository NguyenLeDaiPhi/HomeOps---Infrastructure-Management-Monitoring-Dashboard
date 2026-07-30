import React, { useState } from 'react';
import { useTelemetry } from '../context/TelemetryContext';
import { useDockerApi } from '../hooks/useDockerApi';
import { PageContainer } from '../components/layout/PageContainer';
import { SectionCard } from '../components/layout/SectionCard';
import { SearchBar } from '../components/shared/SearchBar';
import { StatusBadge } from '../components/shared/StatusBadge';
import { ActionButton } from '../components/shared/ActionButton';

export function DockerPage() {
  const { telemetry } = useTelemetry();
  const docker = telemetry.docker || {};
  const { containers = [], docker_info = {} } = docker;

  const [searchTerm, setSearchTerm] = useState('');
  const [expandedId, setExpandedId] = useState(null);
  const [logTail, setLogTail] = useState(100);

  const {
    sendCommand,
    fetchLogs,
    closeLogsModal,
    logsModal,
    isContainerLoading,
    actionError,
    clearError,
  } = useDockerApi();

  const filtered = containers.filter((c) => {
    const term = searchTerm.toLowerCase();
    const name = (c.name || '').toLowerCase();
    const image = (c.image || '').toLowerCase();
    const status = (c.status || '').toLowerCase();
    const id = (c.container_id || '').toLowerCase();
    return name.includes(term) || image.includes(term) || status.includes(term) || id.includes(term);
  });

  const toggleExpand = (cid) => {
    setExpandedId(expandedId === cid ? null : cid);
  };

  const handleAction = async (containerId, action) => {
    await sendCommand(containerId, action);
  };

  return (
    <PageContainer
      title="Docker Container Operations Console"
      subtitle="Manage Docker containers, inspect runtime statistics, volume mounts, restart policies, and stream real-time logs."
      icon="🐳"
      actions={
        <div className="flex-row gap-2">
          <StatusBadge
            status={`${docker_info.running || 0} RUNNING`}
            type="active"
            pulse
          />
          <StatusBadge
            status={`${docker_info.stopped || 0} STOPPED`}
            type="idle"
          />
        </div>
      }
    >
      {/* Summary Stat Pills */}
      <div className="docker-summary-pills">
        <div className="summary-pill pill-total">
          <span className="pill-label">Total Containers</span>
          <span className="pill-val">{docker_info.total_containers || 0}</span>
        </div>
        <div className="summary-pill pill-running">
          <span className="pill-label">Active / Running</span>
          <span className="pill-val text-green">{docker_info.running || 0}</span>
        </div>
        <div className="summary-pill pill-stopped">
          <span className="pill-label">Stopped / Exited</span>
          <span className="pill-val text-dim">{docker_info.stopped || 0}</span>
        </div>
        <div className="summary-pill pill-paused">
          <span className="pill-label">Paused</span>
          <span className="pill-val text-warning">{docker_info.paused || 0}</span>
        </div>
      </div>

      {/* Action Error Banner */}
      {actionError && (
        <div className="action-error-banner margin-top-4">
          <div className="banner-content">
            <span className="banner-icon">⚠️</span>
            <span>
              <strong>Command Error ({actionError.code}):</strong> {actionError.message}
            </span>
          </div>
          <button className="banner-close" onClick={clearError}>✕</button>
        </div>
      )}

      {/* Main Containers Table Card */}
      <div className="margin-top-4">
        <SectionCard
          title="Container Inventory & Actions"
          subtitle={`${filtered.length} containers matching filter criteria`}
          icon="📦"
          actions={
            <SearchBar
              value={searchTerm}
              onChange={setSearchTerm}
              placeholder="Search by container name, image, ID, or status..."
            />
          }
        >
          <div className="table-responsive">
            <table className="proc-table docker-table">
              <thead>
                <tr>
                  <th>Container ID</th>
                  <th>Name</th>
                  <th>Image</th>
                  <th>Status</th>
                  <th>CPU %</th>
                  <th>Memory</th>
                  <th>Ports</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="empty-state">
                      {containers.length === 0
                        ? 'No Docker telemetry received from Kali agent yet (or Docker daemon is idle).'
                        : 'No containers match search query.'}
                    </td>
                  </tr>
                ) : (
                  filtered.map((c) => {
                    const isRunning = c.status === 'running';
                    const isStopped = c.status === 'exited' || c.status === 'created';
                    const stats = c.stats || {};
                    const cpuVal = stats.cpu_percent || 0;
                    const memMb = stats.memory_usage_mb || 0;
                    const isExpanded = expandedId === c.container_id;

                    const isStarting = isContainerLoading(c.container_id, 'start');
                    const isStopping = isContainerLoading(c.container_id, 'stop');
                    const isRestarting = isContainerLoading(c.container_id, 'restart');

                    return (
                      <React.Fragment key={c.container_id}>
                        <tr className={isExpanded ? 'row-expanded' : ''}>
                          {/* ID */}
                          <td
                            className="font-mono text-cyan cursor-pointer"
                            onClick={() => toggleExpand(c.container_id)}
                          >
                            <span className="expand-indicator">{isExpanded ? '▼' : '▶'}</span>{' '}
                            {c.container_id}
                          </td>

                          {/* Name */}
                          <td className="font-semibold text-main">
                            <span
                              className="container-name-btn"
                              onClick={() => toggleExpand(c.container_id)}
                            >
                              {c.name}
                            </span>
                          </td>

                          {/* Image */}
                          <td className="text-muted font-mono text-xs">{c.image}</td>

                          {/* Status Tag */}
                          <td>
                            <StatusBadge status={c.status} />
                          </td>

                          {/* CPU % */}
                          <td>
                            <span className={`usage-badge ${cpuVal > 20 ? 'high' : 'normal'}`}>
                              {cpuVal}%
                            </span>
                          </td>

                          {/* Memory */}
                          <td>
                            <span className="stat-val font-mono text-xs">
                              {memMb > 0 ? `${memMb} MB` : '-'}
                            </span>
                          </td>

                          {/* Ports */}
                          <td className="text-xs font-mono text-dim">
                            {c.ports && c.ports.length > 0
                              ? c.ports.map((p, i) => (
                                  <span key={i} className="port-badge">
                                    {p.host_port
                                      ? `${p.host_port}:${p.container_port}`
                                      : `${p.container_port}`}
                                  </span>
                                ))
                              : '-'}
                          </td>

                          {/* Action Buttons */}
                          <td>
                            <div className="btn-group">
                              {!isRunning && (
                                <ActionButton
                                  variant="start"
                                  loading={isStarting}
                                  disabled={isRestarting}
                                  onClick={() => handleAction(c.container_id, 'start')}
                                  title="Start Container"
                                >
                                  Start
                                </ActionButton>
                              )}

                              {isRunning && (
                                <ActionButton
                                  variant="stop"
                                  loading={isStopping}
                                  disabled={isRestarting}
                                  onClick={() => handleAction(c.container_id, 'stop')}
                                  title="Stop Container"
                                >
                                  Stop
                                </ActionButton>
                              )}

                              <ActionButton
                                variant="restart"
                                loading={isRestarting}
                                disabled={isStarting || isStopping}
                                onClick={() => handleAction(c.container_id, 'restart')}
                                title="Restart Container"
                              >
                                Restart
                              </ActionButton>

                              <ActionButton
                                variant="logs"
                                onClick={() => fetchLogs(c.container_id, c.name, logTail)}
                                title="View Container Logs"
                              >
                                Logs
                              </ActionButton>
                            </div>
                          </td>
                        </tr>

                        {/* Expandable Detail Sub-Row */}
                        {isExpanded && (
                          <tr className="detail-row">
                            <td colSpan="8">
                              <div className="container-detail-panel animate-fade-in">
                                <div className="detail-col">
                                  <h4>🔧 Container Metadata</h4>
                                  <p><strong>Full ID:</strong> <span className="font-mono text-xs">{c.container_id_full}</span></p>
                                  <p><strong>Created:</strong> {c.created || 'N/A'}</p>
                                  <p><strong>Restart Count:</strong> {c.restart_count ?? 0}</p>
                                  <p><strong>Restart Policy:</strong> <span className="font-mono text-cyan">{c.restart_policy || 'no'}</span></p>
                                </div>

                                <div className="detail-col">
                                  <h4>🌐 Networks & Port Bindings</h4>
                                  <p><strong>Networks:</strong> {(c.networks || []).join(', ') || 'bridge'}</p>
                                  <p><strong>Port Map:</strong></p>
                                  <ul className="detail-list">
                                    {(c.ports || []).map((p, idx) => (
                                      <li key={idx}>
                                        {p.host_ip}:{p.host_port} → {p.container_port}/{p.protocol}
                                      </li>
                                    ))}
                                    {(!c.ports || c.ports.length === 0) && <li>No active port bindings</li>}
                                  </ul>
                                </div>

                                <div className="detail-col">
                                  <h4>💾 Volumes & Mount Points</h4>
                                  <ul className="detail-list">
                                    {(c.mounts || []).map((m, idx) => (
                                      <li key={idx}>
                                        <code>{m.source}</code> → <code>{m.destination}</code> ({m.mode})
                                      </li>
                                    ))}
                                    {(!c.mounts || c.mounts.length === 0) && <li>No volume mounts attached</li>}
                                  </ul>
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </SectionCard>
      </div>

      {/* Container Log Viewer Modal */}
      {logsModal.open && (
        <div className="modal-overlay" onClick={closeLogsModal}>
          <div className="modal-content glass-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="flex-row">
                <span className="card-icon">📜</span>
                <h3>Container Output Logs — {logsModal.containerName}</h3>
              </div>
              <div className="flex-row">
                <select
                  className="tail-select"
                  value={logTail}
                  onChange={(e) => {
                    const newTail = Number(e.target.value);
                    setLogTail(newTail);
                  }}
                >
                  <option value={50}>50 Lines</option>
                  <option value={100}>100 Lines</option>
                  <option value={250}>250 Lines</option>
                  <option value={500}>500 Lines</option>
                </select>
                <button className="btn btn-close" onClick={closeLogsModal}>✕</button>
              </div>
            </div>

            <div className="modal-body">
              {logsModal.loading ? (
                <div className="logs-loading">Fetching log stdout / stderr output...</div>
              ) : (
                <pre className="logs-pre font-mono">{logsModal.logs}</pre>
              )}
            </div>

            <div className="modal-footer">
              <span className="text-dim text-xs">Connected to Docker REST Daemon API (Port 8500)</span>
              <button className="btn btn-secondary" onClick={closeLogsModal}>Close</button>
            </div>
          </div>
        </div>
      )}
    </PageContainer>
  );
}
