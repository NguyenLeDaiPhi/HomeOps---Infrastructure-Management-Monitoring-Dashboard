import React, { useState } from 'react';

export function ProcessTable({ processMap = {} }) {
  const [searchTerm, setSearchTerm] = useState('');
  const processes = Object.values(processMap);

  const filtered = processes.filter((proc) => {
    const term = searchTerm.toLowerCase();
    const nameStr = (proc.name || '').toLowerCase();
    const pidStr = String(proc.pid || '');
    const userStr = (proc.username || '').toLowerCase();
    return nameStr.includes(term) || pidStr.includes(term) || userStr.includes(term);
  });

  return (
    <div className="glass-card full-width-card">
      <div className="card-header space-between">
        <div className="flex-row">
          <span className="card-icon">⚙️</span>
          <h3>Active Processes Explorer</h3>
          <span className="count-badge">{filtered.length} Processes</span>
        </div>

        <div className="search-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Search by PID, Name, User..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <div className="table-responsive">
        <table className="proc-table">
          <thead>
            <tr>
              <th>PID</th>
              <th>Process Name</th>
              <th>User</th>
              <th>Status</th>
              <th>CPU %</th>
              <th>RAM %</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan="6" className="text-center py-4 text-muted">
                  No running processes match search query.
                </td>
              </tr>
            ) : (
              filtered.slice(0, 100).map((proc) => {
                const cpuVal = proc.cpu_percent || 0;
                const memVal = proc.memory_percent || 0;

                return (
                  <tr key={proc.pid}>
                    <td className="font-mono text-cyan">{proc.pid}</td>
                    <td className="font-semibold">{proc.name || 'Unknown'}</td>
                    <td className="text-muted">{proc.username || 'root'}</td>
                    <td>
                      <span className={`status-tag ${proc.status === 'running' ? 'active' : 'idle'}`}>
                        {proc.status || 'sleeping'}
                      </span>
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
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
