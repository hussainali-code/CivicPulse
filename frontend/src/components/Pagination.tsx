import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (newPage: number) => void;
}

export const Pagination: React.FC<PaginationProps> = ({
  page,
  pageSize,
  total,
  onPageChange,
}) => {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const isFirstPage = page <= 1;
  const isLastPage = page >= totalPages;

  const startItem = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const endItem = Math.min(page * pageSize, total);

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '1rem 0.5rem',
        marginTop: '1.5rem',
        flexWrap: 'wrap',
        gap: '1rem',
      }}
      data-testid="pagination-controls"
    >
      <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
        Showing <strong style={{ color: '#fff' }}>{startItem}</strong> to{' '}
        <strong style={{ color: '#fff' }}>{endItem}</strong> of{' '}
        <strong style={{ color: '#fff' }}>{total}</strong> complaints
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <button
          type="button"
          onClick={() => onPageChange(page - 1)}
          disabled={isFirstPage}
          style={{
            background: 'rgba(15, 23, 42, 0.6)',
            border: '1px solid var(--border-subtle)',
            color: isFirstPage ? 'var(--text-muted)' : 'var(--text-primary)',
            padding: '0.5rem 0.85rem',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: isFirstPage ? 'not-allowed' : 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.35rem',
            transition: 'all 0.2s ease',
          }}
          aria-label="Previous page"
        >
          <ChevronLeft size={16} /> Previous
        </button>

        <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', padding: '0 0.5rem' }}>
          Page <strong style={{ color: '#fff' }}>{page}</strong> of{' '}
          <strong style={{ color: '#fff' }}>{totalPages}</strong>
        </span>

        <button
          type="button"
          onClick={() => onPageChange(page + 1)}
          disabled={isLastPage}
          style={{
            background: 'rgba(15, 23, 42, 0.6)',
            border: '1px solid var(--border-subtle)',
            color: isLastPage ? 'var(--text-muted)' : 'var(--text-primary)',
            padding: '0.5rem 0.85rem',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: isLastPage ? 'not-allowed' : 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.35rem',
            transition: 'all 0.2s ease',
          }}
          aria-label="Next page"
        >
          Next <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
};
