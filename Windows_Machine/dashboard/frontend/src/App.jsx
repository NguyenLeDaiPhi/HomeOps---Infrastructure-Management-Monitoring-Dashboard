import React from 'react';
import { Navigate, Routes, Route } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { DashboardPage } from './pages/DashboardPage';
import { InfrastructurePage } from './pages/InfrastructurePage';
import { DockerPage } from './pages/DockerPage';
import { NetworkPage } from './pages/NetworkPage';
import { ProcessesPage } from './pages/ProcessesPage';
import { EventsPage } from './pages/EventsPage';
import { HistoricalMetricsPage } from './pages/HistoricalMetricsPage';
import { HttpMonitorPage } from './pages/HttpMonitorPage';
import { SettingsPage } from './pages/SettingsPage';
import { UserManagementPage } from './pages/UserManagementPage';
import { LoginPage } from './pages/LoginPage';
import './App.css';

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Navigate to="/dashboard" replace />
          </ProtectedRoute>
        }
      />
      <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/infrastructure" element={<InfrastructurePage />} />
        <Route path="/docker" element={<ProtectedRoute allowedRoles={['admin', 'operator']}><DockerPage /></ProtectedRoute>} />
        <Route path="/network" element={<NetworkPage />} />
        <Route path="/processes" element={<ProcessesPage />} />
        <Route path="/events" element={<EventsPage />} />
        <Route path="/history" element={<HistoricalMetricsPage />} />
        <Route path="/http-monitor" element={<HttpMonitorPage />} />
        <Route path="/settings" element={<ProtectedRoute allowedRoles={['admin']}><SettingsPage /></ProtectedRoute>} />
        <Route path="/users" element={<ProtectedRoute allowedRoles={['admin']}><UserManagementPage /></ProtectedRoute>} />
      </Route>
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default App;
