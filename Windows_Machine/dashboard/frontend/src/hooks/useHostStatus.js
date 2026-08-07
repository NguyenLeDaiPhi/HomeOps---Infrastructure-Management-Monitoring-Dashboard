import { useState, useEffect, useCallback, useRef } from 'react';
import { authFetch } from '../auth/api';

const DOCKER_API = import.meta.env.VITE_DOCKER_API_URL || 'http://192.168.2.1:8500/api/v1/docker';
const HOSTS_STATUS_API = DOCKER_API.replace('/api/v1/docker', '/api/v1/hosts/status');
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://192.168.2.1:8000/ws';

export function useHostStatus() {
  const [hosts, setHosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const wsRef = useRef(null);

  const fetchHostStatus = useCallback(async () => {
    try {
      const res = await authFetch(HOSTS_STATUS_API);
      if (res.ok) {
        const data = await res.json();
        setHosts(Array.isArray(data) ? data : [data]);
      }
    } catch (err) {
      console.error('Error fetching host status:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHostStatus();
  }, [fetchHostStatus]);

  // WebSocket subscription for HEARTBEAT_UPDATE events
  useEffect(() => {
    let ws;
    try {
      ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'HEARTBEAT_UPDATE') {
            setHosts((prevHosts) => {
              const idx = prevHosts.findIndex((h) => h.hostname === data.hostname);
              if (idx >= 0) {
                const updated = [...prevHosts];
                updated[idx] = {
                  ...updated[idx],
                  status: data.status,
                  last_heartbeat: data.last_heartbeat,
                };
                return updated;
              } else {
                return [
                  ...prevHosts,
                  {
                    hostname: data.hostname,
                    status: data.status,
                    last_heartbeat: data.last_heartbeat,
                  },
                ];
              }
            });
          }
        } catch {
          /* ignore non-JSON */
        }
      };

      ws.onerror = () => { };
      ws.onclose = () => {
        setTimeout(() => {
          if (wsRef.current === ws) {
            wsRef.current = null;
          }
        }, 3000);
      };
    } catch {
      /* Fallback handled by interval */
    }

    return () => {
      if (ws) ws.close();
    };
  }, []);

  // Interval polling fallback every 3s
  useEffect(() => {
    const interval = setInterval(fetchHostStatus, 3000);
    return () => clearInterval(interval);
  }, [fetchHostStatus]);

  return { hosts, loading, refetch: fetchHostStatus };
}
