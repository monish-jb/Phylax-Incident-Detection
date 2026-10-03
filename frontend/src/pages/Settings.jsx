import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Settings as SettingsIcon, ShieldCheck, Users, PhoneCall, Plus, Trash2, Send, CheckCircle, AlertTriangle } from 'lucide-react';

export const Settings = () => {
  const { user, checkAuth } = useAuth();
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState('');
  const [error, setError] = useState('');

  // Add Contact Form State
  const [showAddForm, setShowAddForm] = useState(false);
  const [fullName, setFullName] = useState('');
  const [relationship, setRelationship] = useState('Family');
  const [phone, setPhone] = useState('');
  const [whatsapp, setWhatsapp] = useState('');
  const [email, setEmail] = useState('');
  const [channels, setChannels] = useState(['SMS']);

  useEffect(() => {
    fetchContacts();
  }, []);

  const fetchContacts = async () => {
    try {
      const res = await api.get('/contacts');
      setContacts(res.data);
      setLoading(false);
    } catch (err) {
      setLoading(false);
    }
  };

  const handleChannelToggle = (ch) => {
    if (channels.includes(ch)) {
      if (channels.length === 1) return;
      setChannels(channels.filter(c => c !== ch));
    } else {
      setChannels([...channels, ch]);
    }
  };

  const handleAddContact = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.post('/contacts', {
        full_name: fullName,
        relationship,
        phone,
        whatsapp: whatsapp || phone,
        email: email || undefined,
        channels
      });
      setMsg('Emergency contact added successfully.');
      setShowAddForm(false);
      setFullName('');
      setPhone('');
      setWhatsapp('');
      setEmail('');
      fetchContacts();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add emergency contact');
    }
  };

  const handleDeleteContact = async (id) => {
    if (contacts.length <= 1) {
      alert('Cannot delete the only emergency contact! At least 1 contact must exist.');
      return;
    }

    if (!window.confirm('Are you sure you want to delete this emergency contact?')) return;

    try {
      await api.delete(`/contacts/${id}`);
      fetchContacts();
      checkAuth();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete contact');
    }
  };

  const handleTestAlert = async (id) => {
    try {
      await api.post(`/contacts/${id}/test-alert`);
      alert('Test alert dispatched to contact!');
    } catch (err) {
      alert('Failed to send test alert');
    }
  };

  return (
    <div style={{ maxWidth: '960px', margin: '30px auto', padding: '0 24px' }}>
      
      {/* Account Info */}
      <div className="hud-card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <SettingsIcon size={22} color="var(--hud-cyan)" />
          <div>
            <h2 style={{ fontFamily: 'var(--font-hud)', fontSize: '18px', margin: 0 }}>
              ACCOUNT & MONITORED PROFILE
            </h2>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-dim)', margin: 0 }}>
              OFFICER CREDENTIALS & LOCATION CONFIGURATION
            </p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', fontSize: '13px' }}>
          <div>
            <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '11px' }}>NAME</span>
            <strong>{user?.full_name || user?.username}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '11px' }}>EMAIL</span>
            <strong>{user?.email}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '11px' }}>LOCATION PROFILE</span>
            <strong style={{ color: 'var(--hud-cyan)' }}>{user?.location_type || 'HOME'}</strong>
          </div>
        </div>
      </div>

      {/* Emergency Contacts Management */}
      <div className="hud-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Users size={22} color="var(--hud-cyan)" />
            <div>
              <h2 style={{ fontFamily: 'var(--font-hud)', fontSize: '18px', margin: 0 }}>
                EMERGENCY CONTACTS ({contacts.length})
              </h2>
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-dim)', margin: 0 }}>
                RECIPIENTS NOTIFIED UPON HIGH/CRITICAL INCIDENT DISPATCH
              </p>
            </div>
          </div>

          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="cmd-btn cmd-btn-primary"
            style={{ fontSize: '12px', padding: '8px 14px' }}
          >
            <Plus size={14} /> ADD CONTACT
          </button>
        </div>

        {msg && (
          <div style={{ background: 'rgba(16, 185, 129, 0.2)', border: '1px solid var(--hud-green)', padding: '10px 14px', borderRadius: '4px', color: 'var(--hud-green)', fontSize: '13px', marginBottom: '20px' }}>
            ✓ {msg}
          </div>
        )}

        {error && (
          <div style={{ background: 'rgba(239, 68, 68, 0.2)', border: '1px solid var(--hud-red)', padding: '10px 14px', borderRadius: '4px', color: '#fff', fontSize: '13px', marginBottom: '20px' }}>
            🚨 {error}
          </div>
        )}

        {/* Add Contact Form */}
        {showAddForm && (
          <form onSubmit={handleAddContact} style={{ background: 'var(--input-bg)', padding: '20px', borderRadius: '8px', border: '1px solid var(--hud-cyan)', marginBottom: '24px' }}>
            <h3 style={{ fontSize: '14px', color: 'var(--hud-cyan)', marginTop: 0, marginBottom: '16px' }}>Add New Emergency Contact</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label className="cmd-label">Full Name *</label>
                <input type="text" required placeholder="John Doe" className="cmd-input" value={fullName} onChange={e => setFullName(e.target.value)} />
              </div>
              <div>
                <label className="cmd-label">Relationship *</label>
                <select className="cmd-input" value={relationship} onChange={e => setRelationship(e.target.value)}>
                  <option value="Family">Family</option>
                  <option value="Manager">Manager</option>
                  <option value="Security Guard">Security Guard</option>
                  <option value="Neighbour">Neighbour</option>
                  <option value="Police">Police</option>
                </select>
              </div>
              <div>
                <label className="cmd-label">Phone *</label>
                <input type="text" required placeholder="+1234567890" className="cmd-input" value={phone} onChange={e => setPhone(e.target.value)} />
              </div>
              <div>
                <label className="cmd-label">WhatsApp</label>
                <input type="text" placeholder="+1234567890" className="cmd-input" value={whatsapp} onChange={e => setWhatsapp(e.target.value)} />
              </div>
            </div>

            <div style={{ marginTop: '16px', display: 'flex', gap: '10px' }}>
              <button type="submit" className="cmd-btn cmd-btn-primary" style={{ fontSize: '12px', padding: '8px 16px' }}>
                SAVE CONTACT
              </button>
              <button type="button" onClick={() => setShowAddForm(false)} className="cmd-btn cmd-btn-secondary" style={{ fontSize: '12px', padding: '8px 16px' }}>
                CANCEL
              </button>
            </div>
          </form>
        )}

        {/* Contacts List */}
        {contacts.map((c) => (
          <div key={c.id} style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '16px', marginBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontWeight: 'bold', fontSize: '14px', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                {c.full_name} <span style={{ fontSize: '11px', color: 'var(--hud-cyan)', fontWeight: 'normal' }}>({c.relationship})</span>
                {c.verified && (
                  <span style={{ fontSize: '10px', background: 'rgba(16, 185, 129, 0.2)', color: '#10b981', padding: '2px 6px', borderRadius: '4px' }}>
                    VERIFIED
                  </span>
                )}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-dim)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
                PHONE: {c.phone} | CHANNELS: {c.channels?.join(', ')}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button onClick={() => handleTestAlert(c.id)} className="cmd-btn cmd-btn-secondary" style={{ fontSize: '11px', padding: '6px 12px' }}>
                <Send size={12} /> TEST ALERT
              </button>
              <button onClick={() => handleDeleteContact(c.id)} className="cmd-btn" style={{ fontSize: '11px', padding: '6px 12px', background: 'rgba(239, 68, 68, 0.2)', color: '#ef4444', border: '1px solid #ef4444' }}>
                <Trash2 size={12} /> DELETE
              </button>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
};
