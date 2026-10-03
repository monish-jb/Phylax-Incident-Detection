import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import { IncidentScrubber } from '../components/IncidentScrubber';
import { AlertTriangle, Download, ArrowLeft, Eye, ShieldAlert, CheckCircle, XCircle, FileText } from 'lucide-react';

export const VideoDetail = () => {
  const { id } = useParams();
  const [video, setVideo] = useState(null);
  const [showAnnotated, setShowAnnotated] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [loading, setLoading] = useState(true);
  const videoRef = useRef(null);

  useEffect(() => {
    fetchVideoDetail();
  }, [id]);

  const fetchVideoDetail = async () => {
    try {
      const res = await api.get(`/videos/${id}`);
      setVideo(res.data);
    } catch (err) {
      console.error('Failed to fetch video detail:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleReviewIncident = async (incidentId, newStatus) => {
    try {
      await api.post(`/incidents/${incidentId}/review`, { status: newStatus });
      fetchVideoDetail(); // Refresh incidents
    } catch (err) {
      alert('Failed to update incident review status');
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleSeek = (targetTimeSec) => {
    if (videoRef.current) {
      videoRef.current.currentTime = targetTimeSec;
      videoRef.current.play();
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', fontFamily: 'var(--font-mono)', color: 'var(--hud-cyan)' }}>
        LOADING PHYLAX SURVEILLANCE FEED ANALYSIS...
      </div>
    );
  }

  if (!video) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: 'var(--hud-red)' }}>
        SURVEILLANCE FEED RECORD NOT FOUND OR ACCESS DENIED.
      </div>
    );
  }

  const streamUrl = showAnnotated && video.analysis_job?.annotated_video_path
    ? `/api/videos/${video.id}/stream-annotated`
    : `/api/videos/${video.id}/stream`;

  return (
    <div style={{ maxWidth: '1280px', margin: '30px auto', padding: '0 24px' }}>
      
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <Link to="/history" className="cmd-btn cmd-btn-secondary" style={{ padding: '6px 14px', fontSize: '11px' }}>
          <ArrowLeft size={14} /> BACK TO SURVEILLANCE WALL
        </Link>

        <div style={{ display: 'flex', gap: '10px' }}>
          <a
            href={`/api/reports/video/${video.id}/json`}
            target="_blank"
            rel="noreferrer"
            className="cmd-btn cmd-btn-secondary"
            style={{ fontSize: '11px' }}
          >
            <Download size={13} /> EXPORT JSON REPORT
          </a>
          <a
            href={`/api/reports/video/${video.id}/pdf`}
            target="_blank"
            rel="noreferrer"
            className="cmd-btn cmd-btn-primary"
            style={{ fontSize: '11px' }}
          >
            <FileText size={13} /> EXPORT PDF/HTML REPORT
          </a>
        </div>
      </div>

      {/* Incident Alert Banner */}
      {video.incidents && video.incidents.length > 0 && (
        <div className="glitch-alert-banner" style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '20px' }}>
          <AlertTriangle size={28} color="var(--hud-red)" />
          <div>
            <div style={{ fontWeight: 'bold' }}>
              PHYLAX INCIDENT AUDIT // {video.incidents.length} EVENTS FLAGGED FOR HUMAN REVIEW
            </div>
            <div style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: '#ffd1d1' }}>
              PROFILE: {video.profile || 'ROAD_PARKING'} | ALL FLAGGED EVENTS REQUIRE OPERATOR REVIEW.
            </div>
          </div>
        </div>
      )}

      {/* Main Player Card */}
      <div className="hud-card" style={{ marginBottom: '24px' }}>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 style={{ fontFamily: 'var(--font-hud)', fontSize: '18px', margin: 0 }}>
              {video.original_filename}
            </h2>
            <span style={{ fontSize: '11px', color: 'var(--hud-cyan)', fontFamily: 'var(--font-mono)' }}>
              PROFILE: {video.profile || 'HOME'} | FEED ID: #{video.id}
            </span>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={() => setShowAnnotated(!showAnnotated)}
              className={`cmd-btn ${showAnnotated ? 'cmd-btn-primary' : 'cmd-btn-secondary'}`}
              style={{ fontSize: '11px' }}
            >
              <Eye size={14} /> {showAnnotated ? 'VIEWING ANNOTATED FEED' : 'VIEWING RAW FEED'}
            </button>
          </div>
        </div>

        {/* Video Player */}
        <div style={{ background: '#000', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--hud-panel-border)' }}>
          <video
            ref={videoRef}
            key={streamUrl}
            src={streamUrl}
            controls
            onTimeUpdate={handleTimeUpdate}
            style={{ width: '100%', maxHeight: '500px', display: 'block' }}
          />
        </div>

        {/* Interactive Scrubber */}
        <IncidentScrubber
          duration={video.duration_sec || 1}
          currentTime={currentTime}
          incidents={video.incidents || []}
          onSeek={handleSeek}
        />

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '16px' }}>
          {video.analysis_job?.annotated_video_path && (
            <a
              href={`/${video.analysis_job.annotated_video_path}`}
              download
              className="cmd-btn cmd-btn-secondary"
              style={{ fontSize: '11px' }}
            >
              <Download size={14} /> DOWNLOAD ANNOTATED MP4
            </a>
          )}
        </div>

      </div>

      {/* Incidents Keyframes & Human Review Workflow */}
      <div className="hud-card">
        <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '16px', marginBottom: '16px', letterSpacing: '1px' }}>
          FLAGGED INCIDENTS REVIEW WORKFLOW ({video.incidents?.length || 0})
        </h3>

        {(!video.incidents || video.incidents.length === 0) ? (
          <div style={{ padding: '20px', textAlign: 'center', color: 'var(--hud-green)', fontFamily: 'var(--font-mono)' }}>
            ✓ ALL CLEAR: NO INCIDENTS FLAGGED IN THIS FOOTAGE.
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
            {video.incidents.map((inc) => (
              <div
                key={inc.id}
                style={{
                  background: 'rgba(0,0,0,0.5)',
                  border: inc.reviewed_status === 'CONFIRMED' ? '1px solid #10b981' : inc.reviewed_status === 'FALSE_ALARM' ? '1px solid #64748b' : '1px solid var(--hud-red)',
                  borderRadius: '6px',
                  overflow: 'hidden'
                }}
              >
                <img
                  src={inc.keyframe_thumbnail_path ? `/${inc.keyframe_thumbnail_path}` : 'https://images.unsplash.com/photo-1506521781263-d8422e82f27a?w=400'}
                  alt={`Incident ${inc.id}`}
                  onClick={() => handleSeek(inc.timestamp_sec)}
                  style={{ width: '100%', height: '150px', objectFit: 'cover', cursor: 'pointer' }}
                />
                <div style={{ padding: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ color: 'var(--hud-cyan)', fontWeight: 'bold', fontSize: '13px' }}>
                      {inc.type}
                    </span>
                    <span style={{
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '10px',
                      fontWeight: 700,
                      background: inc.reviewed_status === 'CONFIRMED' ? '#10b981' : inc.reviewed_status === 'FALSE_ALARM' ? '#64748b' : '#ef4444',
                      color: '#fff'
                    }}>
                      {inc.reviewed_status || 'FLAGGED FOR REVIEW'}
                    </span>
                  </div>

                  <div style={{ fontSize: '11px', color: 'var(--text-dim)', margin: '8px 0', fontFamily: 'var(--font-mono)' }}>
                    TIMESTAMP: {inc.timestamp_sec.toFixed(2)}s | SEVERITY: {inc.severity}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-main)', marginBottom: '12px' }}>
                    {inc.description || 'Flagged for operator review.'}
                  </div>

                  {/* Review Buttons */}
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      onClick={() => handleReviewIncident(inc.id, 'CONFIRMED')}
                      className="cmd-btn"
                      style={{
                        flex: 1,
                        padding: '6px',
                        fontSize: '10px',
                        background: inc.reviewed_status === 'CONFIRMED' ? '#10b981' : 'rgba(16, 185, 129, 0.2)',
                        color: '#fff',
                        border: '1px solid #10b981'
                      }}
                    >
                      <CheckCircle size={12} /> CONFIRM
                    </button>
                    <button
                      onClick={() => handleReviewIncident(inc.id, 'FALSE_ALARM')}
                      className="cmd-btn"
                      style={{
                        flex: 1,
                        padding: '6px',
                        fontSize: '10px',
                        background: inc.reviewed_status === 'FALSE_ALARM' ? '#64748b' : 'rgba(100, 116, 139, 0.2)',
                        color: '#fff',
                        border: '1px solid #64748b'
                      }}
                    >
                      <XCircle size={12} /> FALSE ALARM
                    </button>
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
