import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Shield, Home, ShoppingBag, Store, Film, Building2, Car, PhoneCall, CheckCircle, ShieldAlert, ArrowRight, Lock } from 'lucide-react';

const LOCATION_OPTIONS = [
  { id: 'HOME', label: 'Home / Residential', icon: Home, desc: 'Intrusion, Fall, Fire/Smoke, Loitering' },
  { id: 'SHOP_RETAIL', label: 'Shop / Retail Store', icon: Store, desc: 'Theft, Loitering, Intrusion, Crowd Density, Fire' },
  { id: 'MALL', label: 'Shopping Mall', icon: ShoppingBag, desc: 'Crowd Density, Abandoned Object, Theft, Fight, Fire' },
  { id: 'CINEMA_THEATRE', label: 'Cinema / Theatre', icon: Film, desc: 'Crowd Density, Abandoned Object, Fight, Fire, Fall' },
  { id: 'OFFICE_WAREHOUSE', label: 'Office / Warehouse', icon: Building2, desc: 'Intrusion, After-Hours Movement, Fire, Fall' },
  { id: 'ROAD_PARKING', label: 'Road / Parking Lot', icon: Car, desc: 'Vehicle Collision, Vehicle Loitering, Fire' },
];

export const OnboardingWizard = () => {
  const { checkAuth, user } = useAuth();
  const navigate = useNavigate();

  const [step, setStep] = useState(2); // 2: Location, 3: Contact, 4: OTP, 5: Done
  const [locationType, setLocationType] = useState('HOME');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Contact Form State
  const [contactName, setContactName] = useState('');
  const [relationship, setRelationship] = useState('Family');
  const [phone, setPhone] = useState('');
  const [whatsapp, setWhatsapp] = useState('');
  const [sameAsPhone, setSameAsPhone] = useState(true);
  const [email, setEmail] = useState('');
  const [channels, setChannels] = useState(['SMS']);
  const [consent, setConsent] = useState(false);

  // Verification State
  const [createdContact, setCreatedContact] = useState(null);
  const [otpCode, setOtpCode] = useState('');
  const [otpSuccess, setOtpSuccess] = useState(false);

  const handleSelectLocation = async (type) => {
    setLocationType(type);
    try {
      await api.post('/onboarding/location', { location_type: type });
      setStep(3);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to set location profile');
    }
  };

  const handleChannelToggle = (ch) => {
    if (channels.includes(ch)) {
      if (channels.length === 1) return; // Must keep at least one channel
      setChannels(channels.filter(c => c !== ch));
    } else {
      setChannels([...channels, ch]);
    }
  };

  const handleAddContactSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!consent) {
      setError('You must confirm that this person agrees to receive security alerts.');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        full_name: contactName,
        relationship,
        phone,
        whatsapp: sameAsPhone ? phone : whatsapp,
        email: email || undefined,
        channels,
        priority: 1
      };
      const res = await api.post('/contacts', payload);
      setCreatedContact(res.data);
      setLoading(false);
      setStep(4);
    } catch (err) {
      setLoading(false);
      setError(err.response?.data?.detail || 'Failed to add emergency contact');
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    if (!createdContact) return;
    setError('');
    setLoading(true);

    try {
      const res = await api.post('/contacts/verify-otp', {
        contact_id: createdContact.id,
        code: otpCode
      });
      setOtpSuccess(true);
      setLoading(false);
      await checkAuth(); // Refresh user state
      setStep(5);
    } catch (err) {
      setLoading(false);
      setError(err.response?.data?.detail || 'Invalid verification code');
    }
  };

  const handleFinishOnboarding = async () => {
    try {
      await api.post('/onboarding/complete');
      await checkAuth();
      navigate('/dashboard');
    } catch (err) {
      navigate('/dashboard');
    }
  };

  return (
    <div style={{ minHeight: 'calc(100vh - 70px)', padding: '40px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      
      {/* Wizard Card Container */}
      <div style={{ width: '100%', maxWidth: '720px', background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '32px', boxShadow: '0 20px 50px rgba(0,0,0,0.5)' }}>
        
        {/* Header Branding */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '6px 16px', borderRadius: '20px', background: 'rgba(6, 182, 212, 0.1)', border: '1px solid var(--hud-cyan)', color: 'var(--hud-cyan)', fontSize: '12px', fontWeight: 600 }}>
            <Shield size={16} /> PHYLAX ONBOARDING GUARD
          </div>
          <h2 style={{ fontFamily: 'var(--font-hud)', color: 'var(--text-main)', margin: '12px 0 4px', fontSize: '22px' }}>
            MANDATORY EMERGENCY CONTACT SETUP
          </h2>
          <p style={{ color: 'var(--text-dim)', fontSize: '13px', margin: 0 }}>
            Phylax notifies your chosen contacts when security incidents occur. At least one verified contact is required.
          </p>
        </div>

        {/* Step Progress Bar */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px', position: 'relative' }}>
          {[
            { num: 1, label: 'Account' },
            { num: 2, label: 'Location' },
            { num: 3, label: 'Contact' },
            { num: 4, label: 'OTP Verification' },
            { num: 5, label: 'Ready' }
          ].map((s, idx) => (
            <div key={s.num} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 2 }}>
              <div style={{
                width: '32px', height: '32px', borderRadius: '50%',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontWeight: 'bold', fontSize: '13px',
                background: step >= s.num ? 'var(--hud-cyan)' : 'var(--input-bg)',
                color: step >= s.num ? '#000' : 'var(--text-dim)',
                border: step === s.num ? '2px solid #fff' : '1px solid var(--border-color)',
                boxShadow: step === s.num ? '0 0 15px var(--hud-cyan)' : 'none'
              }}>
                {step > s.num ? '✓' : s.num}
              </div>
              <span style={{ fontSize: '10px', marginTop: '6px', color: step >= s.num ? 'var(--hud-cyan)' : 'var(--text-dim)' }}>
                {s.label}
              </span>
            </div>
          ))}
        </div>

        {error && (
          <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#fca5a5', padding: '12px 16px', borderRadius: '6px', fontSize: '13px', marginBottom: '20px' }}>
            🚨 {error}
          </div>
        )}

        {/* STEP 2: Choose Location Profile */}
        {step === 2 && (
          <div>
            <h3 style={{ fontSize: '16px', color: 'var(--hud-cyan)', marginBottom: '16px' }}>
              Step 2: Select Monitored Location Type
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
              {LOCATION_OPTIONS.map(opt => {
                const IconComp = opt.icon;
                return (
                  <div
                    key={opt.id}
                    onClick={() => handleSelectLocation(opt.id)}
                    style={{
                      background: 'var(--input-bg)',
                      border: locationType === opt.id ? '2px solid var(--hud-cyan)' : '1px solid var(--border-color)',
                      borderRadius: '8px',
                      padding: '16px',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <IconComp size={24} style={{ color: 'var(--hud-cyan)', marginBottom: '8px' }} />
                    <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-main)' }}>{opt.label}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px' }}>{opt.desc}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* STEP 3: Add Emergency Contact */}
        {step === 3 && (
          <form onSubmit={handleAddContactSubmit}>
            <h3 style={{ fontSize: '16px', color: 'var(--hud-cyan)', marginBottom: '16px' }}>
              Step 3: Add Primary Emergency Contact (Mandatory)
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label className="cmd-label">Full Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. John Doe"
                  className="cmd-input"
                  value={contactName}
                  onChange={(e) => setContactName(e.target.value)}
                />
              </div>

              <div>
                <label className="cmd-label">Relationship *</label>
                <select
                  className="cmd-input"
                  value={relationship}
                  onChange={(e) => setRelationship(e.target.value)}
                >
                  <option value="Owner">Owner</option>
                  <option value="Family">Family</option>
                  <option value="Manager">Manager</option>
                  <option value="Security Guard">Security Guard</option>
                  <option value="Neighbour">Neighbour</option>
                  <option value="Police">Police</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div>
                <label className="cmd-label">Primary Phone (with Country Code) *</label>
                <input
                  type="text"
                  required
                  placeholder="+1234567890"
                  className="cmd-input"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                />
              </div>

              <div>
                <label className="cmd-label">WhatsApp Number</label>
                <input
                  type="text"
                  placeholder="+1234567890"
                  disabled={sameAsPhone}
                  className="cmd-input"
                  value={sameAsPhone ? phone : whatsapp}
                  onChange={(e) => setWhatsapp(e.target.value)}
                />
                <label style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <input
                    type="checkbox"
                    checked={sameAsPhone}
                    onChange={(e) => setSameAsPhone(e.target.checked)}
                  />
                  Same as primary phone
                </label>
              </div>

              <div style={{ gridColumn: 'span 2' }}>
                <label className="cmd-label">Email Address (Recommended)</label>
                <input
                  type="email"
                  placeholder="contact@example.com"
                  className="cmd-input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            <div style={{ marginTop: '16px' }}>
              <label className="cmd-label">Preferred Notification Channels</label>
              <div style={{ display: 'flex', gap: '12px', marginTop: '6px' }}>
                {['SMS', 'WhatsApp', 'Email', 'Call'].map(ch => (
                  <button
                    key={ch}
                    type="button"
                    onClick={() => handleChannelToggle(ch)}
                    style={{
                      padding: '8px 16px',
                      borderRadius: '6px',
                      fontSize: '12px',
                      fontWeight: 600,
                      cursor: 'pointer',
                      background: channels.includes(ch) ? 'rgba(6, 182, 212, 0.2)' : 'var(--input-bg)',
                      border: channels.includes(ch) ? '1px solid var(--hud-cyan)' : '1px solid var(--border-color)',
                      color: channels.includes(ch) ? 'var(--hud-cyan)' : 'var(--text-dim)'
                    }}
                  >
                    {channels.includes(ch) ? '✓ ' : ''}{ch}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ marginTop: '20px', padding: '12px', background: 'var(--input-bg)', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
              <label style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', cursor: 'pointer', fontSize: '12px', color: 'var(--text-main)' }}>
                <input
                  type="checkbox"
                  required
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                  style={{ marginTop: '2px' }}
                />
                <span>
                  I confirm that <strong>{contactName || 'this person'}</strong> agrees to receive automated security alerts from Phylax.
                </span>
              </label>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="cmd-btn cmd-btn-primary"
              style={{ width: '100%', marginTop: '24px', padding: '12px', fontSize: '14px' }}
            >
              {loading ? 'SAVING CONTACT...' : 'SAVE & PROCEED TO VERIFICATION →'}
            </button>
          </form>
        )}

        {/* STEP 4: OTP Verification */}
        {step === 4 && (
          <form onSubmit={handleVerifyOTP} style={{ textAlign: 'center' }}>
            <h3 style={{ fontSize: '16px', color: 'var(--hud-cyan)', marginBottom: '8px' }}>
              Step 4: Verify Emergency Contact OTP
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-dim)', marginBottom: '20px' }}>
              Enter the 6-digit verification code sent to <strong>{createdContact?.phone}</strong> (or use code <strong>123456</strong> for testing).
            </p>

            <input
              type="text"
              required
              maxLength={6}
              placeholder="123456"
              style={{
                fontSize: '24px',
                letterSpacing: '8px',
                textAlign: 'center',
                width: '200px',
                padding: '12px',
                fontFamily: 'var(--font-mono)',
                marginBottom: '20px'
              }}
              className="cmd-input"
              value={otpCode}
              onChange={(e) => setOtpCode(e.target.value)}
            />

            <div>
              <button
                type="submit"
                disabled={loading}
                className="cmd-btn cmd-btn-primary"
                style={{ width: '100%', padding: '12px', fontSize: '14px' }}
              >
                {loading ? 'VERIFYING...' : 'VERIFY CONTACT NOW →'}
              </button>
            </div>
          </form>
        )}

        {/* STEP 5: Finished */}
        {step === 5 && (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <CheckCircle size={56} style={{ color: '#10b981', marginBottom: '16px' }} />
            <h3 style={{ fontSize: '20px', color: '#10b981', margin: '0 0 8px' }}>
              ONBOARDING COMPLETE!
            </h3>
            <p style={{ color: 'var(--text-dim)', fontSize: '14px', marginBottom: '24px' }}>
              Your emergency contact is verified and active. You can now access your Phylax surveillance command dashboard.
            </p>

            <button
              onClick={handleFinishOnboarding}
              className="cmd-btn cmd-btn-primary"
              style={{ padding: '12px 32px', fontSize: '14px' }}
            >
              LAUNCH DASHBOARD →
            </button>
          </div>
        )}

      </div>
    </div>
  );
};
