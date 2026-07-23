import React from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { Header } from './components/Header';
import { HardwareGauges } from './components/HardwareGauges';
import { NetworkCard } from './components/NetworkCard';
import { AlertFeed } from './components/AlertFeed';
import { ProcessTable } from './components/ProcessTable';
import './App.css';

export function App() {
  const { telemetry, isConnected, mode } = useWebSocket();

  return (
    <div className="dashboard-container">
      <Header telemetry={telemetry} isConnected={isConnected} mode={mode} />

      <main className="dashboard-main">
        {/* Top Hardware Metrics Grid */}
        <HardwareGauges hardware={telemetry.hardware} />

        {/* Middle Split: Network Interfaces & Live Alert Log */}
        <div className="middle-grid">
          <NetworkCard network={telemetry.network} />
          <AlertFeed alerts={telemetry.alerts} />
        </div>

        {/* Bottom Full-Width Process Explorer */}
        <ProcessTable processMap={telemetry.process} />
      </main>

      <footer className="dashboard-footer">
        <p>HomeOps Infrastructure Dashboard • Kali Linux Agent & Windows Telemetry Host • 2026 Production Build</p>
      </footer>
    </div>
  );
}

export default App;
