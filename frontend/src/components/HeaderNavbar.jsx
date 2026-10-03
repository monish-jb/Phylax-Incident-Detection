import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, LayoutDashboard, Monitor, UploadCloud, Bell, Settings, LogOut, Users } from 'lucide-react';

export const HeaderNavbar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();

  if (!user) return null;

  return (
    <header className="cmd-navbar">
      <div className="cmd-logo">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Shield size={22} style={{ color: 'var(--hud-cyan)' }} />
          <div>
            <div className="cmd-title" style={{ letterSpacing: '1px', fontWeight: 800, fontSize: '16px' }}>
              PHYLAX <span style={{ color: 'var(--hud-cyan)', fontSize: '11px', fontWeight: 600 }}>AI PLATFORM</span>
            </div>
            <div style={{ fontSize: '9px', color: 'var(--text-dim)', letterSpacing: '0.5px' }}>
              Detect. Alert. Protect.
            </div>
          </div>
        </div>
      </div>

      {user.onboarding_completed && (
        <nav className="cmd-nav-links">
          <Link to="/dashboard" className={`cmd-nav-item ${location.pathname === '/dashboard' ? 'active' : ''}`}>
            <LayoutDashboard size={15} /> Dashboard
          </Link>
          <Link to="/upload" className={`cmd-nav-item ${location.pathname === '/upload' ? 'active' : ''}`}>
            <UploadCloud size={15} /> Add Source
          </Link>
          <Link to="/history" className={`cmd-nav-item ${location.pathname === '/history' ? 'active' : ''}`}>
            <Monitor size={15} /> Surveillance Wall
          </Link>
          <Link to="/alerts" className={`cmd-nav-item ${location.pathname === '/alerts' ? 'active' : ''}`}>
            <Bell size={15} /> Alert Logs
          </Link>
          <Link to="/settings" className={`cmd-nav-item ${location.pathname === '/settings' ? 'active' : ''}`}>
            <Settings size={15} /> Settings
          </Link>
        </nav>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--hud-cyan)', fontWeight: 600 }}>
            <span className="led-indicator led-green" style={{ marginRight: '6px' }}></span>
            {user.full_name || user.username}
          </div>
          <div style={{ fontSize: '9px', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
            LOCATION: {user.location_type || 'HOME'}
          </div>
        </div>

        <button onClick={logout} className="cmd-btn cmd-btn-secondary" style={{ padding: '6px 12px', fontSize: '11px' }}>
          <LogOut size={13} /> LOGOUT
        </button>
      </div>
    </header>
  );
};
