import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { PageContainer } from '../components/layout/PageContainer';
import { SectionCard } from '../components/layout/SectionCard';

export function ProtectedRoute({ children, allowedRoles = null }) {
  const { isAuthenticated, user, role, loading } = useAuth();

  if (loading) {
    return (
      <div className="auth-loading-spinner">
        <div className="spinner"></div>
        <span>Authenticating NOC session...</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && allowedRoles.length > 0) {
    const userRole = (role || '').toLowerCase();
    const hasRole = allowedRoles.map((r) => r.toLowerCase()).includes(userRole);

    if (!hasRole) {
      return (
        <PageContainer
          title="403 — Access Forbidden"
          subtitle="Role-Based Access Control Restriction"
          icon="🚫"
        >
          <SectionCard
            title="Insufficient Permissions"
            subtitle={`Your account role is '${userRole?.toUpperCase()}'`}
            icon="🔒"
          >
            <div className="empty-state text-center py-8">
              <span className="banner-icon font-mono text-xl block margin-bottom-2">⚠️</span>
              <h4 className="text-main font-semibold margin-bottom-2">
                Access Denied for Role '{userRole?.toUpperCase()}'
              </h4>
              <p className="text-muted text-xs max-w-md margin-auto">
                This page or administrative action requires one of the following permissions:{' '}
                <span className="text-cyan font-mono">{allowedRoles.join(', ').toUpperCase()}</span>.
                Contact your HomeOps System Administrator to request elevated access.
              </p>
            </div>
          </SectionCard>
        </PageContainer>
      );
    }
  }

  return children;
}
