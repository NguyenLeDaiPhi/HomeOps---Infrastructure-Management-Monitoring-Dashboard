import React, { useState } from 'react';
import { useTelemetry } from '../context/TelemetryContext';
import { PageContainer } from '../components/layout/PageContainer';
import { SectionCard } from '../components/layout/SectionCard';
import { SearchBar } from '../components/shared/SearchBar';
import { StatusBadge } from '../components/shared/StatusBadge';
import { ProcessDetailModal } from '../components/shared/ProcessDetailModal';

export function ProcessesPage() {
  const { telemetry } = useTelemetry();
  const processMap = telemetry.process || {};
  const processes = Object.values(processMap);

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProcess, setSelectedProcess] = useState(null);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sortBy, setSortBy] = useState('cpu'); // 'cpu' | 'memory' | 'pid'

  const filtered = processes.filter((proc) => {
    const term = searchTerm.toLowerCase();
    const nameStr = (proc.name || '').toLowerCase();
    const pidStr = String(proc.pid || '');
    const userStr = (proc.username || '').toLowerCase();
    const matchesSearch = nameStr.includes(term) || pidStr.includes(term) || userStr.includes(term);

    if (statusFilter === 'ALL') return matchesSearch;
    return matchesSearch && proc.status?.toLowerCase() === statusFilter.toLowerCase();
  });

  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === 'cpu') return (b.cpu_percent || 0) - (a.cpu_percent || 0);
    if (sortBy === 'memory') return (b.memory_percent || 0) - (a.memory_percent || 0);
    if (sortBy === 'pid') return (a.pid || 0) - (b.pid || 0);
    return 0;
  });

  return (
    <PageContainer
      title="Host Active Processes Explorer"
      subtitle="Inspect running system tasks, resource utilization (CPU/RAM %), execution state, and target user accounts."
      icon="⚙️"
      actions={
        <div className="flex-row gap-2">
          <StatusBadge status={`${processes.length} Processes`} type="neutral" />
        </div>
      }
    >
      <SectionCard
        title="Running System Processes"
        subtitle={`Displaying top ${Math.min(sorted.length, 100)} processes`}
        icon="📋"
        actions={
          <div className="flex-row gap-2">
            <select
              className="tail-select text-xs"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="ALL">All Statuses</option>
              <option value="running">Running Only</option>
              <option value="sleeping">Sleeping / Idle</option>
            </select>

            <select
              className="tail-select text-xs"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="cpu">Sort by CPU %</option>
              <option value="memory">Sort by RAM %</option>
              <option value="pid">Sort by PID</option>
            </select>

            <SearchBar
              value={searchTerm}
              onChange={setSearchTerm}
              placeholder="Search by PID, Name, User..."
            />
          </div>
        }
      >
        <div className="table-responsive">
          <table className="proc-table">
            <thead>
              <tr>
                <th>PID</th>
                <th>Process Name</th>
                <th>User Account</th>
                <th>Execution Status</th>
                <th>CPU Utilization %</th>
                <th>RAM Memory %</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {sorted.length === 0 ? (
                <tr>
                  <td colSpan="7" className="empty-state">
                    No active processes match filter criteria.
                  </td>
                </tr>
              ) : (
                sorted.slice(0, 100).map((proc) => {
                  const cpuVal = proc.cpu_percent || 0;
                  const memVal = proc.memory_percent || 0;

                  return (
                    <tr key={proc.pid} className="cursor-pointer" onClick={() => setSelectedProcess(proc)}>
                      <td className="font-mono text-cyan font-semibold">{proc.pid}</td>
                      <td className="font-semibold text-main">{proc.name || 'Unknown'}</td>
                      <td className="text-muted text-xs font-mono">{proc.username || 'root'}</td>
                      <td>
                        <StatusBadge status={proc.status || 'running'} />
                      </td>
                      <td>
                        <span className={`usage-badge ${cpuVal > 20 ? 'high' : 'normal'}`}>
                          {cpuVal}%
                        </span>
                      </td>
                      <td>
                        <span className={`usage-badge ${memVal > 10 ? 'high' : 'normal'}`}>
                          {memVal}%
                        </span>
                      </td>
                      <td>
                        <button
                          className="btn btn-secondary text-xs"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedProcess(proc);
                          }}
                        >
                          Inspect 🔍
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </SectionCard>

      {/* Process Inspector Modal */}
      {selectedProcess && (
        <ProcessDetailModal
          process={selectedProcess}
          onClose={() => setSelectedProcess(null)}
        />
      )}
    </PageContainer>
  );
}
