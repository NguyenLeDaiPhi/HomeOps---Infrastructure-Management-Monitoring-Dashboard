import React from 'react';

export function ActionButton({
  children,
  onClick,
  variant = 'primary',
  disabled = false,
  loading = false,
  icon,
  title,
  className = '',
}) {
  return (
    <button
      className={`btn btn-${variant} ${loading ? 'loading' : ''} ${className}`}
      onClick={onClick}
      disabled={disabled || loading}
      title={title}
    >
      {loading ? (
        <span className="btn-spinner">⏳</span>
      ) : icon ? (
        <span className="btn-icon">{icon}</span>
      ) : null}
      <span className="btn-label">{children}</span>
    </button>
  );
}
