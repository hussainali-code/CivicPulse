import React, { useState } from 'react';
import {
  AlertCircle,
  Clock,
  Cpu,
  MapPin,
  Sparkles,
  User,
  X,
} from 'lucide-react';
import { api } from '../api/client';
import { ApiError, Complaint, Status } from '../api/types';
import { StatusBadge } from './StatusBadge';

export interface ComplaintCardProps {
  complaint: Complaint;
  onStatusChange?: (id: string, newStatus: Status) => Promise<void>;
}

export const ComplaintCard: React.FC<ComplaintCardProps> = ({
  complaint,
  onStatusChange,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStatusTransition = async (targetStatus: Status) => {
    if (targetStatus === complaint.status || loading) return;

    setError(null);
    setLoading(true);
    try {
      if (onStatusChange) {
        await onStatusChange(complaint.id, targetStatus);
      } else {
        await api.updateComplaintStatus(complaint.id, targetStatus);
      }
    } catch (err: any) {
      const msg = err instanceof ApiError ? err.message : (err?.message || 'Failed to update status');
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const formattedDate = new Date(complaint.created_at).toLocaleString('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });

  return (
    <div
      className="card"
      style={{
        padding: '1.5rem',
        marginBottom: '1rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
      }}
      data-testid={`complaint-card-${complaint.id}`}
    >
      {/* Top Header: ID, Badges, Date */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: '0.75rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <StatusBadge status={complaint.status} />
          <span className={`badge badge-${complaint.priority}`}>
            {complaint.priority}
          </span>
          <span className="badge badge-normal">{complaint.category}</span>
          <span
            style={{
              fontSize: '0.8rem',
              color: 'var(--text-muted)',
              fontFamily: 'JetBrains Mono, monospace',
            }}
          >
            #{complaint.id.slice(0, 8)}
          </span>
        </div>

        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          {formattedDate}
        </div>
      </div>

      {/* Description Text */}
      <p style={{ fontSize: '1rem', color: '#fff', lineHeight: 1.5, margin: 0 }}>
        {complaint.text}
      </p>

      {/* AI Summary if present */}
      {complaint.ai_summary && (
        <div
          style={{
            background: 'rgba(99, 102, 241, 0.1)',
            borderLeft: '3px solid var(--color-accent)',
            padding: '0.65rem 0.85rem',
            borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
            fontSize: '0.875rem',
            color: '#c7d2fe',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.5rem',
          }}
        >
          <Sparkles size={16} style={{ flexShrink: 0, marginTop: '2px', color: '#818cf8' }} />
          <div>
            <strong style={{ color: '#e0e7ff', display: 'block', fontSize: '0.75rem', marginBottom: '0.2rem' }}>
              AI Summary
            </strong>
            {complaint.ai_summary}
          </div>
        </div>
      )}

      {/* Meta Info: Location, Reporter, Triage Latency & Provider */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '1.25rem',
          fontSize: '0.85rem',
          color: 'var(--text-secondary)',
          paddingTop: '0.5rem',
          borderTop: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <MapPin size={15} style={{ color: 'var(--color-primary)' }} />
          <span>{complaint.location}</span>
        </div>

        {complaint.reporter_contact && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <User size={15} style={{ color: 'var(--text-muted)' }} />
            <span>{complaint.reporter_contact}</span>
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Cpu size={15} style={{ color: '#a5b4fc' }} />
          <span>{complaint.triaged_by}</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Clock size={15} style={{ color: 'var(--text-muted)' }} />
          <span>{complaint.triage_latency_ms} ms</span>
        </div>
      </div>

      {/* Status Transition Action Buttons */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.75rem',
          paddingTop: '0.75rem',
          borderTop: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>
          Transition Status:
        </div>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          <button
            type="button"
            onClick={() => handleStatusTransition('open')}
            disabled={loading || complaint.status === 'open'}
            style={{
              padding: '0.35rem 0.75rem',
              fontSize: '0.8rem',
              fontWeight: 600,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              background:
                complaint.status === 'open'
                  ? 'rgba(245, 158, 11, 0.25)'
                  : 'rgba(245, 158, 11, 0.1)',
              color: '#fbbf24',
              cursor: complaint.status === 'open' || loading ? 'not-allowed' : 'pointer',
              opacity: complaint.status === 'open' ? 0.6 : 1,
            }}
            aria-label="Set Open"
          >
            Open
          </button>

          <button
            type="button"
            onClick={() => handleStatusTransition('in_progress')}
            disabled={loading || complaint.status === 'in_progress'}
            style={{
              padding: '0.35rem 0.75rem',
              fontSize: '0.8rem',
              fontWeight: 600,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              background:
                complaint.status === 'in_progress'
                  ? 'rgba(59, 130, 246, 0.25)'
                  : 'rgba(59, 130, 246, 0.1)',
              color: '#60a5fa',
              cursor: complaint.status === 'in_progress' || loading ? 'not-allowed' : 'pointer',
              opacity: complaint.status === 'in_progress' ? 0.6 : 1,
            }}
            aria-label="Set In Progress"
          >
            In Progress
          </button>

          <button
            type="button"
            onClick={() => handleStatusTransition('resolved')}
            disabled={loading || complaint.status === 'resolved'}
            style={{
              padding: '0.35rem 0.75rem',
              fontSize: '0.8rem',
              fontWeight: 600,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              background:
                complaint.status === 'resolved'
                  ? 'rgba(16, 185, 129, 0.25)'
                  : 'rgba(16, 185, 129, 0.1)',
              color: '#34d399',
              cursor: complaint.status === 'resolved' || loading ? 'not-allowed' : 'pointer',
              opacity: complaint.status === 'resolved' ? 0.6 : 1,
            }}
            aria-label="Set Resolved"
          >
            Resolved
          </button>

          <button
            type="button"
            onClick={() => handleStatusTransition('rejected')}
            disabled={loading || complaint.status === 'rejected'}
            style={{
              padding: '0.35rem 0.75rem',
              fontSize: '0.8rem',
              fontWeight: 600,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid rgba(100, 116, 139, 0.3)',
              background:
                complaint.status === 'rejected'
                  ? 'rgba(100, 116, 139, 0.25)'
                  : 'rgba(100, 116, 139, 0.1)',
              color: '#94a3b8',
              cursor: complaint.status === 'rejected' || loading ? 'not-allowed' : 'pointer',
              opacity: complaint.status === 'rejected' ? 0.6 : 1,
            }}
            aria-label="Set Rejected"
          >
            Rejected
          </button>
        </div>
      </div>

      {/* Error alert on transition error (409 Conflict exact message) */}
      {error && (
        <div
          className="alert-error"
          role="alert"
          style={{ margin: '0.5rem 0 0 0', padding: '0.75rem 1rem' }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '0.5rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <AlertCircle size={18} style={{ flexShrink: 0 }} />
              <span data-testid="transition-error-message">{error}</span>
            </div>
            <button
              type="button"
              onClick={() => setError(null)}
              style={{
                background: 'none',
                border: 'none',
                color: '#fca5a5',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                padding: '2px',
              }}
              aria-label="Dismiss error"
            >
              <X size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
