import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Monitor, Search, Filter, Trash2, AlertTriangle, ShieldCheck } from 'lucide-react';

export const SurveillanceWall = () => {
  const [videos, setVideos] = useState([]);
  const [search, setSearch] = useState('');
  const [filterAccident, setFilterAccident] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchVideos();
  }, [search, filterAccident]);

  const fetchVideos = async () => {
    try {
      let url = `/videos?search=${encodeURIComponent(search)}`;
      if (filterAccident === 'accident') url += '&has_accident=true';
      if (filterAccident === 'normal') url += '&has_accident=false';

      const res = await api.get(url);
      setVideos(res.data.items || []);
    } catch (err) {
      console.error('Failed to load surveillance wall:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (e, videoId) => {
    e.preventDefault();
    e.stopPropagation();
    if (!window.confirm(`Are you sure you want to purge Surveillance Feed #${videoId}?`)) return;

    try {
      await api.delete(`/videos/${videoId}`);
      fetchVideos();
    } catch (err) {
      alert('Failed to delete video');
    }
  };

  return (
    <div style={{ maxWidth: '1280px', margin: '30px auto', padding: '0 24px' }}>
      
      {/* Header Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontFamily: 'var(--font-hud)', fontSize: '22px', letterSpacing: '2px', color: 'var(--text-main)' }}>
            PHYLAX SURVEILLANCE WALL
          </h1>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-dim)' }}>
            MONITORED CAMERA FEEDS, LOCATION PROFILES & FLAGGED INCIDENTS
          </p>
        </div>

        {/* Filter Controls */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          
          <div style={{ position: 'relative' }}>
            <Search size={14} color="var(--text-dim)" style={{ position: 'absolute', left: '10px', top: '10px' }} />
            <input
              type="text"
              placeholder="SEARCH FEEDS..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                background: 'rgba(0,0,0,0.5)',
                border: '1px solid var(--hud-panel-border)',
                padding: '8px 12px 8px 32px',
                borderRadius: '4px',
                color: '#fff',
                fontFamily: 'var(--font-mono)',
                fontSize: '12px'
              }}
            />
          </div>

          <div style={{ display: 'flex', background: 'rgba(0,0,0,0.4)', borderRadius: '4px', border: '1px solid var(--hud-panel-border)' }}>
            <button
              onClick={() => setFilterAccident('all')}
              style={{ padding: '6px 12px', background: filterAccident === 'all' ? 'var(--hud-cyan)' : 'transparent', color: filterAccident === 'all' ? '#000' : 'var(--text-dim)', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: '11px', fontWeight: 600 }}
            >
              ALL FEEDS
            </button>
            <button
              onClick={() => setFilterAccident('accident')}
              style={{ padding: '6px 12px', background: filterAccident === 'accident' ? 'var(--hud-red)' : 'transparent', color: filterAccident === 'accident' ? '#fff' : 'var(--text-dim)', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: '11px', fontWeight: 600 }}
            >
              INCIDENTS FLAGGED
            </button>
            <button
              onClick={() => setFilterAccident('normal')}
              style={{ padding: '6px 12px', background: filterAccident === 'normal' ? 'var(--hud-green)' : 'transparent', color: filterAccident === 'normal' ? '#000' : 'var(--text-dim)', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: '11px', fontWeight: 600 }}
            >
              CLEAR FEEDS
            </button>
          </div>

        </div>
      </div>

      {/* Surveillance Tiles Grid */}
      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', fontFamily: 'var(--font-mono)', color: 'var(--hud-cyan)' }}>
          LOADING PHYLAX SURVEILLANCE WALL MONITOR TILES...
        </div>
      ) : videos.length === 0 ? (
        <div className="hud-card" style={{ padding: '40px', textAlign: 'center', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
          NO SURVEILLANCE FEEDS MATCHING CURRENT FILTER.
        </div>
      ) : (
        <div className="surveillance-grid">
          {videos.map((video) => (
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

              <div style={{ padding: '12px 16px', background: 'rgba(15, 23, 42, 0.95)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: '#fff', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '200px' }}>
                    {video.original_filename}
                  </div>
                  <button
                    onClick={(e) => handleDelete(e, video.id)}
                    title="Purge Video"
                    style={{ background: 'none', border: 'none', color: 'var(--hud-red)', cursor: 'pointer' }}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                  <span>FPS: {video.fps || 30.0} | {video.duration_sec ? `${video.duration_sec.toFixed(1)}s` : 'Processing'}</span>
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
  );
};
