import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { TelemetryProvider } from './context/TelemetryContext';
import { AuthProvider } from './auth/AuthContext';
import './index.css';
import App from './App.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <TelemetryProvider>
          <App />
        </TelemetryProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>
);
