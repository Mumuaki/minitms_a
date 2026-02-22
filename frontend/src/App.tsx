import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from './features/auth/pages/LoginPage';
import { MainLayout } from './components/layout/MainLayout';
import { UsersPage } from './features/users/pages/UsersPage';
import { LoadsPage } from './features/loads/LoadsPage';
import { DashboardPage } from './features/dashboard/pages/DashboardPage';
import { FleetPage } from './features/fleet/pages/FleetPage';
import { FinancePage } from './features/finance/pages/FinancePage';
import { ReportsPage } from './features/reports/pages/ReportsPage';
import { SettingsPage } from './features/settings/pages/SettingsPage';
import { GpsPage } from './features/gps/pages/GpsPage';
import './index.css';
import { useEffect, useState } from 'react';

import { ThemeProvider } from './contexts/ThemeContext';

// Защищенный маршрут: рендерит children внутри MainLayout только если авторизован
const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const isAuthenticated = !!localStorage.getItem('access_token');
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return (
    <MainLayout>
      {children}
    </MainLayout>
  );
};

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!localStorage.getItem('access_token'));

  useEffect(() => {
    const checkAuth = () => {
      setIsAuthenticated(!!localStorage.getItem('access_token'));
    };
    window.addEventListener('storage', checkAuth);
    return () => window.removeEventListener('storage', checkAuth);
  }, []);

  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={
            isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />
          } />
          
          <Route path="/" element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          } />

          <Route path="/users" element={
            <ProtectedRoute>
              <UsersPage />
            </ProtectedRoute>
          } />

          <Route path="/loads" element={
            <ProtectedRoute>
              <LoadsPage />
            </ProtectedRoute>
          } />

          <Route path="/fleet" element={
            <ProtectedRoute>
              <FleetPage />
            </ProtectedRoute>
          } />

          <Route path="/gps" element={
            <ProtectedRoute>
              <GpsPage />
            </ProtectedRoute>
          } />

          <Route path="/finance" element={
            <ProtectedRoute>
              <FinancePage />
            </ProtectedRoute>
          } />

          <Route path="/reports" element={
            <ProtectedRoute>
              <ReportsPage />
            </ProtectedRoute>
          } />

          <Route path="/settings" element={
            <ProtectedRoute>
              <SettingsPage />
            </ProtectedRoute>
          } />

          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
