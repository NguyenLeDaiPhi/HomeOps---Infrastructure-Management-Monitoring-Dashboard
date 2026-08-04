import React, { useRef } from 'react';
import { useHttpMonitor } from '../hooks/useHttpMonitor';
import { PageContainer } from '../components/layout/PageContainer';
import { SectionCard } from '../components/layout/SectionCard';
import { SearchBar } from '../components/shared/SearchBar';
import { StatusBadge } from '../components/shared/StatusBadge';

const METHOD_COLORS = {
  GET: 'method-get',
  POST: 'method-post',
  PUT: 'method-put',
  PATCH: 'method-patch',
  DELETE: 'method-delete',
  HEAD: 'method-head',
  OPTIONS: 'method-options',
};

function getStatusClass(code) {
  if (!code) return 'http-status-unknown';
  if (code >= 500) return 'http-status-5xx';
  if (code >= 400) return 'http-status-4xx';
  if (code >= 300) return 'http-status-3xx';
  if (code >= 200) return 'http-status-2xx';
  return 'http-status-unknown';
}

function formatTimestamp(iso) {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return (
      d.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }) +
      '.' +
      String(d.getMilliseconds()).padStart(3, '0')
    );
  } catch {
    return iso;
  }
}

function formatDate(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
}

export function HttpMonitorPage() {
  const {
    filteredRequests,
    loading,
    autoRefresh,
    setAutoRefresh,
    methodFilter,
    setMethodFilter,
    statusFilter,
    setStatusFilter,
    searchTerm,
    setSearchTerm,
    totalRequests,
    avgLatency,
    errorCount,
    errorRate,
    successCount,
  } = useHttpMonitor();

  const tableRef = useRef(null);

  return (
    <PageContainer
      title="HTTP Request Monitoring"
      subtitle="Real-time visibility into every API request processed by the monitoring server."
      icon="🌍"
      actions={
        <div className="flex-row gap-2">
          <StatusBadge status={`${totalRequests} Requests`} type="info" />
          <button
            id="http-auto-refresh-toggle"
            className={`btn ${autoRefresh ? 'btn-primary' : 'btn-secondary'} text-xs`}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? '⏸ Pause' : '▶ Resume'}
          </button>
        </div>
      }
    >
      {/* Summary Stats Row */}
      <div className="http-summary-row">
        <div className="http-stat-card">
          <span className="http-stat-label">TOTAL REQUESTS</span>
          <span className="http-stat-value font-mono">{totalRequests}</span>
        </div>
        <div className="http-stat-card">
          <span className="http-stat-label">AVG LATENCY</span>
          <span className="http-stat-value font-mono text-cyan">{avgLatency} ms</span>
        </div>
        <div className="http-stat-card">
          <span className="http-stat-label">SUCCESS (2xx)</span>
          <span className="http-stat-value font-mono text-green">{successCount}</span>
        </div>
        <div className="http-stat-card">
          <span className="http-stat-label">ERROR RATE</span>
          <span
            className={`http-stat-value font-mono ${parseFloat(errorRate) > 5 ? 'text-warning' : 'text-green'
              }`}
          >
            {errorRate}%
          </span>
        </div>
        <div className="http-stat-card">
          <span className="http-stat-label">ERRORS (4xx/5xx)</span>
          <span className={`http-stat-value font-mono ${errorCount > 0 ? 'text-warning' : 'text-green'}`}>
            {errorCount}
          </span>
        </div>
      </div>

      {/* Request Feed */}
      <SectionCard
        title="Live Request Feed"
        subtitle="HTTP requests captured by FastAPI middleware — sorted newest first."
        icon="⚡"
        badge={`${filteredRequests.length} shown`}
        actions={
          <div className="flex-row gap-2">
            <select
              id="http-method-filter"
              className="tail-select text-xs"
              value={methodFilter}
              onChange={(e) => setMethodFilter(e.target.value)}
            >
              <option value="ALL">All Methods</option>
              <option value="GET">GET</option>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="PATCH">PATCH</option>
              <option value="DELETE">DELETE</option>
              <option value="HEAD">HEAD</option>
              <option value="OPTIONS">OPTIONS</option>
            </select>

            <select
              id="http-status-filter"
              className="tail-select text-xs"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="ALL">All Status</option>
              <option value="2xx">2xx Success</option>
              <option value="3xx">3xx Redirect</option>
              <option value="4xx">4xx Client Error</option>
              <option value="5xx">5xx Server Error</option>
            </select>

            <SearchBar
              value={searchTerm}
              onChange={setSearchTerm}
              placeholder="Search URL or IP..."
            />
          </div>
        }
      >
        <div className="http-table-wrapper" ref={tableRef}>
          {loading ? (
            <div className="empty-state">Loading HTTP request data...</div>
          ) : filteredRequests.length === 0 ? (
            <div className="empty-state">No HTTP requests match your filter criteria.</div>
          ) : (
            <table className="http-table" id="http-request-table">
              <thead>
                <tr>
                  <th>TIMESTAMP</th>
                  <th>CLIENT IP</th>
                  <th>METHOD</th>
                  <th>URL</th>
                  <th>STATUS</th>
                  <th>LATENCY</th>
                </tr>
              </thead>
              <tbody>
                {filteredRequests.map((req, idx) => (
                  <tr key={req.request_id || idx} className="http-row animate-http-row-in">
                    <td className="font-mono text-xs http-cell-time">
                      <span className="http-date-dim">{formatDate(req.timestamp)}</span>{' '}
                      {formatTimestamp(req.timestamp)}
                    </td>
                    <td className="font-mono text-xs">{req.client_ip || '—'}</td>
                    <td>
                      <span
                        className={`http-method-badge ${METHOD_COLORS[req.method] || 'method-get'
                          }`}
                      >
                        {req.method || '—'}
                      </span>
                    </td>
                    <td className="font-mono text-xs http-cell-path" title={req.path}>
                      {req.path || '—'}
                    </td>
                    <td>
                      <span className={`http-status-badge ${getStatusClass(req.status_code)}`}>
                        {req.status_code || '—'}
                      </span>
                    </td>
                    <td className="font-mono text-xs">
                      {req.latency_ms != null ? `${req.latency_ms.toFixed(1)} ms` : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </SectionCard>
    </PageContainer>
  );
}
