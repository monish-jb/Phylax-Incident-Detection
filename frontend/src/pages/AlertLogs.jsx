import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Bell, ShieldAlert, CheckCircle, Clock, Send, AlertTriangle } from 'lucide-react';

export const AlertLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      const res = await api.get('/alerts/log');
      setLogs(res.data);
      setLoading(false);
    } catch (err) {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px 32px', maxWidth: '1200px', margin: '0 auto' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontFamily: 'var(--font-hud)', color: 'var(--text-main)', margin: '0 0 4px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Bell style={{ color: 'var(--hud-cyan)' }} /> ALERT NOTIFICATION LOGS
          </h2>
          <p style={{ color: 'var(--text-dim)', fontSize: '13px', margin: 0 }}>
            Audit trail of all emergency alert dispatches, channel status, and recipient acknowledgments.
          </p>
        </div>

        <button onClick={fetchLogs} className="cmd-btn cmd-btn-secondary" style={{ padding: '8px 16px', fontSize: '12px' }}>
          REFRESH LOGS
        </button>
      </div>

      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--hud-cyan)' }}>LOADING ALERT LOGS...</div>
      ) : logs.length === 0 ? (
        <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', padding: '40px', borderRadius: '8px', textAlign: 'center', color: 'var(--text-dim)' }}>
          No alert logs recorded yet. When high or critical severity incidents occur, notification logs will appear here.
        </div>
      ) : (
        <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '8px', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ background: 'var(--table-header-bg)', borderBottom: '1px solid var(--border-color)', color: 'var(--hud-cyan)', textAlign: 'left' }}>
                <th style={{ padding: '12px 16px' }}>LOG ID</th>
                <th style={{ padding: '12px 16px' }}>DISPATCH TIME</th>
                <th style={{ padding: '12px 16px' }}>CHANNEL</th>
                <th style={{ padding: '12px 16px' }}>STATUS</th>
                <th style={{ padding: '12px 16px' }}>ACKNOWLEDGMENT</th>
              </tr>
            </thead>
            <tbody>
              {logs.map(log => (
                <tr key={log.id} style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-main)' }}>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)' }}>#{log.id}</td>
                  <td style={{ padding: '12px 16px' }}>{new Date(log.sent_at).toLocaleString()}</td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ padding: '3px 8px', borderRadius: '4px', background: 'rgba(6, 182, 212, 0.1)', color: 'var(--hud-cyan)', fontWeight: 600 }}>
                      {log.channel}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{
                      padding: '3px 8px',
                      borderRadius: '4px',
                      fontWeight: 700,
                      fontSize: '11px',
                      background: log.status === 'ACKNOWLEDGED' ? 'rgba(16, 185, 129, 0.2)' : log.status === 'SENT' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                      color: log.status === 'ACKNOWLEDGED' ? '#10b981' : log.status === 'SENT' ? '#3b82f6' : '#ef4444'
                    }}>
                      {log.status}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    {log.acknowledged_at ? (
                      <span style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <CheckCircle size={14} /> ACKNOWLEDGED AT {new Date(log.acknowledged_at).toLocaleTimeString()}
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Clock size={14} /> PENDING ACKNOWLEDGMENT
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
