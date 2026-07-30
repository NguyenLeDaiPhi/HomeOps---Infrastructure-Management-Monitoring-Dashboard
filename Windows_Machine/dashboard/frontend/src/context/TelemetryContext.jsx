import React, { createContext, useContext } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

const TelemetryContext = createContext(null);

export function TelemetryProvider({ children }) {
  const telemetryState = useWebSocket();

  return (
    <TelemetryContext.Provider value={telemetryState}>
      {children}
    </TelemetryContext.Provider>
  );
}

export function useTelemetry() {
  const context = useContext(TelemetryContext);
  if (!context) {
    throw new Error('useTelemetry must be used within a TelemetryProvider');
  }
  return context;
}
