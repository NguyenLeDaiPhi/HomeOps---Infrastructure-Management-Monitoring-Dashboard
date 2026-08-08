import React, { useState } from 'react';
import { PageContainer } from '../components/layout/PageContainer';
import { SectionCard } from '../components/layout/SectionCard';
import { StatusBadge } from '../components/shared/StatusBadge';
import { ActionButton } from '../components/shared/ActionButton';

export function SettingsPage() {
  const defaultOrigin = `${window.location.protocol}//${window.location.host}`;
  const [wsUrl, setWsUrl] = useState(
    import.meta.env.VITE_WS_URL || `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws`
  );
  const [apiUrl, setApiUrl] = useState(
    import.meta.env.VITE_API_URL || `${defaultOrigin}/api/state`
  );
  const [dockerApiUrl, setDockerApiUrl] = useState(
    import.meta.env.VITE_DOCKER_API_URL || `${defaultOrigin}/api/v1/docker`
  );
  const [kaliTarget, setKaliTarget] = useState('192.168.1.150');
  const [refreshInterval, setRefreshInterval] = useState(2000);
  const [cpuThreshold, setCpuThreshold] = useState(80);
  const [ramThreshold, setRamThreshold] = useState(85);
  const [diskThreshold, setDiskThreshold] = useState(90);

  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const res = await fetch(apiUrl);
      if (res.ok) {
        setTestResult({
          success: true,
          message: 'Connection successful! Telemetry backend & REST API are reachable.',
        });
      } else {
        setTestResult({
          success: false,
          message: `Backend returned status ${res.status}. Check API server endpoint.`,
        });
      }
    } catch (err) {
      setTestResult({
        success: false,
        message: `Connection failed: ${err.message}. Verify listener & CORS configuration.`,
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <PageContainer
      title="NOC Operations & System Configuration"
      subtitle="Configure target agent endpoints, API gateway routing, telemetry refresh frequency, and security alert thresholds."
      icon="🔧"
    >
      <div className="grid-2-col">
        {/* Network & Endpoints Settings */}
        <SectionCard
          title="Telemetry Endpoints & Gateways"
          subtitle="Configure WebSocket and REST API endpoints"
          icon="🌐"
        >
          <div className="settings-form space-y-4">
            <div className="form-group">
              <label className="form-label">WebSocket Telemetry URL</label>
              <input
                type="text"
                className="form-input font-mono"
                value={wsUrl}
                onChange={(e) => setWsUrl(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">HTTP Polling API Fallback URL</label>
              <input
                type="text"
                className="form-input font-mono"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Docker REST API Gateway Endpoint</label>
              <input
                type="text"
                className="form-input font-mono"
                value={dockerApiUrl}
                onChange={(e) => setDockerApiUrl(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Kali Target Machine IP / Hostname</label>
              <input
                type="text"
                className="form-input font-mono"
                value={kaliTarget}
                onChange={(e) => setKaliTarget(e.target.value)}
              />
            </div>

            {testResult && (
              <div
                className={`alert-item margin-top-3 ${testResult.success ? 'event-success' : 'event-alert'
                  }`}
              >
                <div className="alert-content">
                  <StatusBadge
                    status={testResult.success ? 'SUCCESS' : 'FAILED'}
                    type={testResult.success ? 'active' : 'idle'}
                  />
                  <span className="alert-text font-mono text-xs">{testResult.message}</span>
                </div>
              </div>
            )}

            <div className="form-actions margin-top-4">
              <ActionButton
                variant="primary"
                loading={testing}
                onClick={handleTestConnection}
              >
                Test Connection to Gateway
              </ActionButton>
            </div>
          </div>
        </SectionCard>

        {/* Polling & Alert Threshold Settings */}
        <SectionCard
          title="Telemetry Frequency & Thresholds"
          subtitle="Set warning & critical thresholds for system alerts"
          icon="⚡"
        >
          <div className="settings-form space-y-4">
            <div className="form-group">
              <label className="form-label">
                HTTP Fallback Refresh Interval ({refreshInterval} ms)
              </label>
              <input
                type="range"
                min="1000"
                max="10000"
                step="500"
                className="form-range"
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
              />
              <span className="text-xs text-dim">
                Interval between HTTP state polls if WebSocket disconnects.
              </span>
            </div>

            <div className="form-group margin-top-4">
              <label className="form-label">CPU High Usage Warning Threshold ({cpuThreshold}%)</label>
              <input
                type="range"
                min="50"
                max="95"
                className="form-range"
                value={cpuThreshold}
                onChange={(e) => setCpuThreshold(Number(e.target.value))}
              />
            </div>

            <div className="form-group margin-top-3">
              <label className="form-label">RAM Memory Warning Threshold ({ramThreshold}%)</label>
              <input
                type="range"
                min="50"
                max="95"
                className="form-range"
                value={ramThreshold}
                onChange={(e) => setRamThreshold(Number(e.target.value))}
              />
            </div>

            <div className="form-group margin-top-3">
              <label className="form-label">Disk Capacity Warning Threshold ({diskThreshold}%)</label>
              <input
                type="range"
                min="50"
                max="98"
                className="form-range"
                value={diskThreshold}
                onChange={(e) => setDiskThreshold(Number(e.target.value))}
              />
            </div>

            <div className="form-actions margin-top-4">
              <button className="btn btn-secondary">Save Configuration Preferences</button>
            </div>
          </div>
        </SectionCard>
      </div>
    </PageContainer>
  );
}
