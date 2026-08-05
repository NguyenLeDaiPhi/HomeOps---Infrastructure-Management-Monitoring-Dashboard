import { useState, useCallback } from 'react';

const COMMAND_GATEWAY_URL =
  import.meta.env.VITE_DOCKER_API_URL || 'http://192.168.2.1:8500/api/v1/docker';

export function useDockerApi(baseUrl = COMMAND_GATEWAY_URL) {
  const [loadingMap, setLoadingMap] = useState({});
  const [actionError, setActionError] = useState(null);
  const [logsModal, setLogsModal] = useState({ open: false, containerName: '', logs: '', loading: false });

  const setContainerLoading = (containerId, action, isLoading) => {
    setLoadingMap((prev) => ({
      ...prev,
      [`${containerId}_${action}`]: isLoading,
    }));
  };

  const isContainerLoading = (containerId, action) => {
    return !!loadingMap[`${containerId}_${action}`];
  };

  const sendCommand = useCallback(
    async (containerId, action) => {
      setActionError(null);
      setContainerLoading(containerId, action, true);

      try {
        const response = await fetch(`${baseUrl}/containers/${containerId}/${action}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const data = await response.json();

        if (!response.ok) {
          const errDetail = data.detail || data;
          const msg = errDetail.message || `Failed to ${action} container`;
          setActionError({ containerId, action, message: msg, code: errDetail.error_code });
          return { success: false, message: msg };
        }

        return { success: true, data };
      } catch (err) {
        const msg = `Network error calling ${action} container: ${err.message}`;
        setActionError({ containerId, action, message: msg, code: 'NETWORK_ERROR' });
        return { success: false, message: msg };
      } finally {
        setContainerLoading(containerId, action, false);
      }
    },
    [baseUrl]
  );

  const fetchLogs = useCallback(
    async (containerId, containerName, tail = 100) => {
      setLogsModal({ open: true, containerName, logs: '', loading: true });
      try {
        const response = await fetch(
          `${baseUrl}/containers/${containerId}/logs?tail=${tail}`
        );
        const data = await response.json();
        if (response.ok) {
          setLogsModal({ open: true, containerName, logs: data.logs || 'No log output.', loading: false });
        } else {
          const errMsg = data.detail?.message || 'Failed to load logs.';
          setLogsModal({ open: true, containerName, logs: `Error: ${errMsg}`, loading: false });
        }
      } catch (err) {
        setLogsModal({ open: true, containerName, logs: `Network error: ${err.message}`, loading: false });
      }
    },
    [baseUrl]
  );

  const closeLogsModal = () => {
    setLogsModal({ open: false, containerName: '', logs: '', loading: false });
  };

  return {
    sendCommand,
    fetchLogs,
    closeLogsModal,
    logsModal,
    isContainerLoading,
    actionError,
    clearError: () => setActionError(null),
  };
}
