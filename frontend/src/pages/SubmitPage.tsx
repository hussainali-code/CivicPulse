import React, { useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Cpu,
  Send,
  Sparkles,
} from 'lucide-react';
import { api } from '../api/client';
import { ApiError, Complaint } from '../api/types';

export const SubmitPage: React.FC = () => {
  const [text, setText] = useState('');
  const [location, setLocation] = useState('');
  const [contact, setContact] = useState('');

  const [touched, setTouched] = useState({ text: false, location: false });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Complaint | null>(null);

  // Client validation
  const textError =
    touched.text && text.trim().length < 10
      ? 'Complaint description must be at least 10 characters.'
      : null;
  const locationError =
    touched.location && location.trim().length < 3
      ? 'Location details must be at least 3 characters.'
      : null;
  const isFormValid = text.trim().length >= 10 && location.trim().length >= 3;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched({ text: true, location: true });

    if (!isFormValid) {
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const created = await api.createComplaint({
        text: text.trim(),
        location: location.trim(),
        reporter_contact: contact.trim() || null,
      });
      setResult(created);
      setText('');
      setLocation('');
      setContact('');
      setTouched({ text: false, location: false });
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 429) {
          setError(
            `Rate limit exceeded. Too many requests submitted. ${
              err.retryAfter ? `Please retry after ${err.retryAfter} seconds.` : ''
            }`
          );
        } else {
          setError(err.message);
        }
      } else {
        setError('An unexpected error occurred while processing your request.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '2rem auto', padding: '0 1rem' }}>
      <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: 'rgba(59, 130, 246, 0.15)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            padding: '0.4rem 0.8rem',
            borderRadius: '9999px',
            color: '#60a5fa',
            fontSize: '0.85rem',
            fontWeight: 600,
            marginBottom: '1rem',
          }}
        >
          <Sparkles size={16} /> Automated Municipal Intake
        </div>
        <h1 style={{ fontSize: '2.25rem', fontWeight: 800, letterSpacing: '-0.03em', marginBottom: '0.5rem' }}>
          Report a Municipal Issue
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem', maxWidth: '540px', margin: '0 auto' }}>
          Submit public infrastructure or civic concerns. Our AI triage engine will categorize, prioritize, and dispatch your report.
        </p>
      </div>

      {error && (
        <div className="alert-error" role="alert">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        </div>
      )}

      {result && (
        <div
          className="card"
          style={{
            marginBottom: '2.5rem',
            border: '1px solid rgba(16, 185, 129, 0.4)',
            background: 'rgba(6, 78, 59, 0.15)',
          }}
          data-testid="triage-result-card"
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
            <div style={{ color: 'var(--color-low)' }}>
              <CheckCircle2 size={24} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Complaint Lodged & Triaged Successfully</h2>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace' }}>
                Ref ID: {result.id}
              </span>
            </div>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '1rem',
              marginBottom: '1.25rem',
              padding: '1rem',
              background: 'rgba(15, 23, 42, 0.6)',
              borderRadius: 'var(--radius-md)',
            }}
          >
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>
                Assigned Category
              </span>
              <span className="badge badge-normal" style={{ fontSize: '0.85rem' }}>
                {result.category}
              </span>
            </div>

            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>
                Assessed Priority
              </span>
              <span className={`badge badge-${result.priority}`} style={{ fontSize: '0.85rem' }}>
                {result.priority}
              </span>
            </div>

            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>
                Triage Provider
              </span>
              <span
                className="badge"
                style={{
                  background: 'rgba(99, 102, 241, 0.15)',
                  color: '#a5b4fc',
                  border: '1px solid rgba(99, 102, 241, 0.3)',
                  fontSize: '0.85rem',
                }}
              >
                <Cpu size={12} style={{ marginRight: '4px' }} /> {result.triaged_by}
              </span>
            </div>

            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>
                Triage Latency
              </span>
              <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={14} /> {result.triage_latency_ms} ms
              </span>
            </div>
          </div>

          {result.ai_summary && (
            <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '0.85rem 1rem', borderRadius: 'var(--radius-md)' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
                AI Extracted Summary:
              </span>
              <p style={{ fontSize: '0.95rem', color: '#fff', lineHeight: 1.5 }}>
                {result.ai_summary}
              </p>
            </div>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit} className="card" noValidate>
        <div className="form-group">
          <label htmlFor="complaint-text" className="form-label">
            Describe the Issue <span style={{ color: 'var(--color-high)' }}>*</span>
          </label>
          <textarea
            id="complaint-text"
            className="form-textarea"
            placeholder="e.g. Main water pipeline burst near Street 12, water flooding residential houses..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            onBlur={() => setTouched((prev) => ({ ...prev, text: true }))}
            maxLength={2000}
            required
            rows={5}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            {textError ? <span className="form-error">{textError}</span> : <span />}
            <span className="char-counter">{text.length} / 2000</span>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="complaint-location" className="form-label">
            Location & Sector <span style={{ color: 'var(--color-high)' }}>*</span>
          </label>
          <div style={{ position: 'relative' }}>
            <input
              id="complaint-location"
              type="text"
              className="form-input"
              placeholder="e.g. Sector F-7/2, Street 12"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              onBlur={() => setTouched((prev) => ({ ...prev, location: true }))}
              maxLength={200}
              required
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            {locationError ? <span className="form-error">{locationError}</span> : <span />}
            <span className="char-counter">{location.length} / 200</span>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="complaint-contact" className="form-label">
            Contact Email or Phone <span style={{ color: 'var(--text-muted)' }}>(Optional)</span>
          </label>
          <input
            id="complaint-contact"
            type="text"
            className="form-input"
            placeholder="e.g. citizen@example.com or +923001234567"
            value={contact}
            onChange={(e) => setContact(e.target.value)}
            maxLength={255}
          />
        </div>

        <button
          type="submit"
          className="btn-primary"
          style={{ width: '100%', marginTop: '1rem' }}
          disabled={loading}
        >
          {loading ? (
            <>
              <div className="spinner" /> Triaging with AI Engine...
            </>
          ) : (
            <>
              <Send size={18} /> Submit Complaint
            </>
          )}
        </button>
      </form>
    </div>
  );
};
