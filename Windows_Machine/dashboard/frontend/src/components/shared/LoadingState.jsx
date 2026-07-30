import React from 'react';

export function LoadingState({ message = 'Loading infrastructure telemetry...' }) {
  return (
    <div className="loading-state-box">
      <div className="loading-spinner-ring"></div>
      <p className="loading-text font-mono">{message}</p>
    </div>
  );
}
