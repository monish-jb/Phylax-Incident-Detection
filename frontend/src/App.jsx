import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { HeaderNavbar } from './components/HeaderNavbar';
import { Login } from './pages/Login';
import { OnboardingWizard } from './pages/OnboardingWizard';
import { Dashboard } from './pages/Dashboard';
import { Upload } from './pages/Upload';
import { SurveillanceWall } from './pages/SurveillanceWall';
import { VideoDetail } from './pages/VideoDetail';
import { AlertLogs } from './pages/AlertLogs';
import { Settings } from './pages/Settings';
import './assets/control_room.css';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--font-hud)', color: 'var(--hud-cyan)' }}>
        AUTHENTICATING PHYLAX CREDENTIALS...
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;

  // Enforce mandatory onboarding guard if not completed
  if (!user.onboarding_completed && location.pathname !== '/onboarding') {
    return <Navigate to="/onboarding" replace />;
  }

  return children;
};

function AppRoutes() {
  const { user } = useAuth();

  return (
    <>
      <HeaderNavbar />
      <Routes>
        <Route path="/login" element={user ? <Navigate to={user.onboarding_completed ? "/dashboard" : "/onboarding"} replace /> : <Login />} />
        
        <Route path="/onboarding" element={<ProtectedRoute><OnboardingWizard /></ProtectedRoute>} />
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/upload" element={<ProtectedRoute><Upload /></ProtectedRoute>} />
        <Route path="/history" element={<ProtectedRoute><SurveillanceWall /></ProtectedRoute>} />
        <Route path="/videos/:id" element={<ProtectedRoute><VideoDetail /></ProtectedRoute>} />
        <Route path="/alerts" element={<ProtectedRoute><AlertLogs /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
        
        <Route path="/" element={<Navigate to={user ? (user.onboarding_completed ? "/dashboard" : "/onboarding") : "/login"} replace />} />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <AppRoutes />
      </Router>
    </AuthProvider>
  );
}
