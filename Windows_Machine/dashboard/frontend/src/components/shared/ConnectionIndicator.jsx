import React from 'react';

export function ConnectionIndicator({ isConnected, mode }) {
  return (
    <div className={`connection-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
      <span className="pulse-dot"></span>
      <span className="indicator-label">{isConnected ? 'ONLINE' : 'OFFLINE'}</span>
      {mode && <span className="indicator-mode font-mono">({mode})</span>}
    </div>
  );
}
