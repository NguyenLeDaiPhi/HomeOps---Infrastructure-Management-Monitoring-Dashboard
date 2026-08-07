import { useState, useEffect, useCallback, useRef } from 'react';
import { authFetch } from '../auth/api';

const DOCKER_API = import.meta.env.VITE_DOCKER_API_URL || 'http://localhost:8500/api/v1/docker';
const HTTP_API_BASE = DOCKER_API.replace('/api/v1/docker', '/api/v1/http');
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

export function useHttpMonitor() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [methodFilter, setMethodFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const wsRef = useRef(null);

  // Fetch recent requests from REST API
  const fetchRecent = useCallback(async () => {
    try {
      const res = await authFetch(`${HTTP_API_BASE}/recent?limit=200`);
      if (res.ok) {
        const json = await res.json();
        setRequests(json.data || []);
      }
    } catch (err) {
      console.error('Failed to fetch HTTP requests:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchRecent();
  }, [fetchRecent]);

  // Auto-refresh polling
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(fetchRecent, 3000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchRecent]);

  // WebSocket listener for real-time HTTP_REQUEST_EVENT
  useEffect(() => {
    let ws;
    try {
      ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'HTTP_REQUEST_EVENT') {
            setRequests((prev) => {
              const updated = [data, ...prev];
              // Keep max 500 in-memory entries
              return updated.length > 500 ? updated.slice(0, 500) : updated;
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
      /* WS connection fallback handled by polling */
    }

    return () => {
      if (ws) ws.close();
    };
  }, []);

  // Compute summary stats
  const totalRequests = requests.length;
  const avgLatency =
    totalRequests > 0
      ? (requests.reduce((sum, r) => sum + (r.latency_ms || 0), 0) / totalRequests).toFixed(1)
      : '0.0';
  const errorCount = requests.filter((r) => r.status_code && r.status_code >= 400).length;
  const errorRate = totalRequests > 0 ? ((errorCount / totalRequests) * 100).toFixed(1) : '0.0';
  const successCount = requests.filter(
    (r) => r.status_code && r.status_code >= 200 && r.status_code < 300
  ).length;

  // Apply filters
  const filteredRequests = requests.filter((r) => {
    if (methodFilter !== 'ALL' && r.method !== methodFilter) return false;
    if (statusFilter !== 'ALL') {
      const code = r.status_code;
      if (statusFilter === '2xx' && (code < 200 || code >= 300)) return false;
      if (statusFilter === '3xx' && (code < 300 || code >= 400)) return false;
      if (statusFilter === '4xx' && (code < 400 || code >= 500)) return false;
      if (statusFilter === '5xx' && (code < 500 || code >= 600)) return false;
    }
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      const pathMatch = (r.path || '').toLowerCase().includes(term);
      const ipMatch = (r.client_ip || '').toLowerCase().includes(term);
      if (!pathMatch && !ipMatch) return false;
    }
    return true;
  });

  return {
    requests,
    filteredRequests,
    loading,
    autoRefresh,
    setAutoRefresh,
    methodFilter,
    setMethodFilter,
    statusFilter,
    setStatusFilter,
    searchTerm,
    setSearchTerm,
    totalRequests,
    avgLatency,
    errorCount,
    errorRate,
    successCount,
    refetch: fetchRecent,
  };
}
