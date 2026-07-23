import React from 'react';

export function HardwareGauges({ hardware = {} }) {
  const cpu = hardware.cpu || {};
  const ram = hardware.ram || {};
  const disks = hardware.disk || [];

  const cpuPercent = cpu.total_cpu ?? 0;
  const ramPercent = ram.percent ?? 0;
  const mainDisk = disks[0] || {};
  const diskPercent = mainDisk.usage_percent ?? 0;

  return (
    <div className="gauges-grid">
      {/* CPU Utilization Card */}
      <div className="glass-card metric-card">
        <div className="card-header">
          <span className="card-icon">🧠</span>
          <h3>CPU Processor</h3>
          <span className="metric-badge">{cpuPercent}%</span>
        </div>
        <div className="progress-container">
          <div 
            className={`progress-bar ${cpuPercent > 80 ? 'danger' : cpuPercent > 50 ? 'warning' : 'normal'}`} 
            style={{ width: `${Math.min(cpuPercent, 100)}%` }}
          ></div>
        </div>
        <div className="card-stats-row">
          <div>
            <span className="stat-label">Cores</span>
            <span className="stat-val">{cpu.logical_cores || 1} L / {cpu.physical_cores || 1} P</span>
          </div>
          <div>
            <span className="stat-label">Frequency</span>
            <span className="stat-val">{cpu.frequency_mhz ? `${cpu.frequency_mhz} MHz` : 'Dynamic'}</span>
          </div>
          <div>
            <span className="stat-label">Load Avg</span>
            <span className="stat-val">{cpu.load_average ? cpu.load_average.join(', ') : '0.00'}</span>
          </div>
        </div>
      </div>

      {/* RAM Memory Card */}
      <div className="glass-card metric-card">
        <div className="card-header">
          <span className="card-icon">⚡</span>
          <h3>System RAM</h3>
          <span className="metric-badge">{ramPercent}%</span>
        </div>
        <div className="progress-container">
          <div 
            className={`progress-bar ${ramPercent > 85 ? 'danger' : ramPercent > 65 ? 'warning' : 'normal'}`} 
            style={{ width: `${Math.min(ramPercent, 100)}%` }}
          ></div>
        </div>
        <div className="card-stats-row">
          <div>
            <span className="stat-label">Used RAM</span>
            <span className="stat-val">{ram.used_gb || 0} GB</span>
          </div>
          <div>
            <span className="stat-label">Available</span>
            <span className="stat-val">{ram.available_gb || 0} GB</span>
          </div>
          <div>
            <span className="stat-label">Total RAM</span>
            <span className="stat-val">{ram.total_gb || 0} GB</span>
          </div>
        </div>
      </div>

      {/* Disk Storage Card */}
      <div className="glass-card metric-card">
        <div className="card-header">
          <span className="card-icon">💾</span>
          <h3>Disk Storage ({mainDisk.mountpoint || '/'})</h3>
          <span className="metric-badge">{diskPercent}%</span>
        </div>
        <div className="progress-container">
          <div 
            className={`progress-bar ${diskPercent > 90 ? 'danger' : diskPercent > 70 ? 'warning' : 'normal'}`} 
            style={{ width: `${Math.min(diskPercent, 100)}%` }}
          ></div>
        </div>
        <div className="card-stats-row">
          <div>
            <span className="stat-label">Used Disk</span>
            <span className="stat-val">{mainDisk.used_gb || 0} GB</span>
          </div>
          <div>
            <span className="stat-label">Free Space</span>
            <span className="stat-val">{mainDisk.free_gb || 0} GB</span>
          </div>
          <div>
            <span className="stat-label">Filesystem</span>
            <span className="stat-val">{mainDisk.fstype || 'ext4'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
