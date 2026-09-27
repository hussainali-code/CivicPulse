import React, { useEffect, useState } from 'react';
import {
  Activity,
  AlertCircle,
  BarChart3,
  CheckCircle,
  Clock,
  Layers,
  RefreshCw,
  Zap,
} from 'lucide-react';
import { api } from '../api/client';
import { ApiError, StatsResponse } from '../api/types';

export const StatsPage: React.FC = () => {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [xCache, setXCache] = useState<string>('MISS');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastFetched, setLastFetched] = useState<Date | null>(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getStats();
      setStats(res.data);
      setXCache(res.xCache);
      setLastFetched(new Date());
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to fetch platform metrics.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const isHit = xCache.toUpperCase().includes('HIT');

  return (
    <div style={{ maxWidth: '1000px', margin: '2rem auto', padding: '0 1rem' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '2rem',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              color: 'var(--color-primary)',
              fontSize: '0.85rem',
              fontWeight: 600,
              marginBottom: '0.5rem',
            }}
          >
            <BarChart3 size={16} /> Analytics & Performance
          </div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.02em', margin: 0 }}>
            Platform Statistics & Cache
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', margin: '0.25rem 0 0 0' }}>
            Real-time complaint aggregation with 60-second Redis caching and cache state visibility.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {/* Prominent X-Cache Badge */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              background: 'rgba(15, 23, 42, 0.7)',
              padding: '0.5rem 0.85rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              Response Header:
            </span>
            <span
              data-testid="x-cache-badge"
              className={`badge ${isHit ? 'badge-hit' : 'badge-miss'}`}
              style={{ fontSize: '0.85rem', padding: '0.35rem 0.75rem' }}
            >
              <Zap size={14} /> X-Cache: {xCache.toUpperCase()}
            </span>
          </div>

          <button
            type="button"
            onClick={fetchStats}
            disabled={loading}
            className="btn-primary"
            style={{
              padding: '0.65rem 1.25rem',
              fontSize: '0.9rem',
            }}
            aria-label="Refresh stats"
          >
            <RefreshCw size={16} className={loading ? 'spinner' : ''} /> Refresh
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="alert-error" role="alert" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && !stats && (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '4rem 1rem',
            color: 'var(--text-secondary)',
          }}
        >
          <div className="spinner" style={{ width: '2rem', height: '2rem', marginBottom: '1rem' }} />
          <span>Loading platform metrics...</span>
        </div>
      )}

      {stats && (
        <div>
          {/* Total Complaints Banner Card */}
          <div
            className="card"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '1.5rem',
              padding: '1.5rem 2rem',
              background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(99, 102, 241, 0.05))',
              border: '1px solid rgba(59, 130, 246, 0.3)',
            }}
          >
            <div>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                Total Lodged Complaints
              </span>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: '#fff', letterSpacing: '-0.03em' }}>
                {stats.total.total}
              </div>
            </div>
            {lastFetched && (
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'right' }}>
                <Clock size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
                Updated {lastFetched.toLocaleTimeString()}
              </div>
            )}
          </div>

          {/* Grid: By Status & By Priority */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '1.5rem',
              marginBottom: '1.5rem',
            }}
          >
            {/* By Status */}
            <div className="card">
              <h2
                style={{
                  fontSize: '1.1rem',
                  fontWeight: 700,
                  marginBottom: '1.25rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                }}
              >
                <Layers size={18} style={{ color: 'var(--color-primary)' }} />
                Breakdown by Status
              </h2>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {[
                  { key: 'open', label: 'Open', colorClass: 'badge-open' },
                  { key: 'in_progress', label: 'In Progress', colorClass: 'badge-in_progress' },
                  { key: 'resolved', label: 'Resolved', colorClass: 'badge-resolved' },
                  { key: 'rejected', label: 'Rejected', colorClass: 'badge-rejected' },
                ].map(({ key, label, colorClass }) => {
                  const count = stats.by_status[key] || 0;
                  const pct = stats.total.total > 0 ? ((count / stats.total.total) * 100).toFixed(0) : '0';
                  return (
                    <div
                      key={key}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '0.65rem 0.85rem',
                        background: 'rgba(15, 23, 42, 0.5)',
                        borderRadius: 'var(--radius-md)',
                      }}
                    >
                      <span className={`badge ${colorClass}`}>{label}</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{pct}%</span>
                        <strong style={{ fontSize: '1.1rem', color: '#fff' }}>{count}</strong>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* By Priority */}
            <div className="card">
              <h2
                style={{
                  fontSize: '1.1rem',
                  fontWeight: 700,
                  marginBottom: '1.25rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                }}
              >
                <Activity size={18} style={{ color: 'var(--color-accent)' }} />
                Breakdown by Priority
              </h2>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {[
                  { key: 'high', label: 'High Priority', colorClass: 'badge-high' },
                  { key: 'normal', label: 'Normal Priority', colorClass: 'badge-normal' },
                  { key: 'low', label: 'Low Priority', colorClass: 'badge-low' },
                ].map(({ key, label, colorClass }) => {
                  const count = stats.by_priority[key] || 0;
                  const pct = stats.total.total > 0 ? ((count / stats.total.total) * 100).toFixed(0) : '0';
                  return (
                    <div
                      key={key}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '0.65rem 0.85rem',
                        background: 'rgba(15, 23, 42, 0.5)',
                        borderRadius: 'var(--radius-md)',
                      }}
                    >
                      <span className={`badge ${colorClass}`}>{label}</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{pct}%</span>
                        <strong style={{ fontSize: '1.1rem', color: '#fff' }}>{count}</strong>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* By Category */}
          <div className="card">
            <h2
              style={{
                fontSize: '1.1rem',
                fontWeight: 700,
                marginBottom: '1.25rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              <CheckCircle size={18} style={{ color: 'var(--color-low)' }} />
              Breakdown by Category
            </h2>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                gap: '1rem',
              }}
            >
              {['water', 'electricity', 'sanitation', 'roads', 'streetlights', 'other'].map((cat) => {
                const count = stats.by_category[cat] || 0;
                return (
                  <div
                    key={cat}
                    style={{
                      padding: '1rem',
                      background: 'rgba(15, 23, 42, 0.5)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <div
                      style={{
                        textTransform: 'capitalize',
                        fontSize: '0.85rem',
                        color: 'var(--text-secondary)',
                        marginBottom: '0.35rem',
                        fontWeight: 600,
                      }}
                    >
                      {cat}
                    </div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#fff' }}>
                      {count}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
