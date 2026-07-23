import { useState, useEffect, useRef } from 'react';

export function useWebSocket(wsUrl = 'ws://localhost:8000', fallbackPollUrl = 'http://localhost:8000/api/state') {
  const [telemetry, setTelemetry] = useState({
    agent_status: 'OFFLINE',
    hostname: 'Kali VM (Disconnected)',
    last_updated: null,
    hardware: {},
    network: {},
    process: {},
    alerts: []
  });
  const [isConnected, setIsConnected] = useState(false);
  const [mode, setMode] = useState('Connecting...');
  const wsRef = useRef(null);

  useEffect(() => {
    let isMounted = true;
    let pollInterval = null;

    function connectWebSocket() {
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!isMounted) return;
          setIsConnected(true);
          setMode('WebSocket (Real-Time)');
          if (pollInterval) clearInterval(pollInterval);
        };

        ws.onmessage = (event) => {
          if (!isMounted) return;
          try {
            const data = JSON.parse(event.data);
            setTelemetry(data);
          } catch (err) {
            console.error('Error parsing WS message:', err);
          }
        };

        ws.onerror = () => {
          if (!isMounted) return;
          setIsConnected(false);
        };

        ws.onclose = () => {
          if (!isMounted) return;
          setIsConnected(false);
          setMode('HTTP Polling Fallback');
          startPolling();
          // Attempt reconnection in 3 seconds
          setTimeout(() => {
            if (isMounted) connectWebSocket();
          }, 3000);
        };
      } catch (e) {
        startPolling();
      }
    }

    function startPolling() {
      if (pollInterval) return;
      fetchState();
      pollInterval = setInterval(fetchState, 2000);
    }

    async function fetchState() {
      try {
        const res = await fetch(fallbackPollUrl);
        if (res.ok) {
          const data = await res.json();
          if (isMounted) {
            setTelemetry(data);
            setIsConnected(true);
          }
        }
      } catch (err) {
        if (isMounted) setIsConnected(false);
      }
    }

    connectWebSocket();

    return () => {
      isMounted = false;
      if (wsRef.current) wsRef.current.close();
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [wsUrl, fallbackPollUrl]);

  return { telemetry, isConnected, mode };
}
