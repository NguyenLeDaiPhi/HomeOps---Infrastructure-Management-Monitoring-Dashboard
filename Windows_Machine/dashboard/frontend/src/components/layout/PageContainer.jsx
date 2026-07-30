import React from 'react';
import { PageTitle } from '../shared/PageTitle';

export function PageContainer({ title, subtitle, icon, actions, children }) {
  return (
    <div className="page-container animate-fade-in">
      {(title || subtitle) && (
        <PageTitle title={title} subtitle={subtitle} icon={icon} actions={actions} />
      )}
      <div className="page-content">{children}</div>
    </div>
  );
}
