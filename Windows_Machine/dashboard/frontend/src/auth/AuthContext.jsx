import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { AUTH_API_BASE, setAuthTokenGetters } from './api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('homeops_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [accessToken, setAccessToken] = useState(
    () => localStorage.getItem('homeops_access_token') || null
  );

  const [refreshToken, setRefreshToken] = useState(
    () => localStorage.getItem('homeops_refresh_token') || null
  );

  const [loading, setLoading] = useState(true);

  // Save session state to localStorage
  const saveSession = (access, refresh, userData) => {
    setAccessToken(access);
    setRefreshToken(refresh);
    setUser(userData);

    if (access) localStorage.setItem('homeops_access_token', access);
    else localStorage.removeItem('homeops_access_token');

    if (refresh) localStorage.setItem('homeops_refresh_token', refresh);
    else localStorage.removeItem('homeops_refresh_token');

    if (userData) localStorage.setItem('homeops_user', JSON.stringify(userData));
    else localStorage.removeItem('homeops_user');
  };

  const clearSession = useCallback(() => {
    saveSession(null, null, null);
  }, []);

  // Refresh token session handler
  const refreshSession = useCallback(async () => {
    const rToken = localStorage.getItem('homeops_refresh_token');
    if (!rToken) {
      clearSession();
      return false;
    }

    try {
      const res = await fetch(`${AUTH_API_BASE}/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: rToken }),
      });

      if (res.ok) {
        const data = await res.json();
        saveSession(data.access_token, data.refresh_token, data.user);
        return true;
      } else {
        clearSession();
        return false;
      }
    } catch (err) {
      console.error('Session refresh error:', err);
      clearSession();
      return false;
    }
  }, [clearSession]);

  // Connect api.js auth getters
  useEffect(() => {
    setAuthTokenGetters(
      () => localStorage.getItem('homeops_access_token'),
      refreshSession
    );
  }, [refreshSession]);

  // Login handler
  const login = async (username, password) => {
    try {
      const res = await fetch(`${AUTH_API_BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        return {
          success: false,
          message: data.detail || 'Invalid username or password.',
        };
      }

      saveSession(data.access_token, data.refresh_token, data.user);
      return { success: true, user: data.user };
    } catch (err) {
      return {
        success: false,
        message: `Network error during login: ${err.message}`,
      };
    }
  };

  // Logout handler
  const logout = async () => {
    const rToken = refreshToken || localStorage.getItem('homeops_refresh_token');
    const aToken = accessToken || localStorage.getItem('homeops_access_token');
    if (rToken) {
      try {
        await fetch(`${AUTH_API_BASE}/logout`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: aToken ? `Bearer ${aToken}` : '',
          },
          body: JSON.stringify({ refresh_token: rToken }),
        });
      } catch (err) {
        console.error('Logout error:', err);
      }
    }
    clearSession();
  };

  // Check initial authentication on mount
  useEffect(() => {
    const initAuth = async () => {
      const storedAccess = localStorage.getItem('homeops_access_token');
      const storedRefresh = localStorage.getItem('homeops_refresh_token');

      if (storedAccess && storedRefresh) {
        // Verify current session with /auth/me
        try {
          const res = await fetch(`${AUTH_API_BASE}/me`, {
            headers: { Authorization: `Bearer ${storedAccess}` },
          });
          if (res.ok) {
            const userData = await res.json();
            setUser(userData);
            localStorage.setItem('homeops_user', JSON.stringify(userData));
          } else {
            // Attempt session refresh if /me failed
            await refreshSession();
          }
        } catch {
          await refreshSession();
        }
      } else {
        clearSession();
      }
      setLoading(false);
    };

    initAuth();
  }, [clearSession, refreshSession]);

  // Automatic token refresh every 14 minutes (14 * 60 * 1000 ms)
  useEffect(() => {
    if (!accessToken || !refreshToken) return;
    const interval = setInterval(() => {
      refreshSession();
    }, 14 * 60 * 1000);
    return () => clearInterval(interval);
  }, [accessToken, refreshToken, refreshSession]);

  const value = {
    user,
    role: user?.role || null,
    accessToken,
    refreshToken,
    isAuthenticated: !!user && !!accessToken,
    loading,
    login,
    logout,
    refreshSession,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
