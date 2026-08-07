import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTelemetry } from '../../context/TelemetryContext';
import { useAuth } from '../../auth/AuthContext';

export function Sidebar({ collapsed, onToggle }) {
  const { telemetry } = useTelemetry();
  const { role } = useAuth();
  const userRole = (role || 'viewer').toLowerCase();

  const containerCount = telemetry.docker?.docker_info?.running ?? 0;
  const totalContainers = telemetry.docker?.docker_info?.total_containers ?? 0;
  const alertCount = telemetry.alerts ? telemetry.alerts.length : 0;
  const processCount = telemetry.process ? Object.keys(telemetry.process).length : 0;
  const netIfaceCount = telemetry.network ? Object.keys(telemetry.network).length : 0;

  const allNavItems = [
    {
      path: '/',
      label: 'Dashboard',
      icon: '📊',
      badge: null,
      roles: ['admin', 'operator', 'viewer'],
    },
    {
      path: '/infrastructure',
      label: 'Infrastructure',
      icon: '💻',
      badge: null,
      roles: ['admin', 'operator', 'viewer'],
    },
    {
      path: '/docker',
      label: 'Docker',
      icon: '🐳',
      badge: totalContainers > 0 ? `${containerCount}/${totalContainers}` : null,
      badgeType: 'info',
      roles: ['admin', 'operator'],
    },
    {
      path: '/network',
      label: 'Network',
      icon: '🌐',
      badge: netIfaceCount > 0 ? netIfaceCount : null,
      badgeType: 'neutral',
      roles: ['admin', 'operator', 'viewer'],
    },
    {
      path: '/processes',
      label: 'Processes',
      icon: '⚙️',
      badge: processCount > 0 ? processCount : null,
      badgeType: 'neutral',
      roles: ['admin', 'operator', 'viewer'],
    },
    {
      path: '/events',
      label: 'Events & Alerts',
      icon: '🔔',
      badge: alertCount > 0 ? alertCount : null,
      badgeType: 'warning',
      roles: ['admin', 'operator', 'viewer'],
    },
    {
      path: '/history',
      label: 'Historical Metrics',
      icon: '📈',
      badge: null,
      roles: ['admin', 'operator', 'viewer'],
    },
    {
      path: '/http-monitor',
      label: 'HTTP Monitoring',
      icon: '🌍',
      badge: null,
      roles: ['admin', 'operator', 'viewer'],
    },
    {
      path: '/users',
      label: 'User Accounts',
      icon: '👥',
      badge: null,
      roles: ['admin'],
    },
    {
      path: '/settings',
      label: 'Settings',
      icon: '🔧',
      badge: null,
      roles: ['admin'],
    },
  ];

  const navItems = allNavItems.filter((item) => item.roles.includes(userRole));

  return (
    <aside className={`noc-sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <button
          className="collapse-toggle-btn"
          onClick={onToggle}
          title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {collapsed ? '▶' : '◀'}
        </button>
        {!collapsed && <span className="sidebar-section-title">NAVIGATION CONSOLE</span>}
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `nav-link ${isActive ? 'active' : ''}`
            }
            title={collapsed ? item.label : undefined}
          >
            <span className="nav-icon">{item.icon}</span>
            {!collapsed && <span className="nav-label">{item.label}</span>}
            {!collapsed && item.badge && (
              <span className={`nav-badge badge-${item.badgeType || 'info'}`}>
                {item.badge}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      {!collapsed && (
        <div className="sidebar-footer-widget">
          <div className="system-health-mini">
            <span className="mini-title">AGENT CONNECTION</span>
            <div className="mini-indicator">
              <span className="pulse-dot green"></span>
              <span className="text-xs font-mono">Kali Telemetry OK</span>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
