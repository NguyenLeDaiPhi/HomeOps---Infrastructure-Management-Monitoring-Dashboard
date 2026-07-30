import React from 'react';

export function MetricCard({
  icon,
  title,
  subtitle,
  value,
  percentage,
  unit = '%',
  stats = [],
  warningThreshold = 65,
  dangerThreshold = 85,
  className = '',
}) {
  const numValue = typeof percentage === 'number' ? percentage : Number(value) || 0;
  const statusClass =
    numValue >= dangerThreshold
      ? 'danger'
      : numValue >= warningThreshold
      ? 'warning'
      : 'normal';

  return (
    <div className={`glass-card metric-card ${statusClass} ${className}`}>
      <div className="card-header space-between">
        <div className="flex-row gap-2">
          {icon && <span className="card-icon">{icon}</span>}
          <div>
            <h3 className="metric-title">{title}</h3>
            {subtitle && <span className="metric-subtitle">{subtitle}</span>}
          </div>
        </div>
        <span className={`metric-badge ${statusClass}`}>
          {percentage !== undefined ? `${percentage}%` : value}
        </span>
      </div>

      {percentage !== undefined && (
        <div className="progress-container margin-y-3">
          <div
            className={`progress-bar ${statusClass}`}
            style={{ width: `${Math.min(Math.max(percentage, 0), 100)}%` }}
          ></div>
        </div>
      )}

      {stats && stats.length > 0 && (
        <div className="card-stats-row">
          {stats.map((stat, idx) => (
            <div key={idx} className="stat-col">
              <span className="stat-label">{stat.label}</span>
              <span className="stat-val">{stat.value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
