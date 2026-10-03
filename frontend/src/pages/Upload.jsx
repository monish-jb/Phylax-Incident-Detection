import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { RadarSweep } from '../components/RadarSweep';
import { UploadCloud, FileVideo, CheckCircle2, AlertCircle, Shield, Settings } from 'lucide-react';

const LOCATION_PROFILES = [
  { id: 'HOME', label: 'Home / Residential', detectors: ['Intrusion', 'Fall', 'Fire/Smoke', 'Loitering'] },
  { id: 'SHOP_RETAIL', label: 'Shop / Retail Store', detectors: ['Theft', 'Loitering', 'Intrusion', 'Crowd Density', 'Fire/Smoke'] },
  { id: 'MALL', label: 'Shopping Mall', detectors: ['Crowd Density', 'Abandoned Object', 'Theft', 'Fight', 'Fire/Smoke'] },
  { id: 'CINEMA_THEATRE', label: 'Cinema / Theatre', detectors: ['Crowd Density', 'Abandoned Object', 'Fight', 'Fire/Smoke', 'Fall'] },
  { id: 'OFFICE_WAREHOUSE', label: 'Office / Warehouse', detectors: ['Intrusion', 'After-Hours', 'Fire/Smoke', 'Fall'] },
  { id: 'ROAD_PARKING', label: 'Road / Parking Lot', detectors: ['Accident', 'Loitering', 'Fire/Smoke'] },
];

export const Upload = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [profile, setProfile] = useState('ROAD_PARKING');
  const [cameraName, setCameraName] = useState('Camera Feed #1');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleFileChange = (file) => {
    if (!file) return;
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['mp4', 'avi', 'mov', 'mkv'].includes(ext)) {
      setError('Invalid file format. Allowed formats: .MP4, .AVI, .MOV, .MKV');
      return;
    }

    if (file.size > 200 * 1024 * 1024) {
      setError('File exceeds max size limit of 200MB.');
      return;
    }

    setError('');
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);
    setError('');
    setProgress(15);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const timer = setInterval(() => {
        setProgress((prev) => (prev >= 85 ? prev : prev + 10));
      }, 500);

      const res = await api.post('/videos/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      clearInterval(timer);
      setProgress(100);

      setTimeout(() => {
        navigate(`/videos/${res.data.id}`);
      }, 800);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload video');
      setUploading(false);
    }
  };

  return (
    <div style={{ maxWidth: '840px', margin: '30px auto', padding: '0 24px' }}>
      <div className="hud-card">
        
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <h2 style={{ fontFamily: 'var(--font-hud)', fontSize: '20px', letterSpacing: '2px', color: 'var(--hud-cyan)' }}>
            PHYLAX SURVEILLANCE FEED INGESTION
          </h2>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-dim)', marginTop: '4px' }}>
            SUBMIT CAMERA FOOTAGE FOR MULTI-DETECTOR AI INCIDENT ANALYSIS
          </p>
        </div>

        {error && (
          <div style={{ background: 'rgba(239, 68, 68, 0.2)', border: '1px solid var(--hud-red)', padding: '12px', borderRadius: '4px', color: '#fff', fontSize: '13px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={16} color="var(--hud-red)" /> {error}
          </div>
        )}

        {uploading ? (
          <RadarSweep progress={progress} statusText="RUNNING PHYLAX SHARED YOLO & MULTI-DETECTOR PIPELINE..." />
        ) : (
          <form onSubmit={handleUploadSubmit}>
            
            {/* Configuration Options */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
              <div>
                <label className="cmd-label">Location Surveillance Profile</label>
                <select
                  className="cmd-input"
                  value={profile}
                  onChange={(e) => setProfile(e.target.value)}
                >
                  {LOCATION_PROFILES.map(p => (
                    <option key={p.id} value={p.id}>{p.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="cmd-label">Camera / Feed Label</label>
                <input
                  type="text"
                  className="cmd-input"
                  value={cameraName}
                  onChange={(e) => setCameraName(e.target.value)}
                  placeholder="e.g. Front Door, Cash Counter, Screen 2"
                />
              </div>
            </div>

            {/* Active Detectors Display */}
            <div style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', padding: '12px 16px', borderRadius: '6px', marginBottom: '20px' }}>
              <div style={{ fontSize: '11px', color: 'var(--hud-cyan)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Shield size={14} /> Auto-Enabled AI Detectors for {profile}:
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {(LOCATION_PROFILES.find(p => p.id === profile)?.detectors || []).map(d => (
                  <span key={d} style={{ background: 'rgba(6, 182, 212, 0.15)', color: 'var(--hud-cyan)', padding: '4px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: 600 }}>
                    ✓ {d}
                  </span>
                ))}
              </div>
            </div>

            {/* File Dropzone */}
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => document.getElementById('feedFileInput').click()}
              style={{
                border: '2px dashed var(--hud-panel-border)',
                borderRadius: '8px',
                padding: '36px',
                textAlign: 'center',
                background: 'rgba(0,0,0,0.4)',
                cursor: 'pointer',
                marginBottom: '20px',
                transition: 'all 0.2s'
              }}
            >
              <UploadCloud size={44} color="var(--hud-cyan)" style={{ marginBottom: '10px' }} />
              <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '15px', marginBottom: '6px' }}>
                DRAG & DROP SURVEILLANCE VIDEO FILE HERE
              </h3>
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-dim)' }}>
                Supports .MP4, .AVI, .MOV, .MKV (Max limit: 200MB)
              </p>
              <input
                type="file"
                id="feedFileInput"
                accept="video/mp4,video/avi,video/mov,video/mkv"
                style={{ display: 'none' }}
                onChange={(e) => handleFileChange(e.target.files[0])}
              />
            </div>

            {selectedFile && (
              <div style={{ background: 'rgba(6, 182, 212, 0.1)', border: '1px solid var(--hud-cyan)', padding: '16px', borderRadius: '6px', marginBottom: '20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                  <FileVideo size={20} color="var(--hud-cyan)" />
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', fontWeight: 'bold' }}>
                    {selectedFile.name} ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
                  </span>
                </div>
                {previewUrl && (
                  <video src={previewUrl} controls style={{ width: '100%', maxHeight: '240px', borderRadius: '4px', background: '#000' }} />
                )}
              </div>
            )}

            <button
              type="submit"
              disabled={!selectedFile}
              className="cmd-btn cmd-btn-primary"
              style={{ width: '100%', justifyContent: 'center', opacity: selectedFile ? 1 : 0.5, padding: '12px', fontSize: '13px' }}
            >
              <CheckCircle2 size={16} /> START PHYLAX AI DETECTION PROCESS
            </button>
          </form>
        )}

      </div>
    </div>
  );
};
