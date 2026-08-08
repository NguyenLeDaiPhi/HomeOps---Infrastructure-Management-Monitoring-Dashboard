const ORIGIN = `${window.location.protocol}//${window.location.host}`;
const COMMAND_GATEWAY_URL =
  import.meta.env.VITE_DOCKER_API_URL || `${ORIGIN}/api/v1/docker`;

export const AUTH_API_BASE = COMMAND_GATEWAY_URL.replace('/api/v1/docker', '/auth');

let getAccessTokenFn = () => localStorage.getItem('homeops_access_token');
let refreshSessionFn = null;

export function setAuthTokenGetters(tokenGetter, refresher) {
  getAccessTokenFn = tokenGetter;
  refreshSessionFn = refresher;
}

export async function authFetch(url, options = {}) {
  const token = getAccessTokenFn ? getAccessTokenFn() : localStorage.getItem('homeops_access_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response = await fetch(url, { ...options, headers });

  // Handle 401 Unauthorized -> Attempt token refresh
  if (response.status === 401 && refreshSessionFn && !options._retry) {
    options._retry = true;
    const refreshed = await refreshSessionFn();
    if (refreshed) {
      const newToken = getAccessTokenFn();
      headers['Authorization'] = `Bearer ${newToken}`;
      response = await fetch(url, { ...options, headers });
    } else {
      // Refresh failed -> clear session and redirect to login
      localStorage.removeItem('homeops_access_token');
      localStorage.removeItem('homeops_refresh_token');
      localStorage.removeItem('homeops_user');
      window.location.href = '/login';
    }
  }

  return response;
}
