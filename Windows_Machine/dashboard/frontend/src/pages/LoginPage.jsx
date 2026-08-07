import React, { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

export function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // If already authenticated, redirect to dashboard
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password.');
      return;
    }

    setSubmitting(true);
    const result = await login(username.trim(), password);
    setSubmitting(false);

    if (result.success) {
      navigate('/dashboard', { replace: true });
    } else {
      setError(result.message || 'Invalid username or password.');
    }
  };

  return (
    <div className="login-container">
      <div className="login-glass-card">
        {/* Header Branding */}
        <div className="login-header text-center margin-bottom-4">
          <div className="login-logo-badge margin-bottom-2">
            <span className="logo-icon">🛡️</span>
          </div>
          <h2 className="login-title">HomeOps NOC Console</h2>
          <p className="login-subtitle">Infrastructure Management & Security Monitoring System</p>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="action-error-banner margin-bottom-4" id="login-error-banner">
            <span>⚠️ {error}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group margin-bottom-3">
            <label className="input-label" htmlFor="login-username">
              USERNAME
            </label>
            <div className="input-wrapper">
              <span className="input-icon">👤</span>
              <input
                id="login-username"
                type="text"
                className="login-input font-mono"
                placeholder="Enter username (e.g. admin)"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
                autoFocus
              />
            </div>
          </div>

          <div className="form-group margin-bottom-3">
            <label className="input-label" htmlFor="login-password">
              PASSWORD
            </label>
            <div className="input-wrapper">
              <span className="input-icon">🔑</span>
              <input
                id="login-password"
                type="password"
                className="login-input font-mono"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>
          </div>

          <div className="flex-row space-between margin-bottom-4 text-xs">
            <label className="flex-row gap-2 cursor-pointer text-muted">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
              />
              <span>Remember session</span>
            </label>
            <span className="text-dim">JWT Auth Enabled</span>
          </div>

          <button
            id="login-submit-button"
            type="submit"
            className="btn btn-primary full-width-btn"
            disabled={submitting}
          >
            {submitting ? 'Authenticating...' : 'Sign In to Dashboard →'}
          </button>
        </form>
      </div>
    </div>
  );
}
