import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { TelemetryProvider } from './context/TelemetryContext';
import './index.css';
import App from './App.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <TelemetryProvider>
        <App />
      </TelemetryProvider>
    </BrowserRouter>
  </StrictMode>
);
