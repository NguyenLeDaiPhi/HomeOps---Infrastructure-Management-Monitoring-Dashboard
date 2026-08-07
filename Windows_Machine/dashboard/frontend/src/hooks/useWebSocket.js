import { useEffect, useReducer, useRef, useState, useMemo } from 'react';
import { authFetch } from '../auth/api';

const WS_URL =
  import.meta.env.VITE_WS_URL || 'ws://192.168.2.1:8000/ws';

const API_URL =
  import.meta.env.VITE_API_URL || 'http://192.168.2.1:8000/api/state';

const initialTelemetry = {
  agent_status: 'OFFLINE',
  hostname: 'Kali VM (Disconnected)',
  last_updated: null,
  hardware: {},
  network: {},
  process: {},
  docker: {
    containers: [],
    docker_info: {
      total_containers: 0,
      running: 0,
      paused: 0,
      stopped: 0,
    },
  },
  alerts: [],
  hosts: [],
  http: {},
};

function mergeTelemetry(state, payload) {
  const next = { ...state };
  if (payload.agent_status !== undefined) next.agent_status = payload.agent_status;
  if (payload.hostname !== undefined) next.hostname = payload.hostname;
  if (payload.last_updated !== undefined) next.last_updated = payload.last_updated;

  if (payload.hardware !== undefined) {
    next.hardware = {
      ...state.hardware,
      ...payload.hardware,
    };
  }
  if (payload.network !== undefined) {
    next.network = {
      ...state.network,
      ...payload.network,
    };
  }
  if (payload.process !== undefined) {
    next.process = {
      ...state.process,
      ...payload.process,
    };
  }
  if (payload.docker !== undefined) {
    next.docker = {
      ...state.docker,
      ...payload.docker,
    };
  }
  if (payload.http !== undefined) {
    next.http = {
      ...state.http,
      ...payload.http,
    };
  }
  if (payload.alerts !== undefined && Array.isArray(payload.alerts)) {
    next.alerts = payload.alerts;
  }
  if (payload.hosts !== undefined && Array.isArray(payload.hosts)) {
    next.hosts = payload.hosts;
  }
  return next;
}

function normalizeAlert(message) {
  if (!message || typeof message !== 'object') return message;
  return message;
}

function updateHostsState(hosts, payload) {
  if (!payload.hostname) return hosts;
  const existingIndex = hosts.findIndex((item) => item.hostname === payload.hostname);
  const updatedHost = {
    hostname: payload.hostname,
    status: payload.status || 'OFFLINE',
    last_heartbeat: payload.last_heartbeat || null,
    ...payload,
  };

  if (existingIndex >= 0) {
    const nextHosts = [...hosts];
    nextHosts[existingIndex] = {
      ...nextHosts[existingIndex],
      ...updatedHost,
    };
    return nextHosts;
  }

  return [updatedHost, ...hosts];
}

function telemetryReducer(state, action) {
  const payload = action.payload || {};

  switch (action.type) {
    case 'SNAPSHOT': {
      if (!payload || typeof payload !== 'object') return state;
      return mergeTelemetry(state, payload);
    }

    case 'HEARTBEAT_UPDATE': {
      return {
        ...state,
        agent_status: payload.status || state.agent_status,
        hostname: payload.hostname || state.hostname,
        last_updated: payload.last_heartbeat || state.last_updated,
        hosts: updateHostsState(state.hosts, payload),
      };
    }

    case 'HARDWARE_UPDATE': {
      return {
        ...state,
        hardware: {
          ...state.hardware,
          cpu: payload.cpu || state.hardware.cpu,
          ram: payload.ram || state.hardware.ram,
          disk: payload.disk || state.hardware.disk,
        },
        last_updated: payload.timestamp || state.last_updated,
      };
    }

    case 'DOCKER_UPDATE': {
      return {
        ...state,
        docker: {
          ...state.docker,
          containers: payload.containers || state.docker.containers,
          docker_info: {
            ...state.docker.docker_info,
            ...(payload.docker_info || {}),
          },
        },
        last_updated: payload.timestamp || state.last_updated,
      };
    }

    case 'PROCESS_EVENT': {
      return {
        ...state,
        process: payload.process ? { ...state.process, ...payload.process } : state.process,
        alerts: [normalizeAlert(payload), ...state.alerts],
        last_updated: payload.timestamp || state.last_updated,
      };
    }

    case 'NETWORK_EVENT': {
      return {
        ...state,
        network: payload.network ? { ...state.network, ...payload.network } : state.network,
        alerts: [normalizeAlert(payload), ...state.alerts],
        last_updated: payload.timestamp || state.last_updated,
      };
    }

    case 'HTTP_EVENT': {
      return {
        ...state,
        http: payload.http ? { ...state.http, ...payload.http } : state.http,
        alerts: [normalizeAlert(payload), ...state.alerts],
        last_updated: payload.timestamp || state.last_updated,
      };
    }

    default:
      return state;
  }
}

export function useWebSocket(
  wsUrl = WS_URL,
  fallbackPollUrl = API_URL
) {
  const [telemetry, dispatch] = useReducer(telemetryReducer, initialTelemetry);
  const [isConnected, setIsConnected] = useState(false);
  const [mode, setMode] = useState('Connecting...');
  const wsRef = useRef(null);

  useEffect(() => {
    let isMounted = true;
    let pollInterval = null;

    function connectWebSocket() {
      try {
        const token = localStorage.getItem('homeops_access_token');
        const authenticatedWsUrl = token
          ? `${wsUrl}${wsUrl.includes('?') ? '&' : '?'}token=${encodeURIComponent(token)}`
          : wsUrl;

        const ws = new WebSocket(authenticatedWsUrl);
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
            if (!data || typeof data !== 'object') return;

            switch (data.type) {
              case 'STATE_SNAPSHOT':
                dispatch({ type: 'SNAPSHOT', payload: data });
                break;
              case 'HEARTBEAT_UPDATE':
                dispatch({ type: 'HEARTBEAT_UPDATE', payload: data });
                break;
              case 'HARDWARE_UPDATE':
                dispatch({ type: 'HARDWARE_UPDATE', payload: data });
                break;
              case 'DOCKER_UPDATE':
                dispatch({ type: 'DOCKER_UPDATE', payload: data });
                break;
              case 'PROCESS_EVENT':
                dispatch({ type: 'PROCESS_EVENT', payload: data });
                break;
              case 'NETWORK_EVENT':
                dispatch({ type: 'NETWORK_EVENT', payload: data });
                break;
              case 'HTTP_EVENT':
                dispatch({ type: 'HTTP_EVENT', payload: data });
                break;
              default:
                dispatch({ type: 'SNAPSHOT', payload: data });
                break;
            }
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
        const res = await authFetch(fallbackPollUrl);
        if (res.ok) {
          const data = await res.json();
          if (isMounted) {
            dispatch({ type: 'SNAPSHOT', payload: data });
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

  const value = useMemo(
    () => ({ telemetry, isConnected, mode }),
    [telemetry, isConnected, mode]
  );

  return value;
}
