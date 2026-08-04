import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { DashboardPage } from './pages/DashboardPage';
import { InfrastructurePage } from './pages/InfrastructurePage';
import { DockerPage } from './pages/DockerPage';
import { NetworkPage } from './pages/NetworkPage';
import { ProcessesPage } from './pages/ProcessesPage';
import { EventsPage } from './pages/EventsPage';
import { HistoricalMetricsPage } from './pages/HistoricalMetricsPage';
import { HttpMonitorPage } from './pages/HttpMonitorPage';
import { SettingsPage } from './pages/SettingsPage';
import './App.css';

export function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/infrastructure" element={<InfrastructurePage />} />
        <Route path="/docker" element={<DockerPage />} />
        <Route path="/network" element={<NetworkPage />} />
        <Route path="/processes" element={<ProcessesPage />} />
        <Route path="/events" element={<EventsPage />} />
        <Route path="/history" element={<HistoricalMetricsPage />} />
        <Route path="/http-monitor" element={<HttpMonitorPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}

export default App;
