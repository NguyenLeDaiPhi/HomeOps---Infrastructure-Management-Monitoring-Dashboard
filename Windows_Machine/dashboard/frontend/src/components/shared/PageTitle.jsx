import React from 'react';

export function PageTitle({ title, subtitle, icon, actions }) {
  return (
    <div className="page-header">
      <div className="page-header-left">
        {icon && <span className="page-header-icon">{icon}</span>}
        <div>
          <h1 className="page-title-text">{title}</h1>
          {subtitle && <p className="page-subtitle-text">{subtitle}</p>}
        </div>
      </div>

      {actions && <div className="page-header-actions">{actions}</div>}
    </div>
  );
}
