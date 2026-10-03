import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Video, AlertTriangle, ShieldCheck, Cpu, ArrowUpRight, Activity, Flame, ShieldAlert, Users, Eye, Lock } from 'lucide-react';

export const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [recentVideos, setRecentVideos] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, videosRes, contactsRes] = await Promise.all([
        api.get('/dashboard/stats'),
        api.get('/videos?page_size=6'),
        api.get('/contacts')
      ]);
      setStats(statsRes.data);
      setRecentVideos(videosRes.data.items || []);
      setContacts(contactsRes.data || []);
    } catch (err) {
      console.error('Failed to load dashboard stats:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', fontFamily: 'var(--font-mono)', color: 'var(--hud-cyan)' }}>
        INITIALIZING PHYLAX COMMAND DASHBOARD...
      </div>
    );
  }

  const verifiedContacts = contacts.filter(c => c.verified);

  return (
    <div style={{ maxWidth: '1280px', margin: '30px auto', padding: '0 24px' }}>
      
      {/* Top Banner Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontFamily: 'var(--font-hud)', fontSize: '24px', letterSpacing: '2px', color: 'var(--text-main)' }}>
            PHYLAX SURVEILLANCE DASHBOARD
          </h1>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-dim)' }}>
            GENERAL-PURPOSE AI CAMERA SURVEILLANCE & EMERGENCY DISPATCH CONTROL
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <Link to="/settings" className="cmd-btn cmd-btn-secondary" style={{ padding: '8px 14px', fontSize: '12px' }}>
            <Users size={14} /> CONTACTS ({verifiedContacts.length} VERIFIED)
          </Link>
          <Link to="/upload" className="cmd-btn cmd-btn-primary">
            <ArrowUpRight size={16} /> ADD CAMERA / FEED
          </Link>
        </div>
      </div>

      {/* Emergency Contact Status Bar */}
      <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid #10b981', padding: '12px 18px', borderRadius: '8px', marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <ShieldCheck size={20} color="#10b981" />
          <span style={{ fontSize: '13px', color: '#10b981', fontWeight: 600 }}>
            EMERGENCY DISPATCH READY: {verifiedContacts.length} verified emergency contact(s) active on SMS / WhatsApp / Email.
          </span>
        </div>
        <Link to="/settings" style={{ color: '#10b981', fontSize: '12px', fontWeight: 700, textDecoration: 'underline' }}>
          Manage Contacts &rarr;
        </Link>
      </div>

      {/* Per-Detector Stats Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '28px' }}>
        
        <div className="hud-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-dim)' }}>FEEDS ANALYZED</span>
            <Video size={18} color="var(--hud-cyan)" />
          </div>
          <div style={{ fontFamily: 'var(--font-hud)', fontSize: '28px', color: 'var(--hud-cyan)' }}>
            {stats?.total_videos || 0}
          </div>
        </div>

        <div className="hud-card hud-card-red">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--hud-red)' }}>ACCIDENT / COLLISION</span>
            <AlertTriangle size={18} color="var(--hud-red)" />
          </div>
          <div style={{ fontFamily: 'var(--font-hud)', fontSize: '28px', color: 'var(--hud-red)' }}>
            {stats?.incidents_by_type?.ACCIDENT || 0}
          </div>
        </div>

        <div className="hud-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--hud-amber)' }}>THEFT / SHOPLIFTING</span>
            <ShieldAlert size={18} color="var(--hud-amber)" />
          </div>
          <div style={{ fontFamily: 'var(--font-hud)', fontSize: '28px', color: 'var(--hud-amber)' }}>
            {stats?.incidents_by_type?.THEFT || 0}
          </div>
        </div>

        <div className="hud-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#a855f7' }}>INTRUSION / BREACH</span>
            <Lock size={18} color="#a855f7" />
          </div>
          <div style={{ fontFamily: 'var(--font-hud)', fontSize: '28px', color: '#a855f7' }}>
            {stats?.incidents_by_type?.INTRUSION || 0}
          </div>
        </div>

        <div className="hud-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#ef4444' }}>FIRE & SMOKE</span>
            <Flame size={18} color="#ef4444" />
          </div>
          <div style={{ fontFamily: 'var(--font-hud)', fontSize: '28px', color: '#ef4444' }}>
            {stats?.incidents_by_type?.FIRE || 0}
          </div>
        </div>

      </div>

      {/* Recent Surveillance Wall Grid */}
      <div className="hud-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '16px', letterSpacing: '1px' }}>
            ACTIVE PHYLAX MONITORED FEEDS
          </h3>
          <Link to="/history" style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--hud-cyan)' }}>
            VIEW FULL SURVEILLANCE WALL &rarr;
          </Link>
        </div>

        {recentVideos.length === 0 ? (
          <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
            NO SURVEILLANCE FEEDS ADDED YET. CLICK "ADD CAMERA / FEED" TO INGEST FOOTAGE.
          </div>
        ) : (
          <div className="surveillance-grid" style={{ marginTop: 0 }}>
            {recentVideos.map((video) => (
              <div key={video.id} className={`surveillance-tile ${video.has_accident ? 'alert-tile' : ''}`}>
                <div className="surveillance-header-overlay">
                  <span className="rec-badge">
                    <span className={`led-indicator ${video.has_accident ? 'led-red' : 'led-green'}`}></span>
                    {video.profile || 'ROAD_PARKING'}
                  </span>
                  <span className="cam-name-badge">FEED-{video.id.toString().padStart(3, '0')}</span>
                </div>

                <Link to={`/videos/${video.id}`}>
                  <img
                    src={video.poster_path ? `/${video.poster_path}` : 'https://images.unsplash.com/photo-1506521781263-d8422e82f27a?w=600'}
                    alt={video.original_filename}
                    className="surveillance-poster"
                  />
                </Link>

                <div style={{ padding: '12px 16px', background: 'rgba(15, 23, 42, 0.9)' }}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: '#fff', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {video.original_filename}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '11px', color: 'var(--text-dim)' }}>
                    <span>{video.duration_sec ? `${video.duration_sec.toFixed(1)}s` : 'Processing'}</span>
                    <span style={{ color: video.has_accident ? 'var(--hud-red)' : 'var(--hud-green)', fontWeight: 'bold' }}>
                      {video.max_score} FLAGGED EVENTS
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
};
