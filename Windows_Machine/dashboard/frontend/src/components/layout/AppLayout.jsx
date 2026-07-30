import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { Footer } from './Footer';

export function AppLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const toggleSidebar = () => {
    setSidebarCollapsed((prev) => !prev);
  };

  return (
    <div className="noc-app-shell">
      <Header />

      <div className="noc-body-container">
        <Sidebar collapsed={sidebarCollapsed} onToggle={toggleSidebar} />

        <main className={`noc-main-content ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
          <Outlet />
        </main>
      </div>

      <Footer />
    </div>
  );
}
