import React from 'react';

export function SectionCard({ title, subtitle, icon, badge, actions, children, className = '' }) {
  return (
    <div className={`glass-card section-card ${className}`}>
      {(title || icon || actions) && (
        <div className="section-card-header">
          <div className="section-header-left">
            {icon && <span className="section-icon">{icon}</span>}
            <div>
              {title && <h3 className="section-title">{title}</h3>}
              {subtitle && <p className="section-subtitle">{subtitle}</p>}
            </div>
            {badge && <span className="section-badge">{badge}</span>}
          </div>

          {actions && <div className="section-header-actions">{actions}</div>}
        </div>
      )}

      <div className="section-card-body">{children}</div>
    </div>
  );
}
