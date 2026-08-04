import { useState, useEffect, useCallback } from 'react';

const API_BASE = import.meta.env.VITE_DOCKER_API_URL || 'http://localhost:8500/api/v1/docker';
const HISTORY_BASE = API_BASE.replace('/docker', '/history');

export function useHistoricalMetrics() {
  const [timeRange, setTimeRange] = useState('1h');
  const [hostFilter, setHostFilter] = useState('');
  const [containerFilter, setContainerFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [summary, setSummary] = useState({
    average_cpu: 0,
    average_ram: 0,
    average_disk: 0,
    docker_samples_count: 0,
    latest_timestamp: null,
  });

  const [hardwareHistory, setHardwareHistory] = useState([]);
  const [dockerHistory, setDockerHistory] = useState([]);

  // Pagination state
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const fetchHistoricalData = useCallback(async () => {
    setLoading(true);
    setError(null);

    // Calculate ISO start timestamp based on timeRange
    const now = new Date();
    let startTime = null;
    if (timeRange === '1h') startTime = new Date(now.getTime() - 60 * 60 * 1000);
    else if (timeRange === '6h') startTime = new Date(now.getTime() - 6 * 60 * 60 * 1000);
    else if (timeRange === '24h') startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    else if (timeRange === '7d') startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

    const startIso = startTime ? startTime.toISOString() : undefined;

    try {
      // 1. Fetch Summary
      const sumUrl = new URL(`${HISTORY_BASE}/summary`);
      if (hostFilter) sumUrl.searchParams.append('host', hostFilter);
      const sumRes = await fetch(sumUrl.toString());
      if (sumRes.ok) {
        const sumData = await sumRes.json();
        if (sumData.summary) setSummary(sumData.summary);
      }

      // 2. Fetch Hardware History
      const hwUrl = new URL(`${HISTORY_BASE}/hardware`);
      if (hostFilter) hwUrl.searchParams.append('host', hostFilter);
      if (startIso) hwUrl.searchParams.append('start', startIso);
      hwUrl.searchParams.append('limit', '200');

      const hwRes = await fetch(hwUrl.toString());
      if (hwRes.ok) {
        const hwData = await hwRes.json();
        setHardwareHistory(hwData.data || []);
      }

      // 3. Fetch Docker History
      const docUrl = new URL(`${HISTORY_BASE}/docker`);
      if (hostFilter) docUrl.searchParams.append('host', hostFilter);
      if (containerFilter) docUrl.searchParams.append('container', containerFilter);
      if (startIso) docUrl.searchParams.append('start', startIso);
      docUrl.searchParams.append('limit', '200');

      const docRes = await fetch(docUrl.toString());
      if (docRes.ok) {
        const docData = await docRes.json();
        setDockerHistory(docData.data || []);
      }
    } catch (err) {
      console.error('Error fetching historical metrics:', err);
      setError(`Failed to load historical data from PostgreSQL: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [timeRange, hostFilter, containerFilter]);

  useEffect(() => {
    fetchHistoricalData();
  }, [fetchHistoricalData]);

  // Paginated Hardware History slice
  const totalPages = Math.ceil(hardwareHistory.length / pageSize) || 1;
  const paginatedHardware = hardwareHistory.slice((page - 1) * pageSize, page * pageSize);

  // Compute Peak CPU / Max RAM
  const peakCpu = hardwareHistory.reduce((max, d) => (d.cpu_percent > max ? d.cpu_percent : max), 0);
  const maxRam = hardwareHistory.reduce((max, d) => ((d.ram_used_mb || 0) > max ? d.ram_used_mb : max), 0);

  return {
    timeRange,
    setTimeRange,
    hostFilter,
    setHostFilter,
    containerFilter,
    setContainerFilter,
    loading,
    error,
    summary,
    hardwareHistory,
    dockerHistory,
    page,
    setPage,
    totalPages,
    paginatedHardware,
    peakCpu,
    maxRam,
    refetch: fetchHistoricalData,
  };
}
