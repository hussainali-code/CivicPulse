import React, { useCallback, useEffect, useState } from 'react';
import { AlertCircle, LayoutDashboard, RefreshCw } from 'lucide-react';
import { api } from '../api/client';
import { ApiError, Complaint, Status } from '../api/types';
import { ComplaintCard } from '../components/ComplaintCard';
import { FilterBar } from '../components/FilterBar';
import { Pagination } from '../components/Pagination';

export const DashboardPage: React.FC = () => {
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);

  const [category, setCategory] = useState('');
  const [priority, setPriority] = useState('');
  const [status, setStatus] = useState('');

  const [loading, setLoading] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const fetchComplaints = useCallback(async () => {
    setLoading(true);
    setFetchError(null);

    try {
      const res = await api.getComplaints({
        category: category || undefined,
        priority: priority || undefined,
        status: status || undefined,
        page,
        page_size: pageSize,
      });
      setComplaints(res.items);
      setTotal(res.total);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setFetchError(err.message);
      } else {
        setFetchError('Failed to load complaints. Please check network connection.');
      }
    } finally {
      setLoading(false);
    }
  }, [category, priority, status, page, pageSize]);

  useEffect(() => {
    fetchComplaints();
  }, [fetchComplaints]);

  const handleCategoryChange = (newCategory: string) => {
    setCategory(newCategory);
    setPage(1);
  };

  const handlePriorityChange = (newPriority: string) => {
    setPriority(newPriority);
    setPage(1);
  };

  const handleStatusChange = (newStatus: string) => {
    setStatus(newStatus);
    setPage(1);
  };

  const handleResetFilters = () => {
    setCategory('');
    setPriority('');
    setStatus('');
    setPage(1);
  };

  const handleStatusTransition = async (id: string, newStatus: Status) => {
    setActionError(null);
    try {
      const updated = await api.updateComplaintStatus(id, newStatus);
      // Update local item in place so UI reflects immediately without total reload
      setComplaints((prev) =>
        prev.map((item) => (item.id === id ? updated : item))
      );
    } catch (err: any) {
      const msg =
        err instanceof ApiError ? err.message : (err?.message || 'Failed to update status');
      setActionError(msg);
      throw err; // Allow ComplaintCard to also receive and render in-card error
    }
  };

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
            <LayoutDashboard size={16} /> Staff Portal
          </div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.02em', margin: 0 }}>
            Complaints Management
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', margin: '0.25rem 0 0 0' }}>
            Monitor, triage, and progress civic issues through verified state machine workflows.
          </p>
        </div>

        <button
          type="button"
          onClick={fetchComplaints}
          disabled={loading}
          className="btn-primary"
          style={{
            padding: '0.65rem 1.25rem',
            fontSize: '0.9rem',
            background: 'rgba(30, 41, 59, 0.8)',
            border: '1px solid var(--border-subtle)',
            boxShadow: 'none',
          }}
          aria-label="Refresh complaints"
        >
          <RefreshCw size={16} className={loading ? 'spinner' : ''} /> Refresh
        </button>
      </div>

      {/* Action Error Banner (e.g. 409 Conflict exact message) */}
      {actionError && (
        <div className="alert-error" role="alert" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <AlertCircle size={20} style={{ flexShrink: 0 }} />
            <span>{actionError}</span>
          </div>
        </div>
      )}

      {/* Fetch Error Banner */}
      {fetchError && (
        <div className="alert-error" role="alert" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <AlertCircle size={20} style={{ flexShrink: 0 }} />
            <span>{fetchError}</span>
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <FilterBar
        category={category}
        priority={priority}
        status={status}
        onCategoryChange={handleCategoryChange}
        onPriorityChange={handlePriorityChange}
        onStatusChange={handleStatusChange}
        onReset={handleResetFilters}
      />

      {/* Complaints List / State rendering */}
      {loading && complaints.length === 0 ? (
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
          <span>Loading complaints...</span>
        </div>
      ) : complaints.length === 0 ? (
        <div
          className="card"
          style={{
            textAlign: 'center',
            padding: '3rem 1.5rem',
            color: 'var(--text-secondary)',
          }}
        >
          <p style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
            No complaints found
          </p>
          <p style={{ fontSize: '0.9rem', margin: 0 }}>
            No complaints match the selected filter criteria. Try adjusting or resetting your filters.
          </p>
        </div>
      ) : (
        <div>
          {complaints.map((complaint) => (
            <ComplaintCard
              key={complaint.id}
              complaint={complaint}
              onStatusChange={handleStatusTransition}
            />
          ))}

          {/* Pagination */}
          <Pagination
            page={page}
            pageSize={pageSize}
            total={total}
            onPageChange={(newPage) => setPage(newPage)}
          />
        </div>
      )}
    </div>
  );
};
