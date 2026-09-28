import React from 'react';
import { Filter, RotateCcw } from 'lucide-react';
import { Category, Priority, Status } from '../api/types';

export interface FilterBarProps {
  category: string;
  priority: string;
  status: string;
  onCategoryChange: (category: string) => void;
  onPriorityChange: (priority: string) => void;
  onStatusChange: (status: string) => void;
  onReset: () => void;
}

const CATEGORIES: { value: Category | ''; label: string }[] = [
  { value: '', label: 'All Categories' },
  { value: 'water', label: 'Water' },
  { value: 'electricity', label: 'Electricity' },
  { value: 'sanitation', label: 'Sanitation' },
  { value: 'roads', label: 'Roads' },
  { value: 'streetlights', label: 'Streetlights' },
  { value: 'other', label: 'Other' },
];

const PRIORITIES: { value: Priority | ''; label: string }[] = [
  { value: '', label: 'All Priorities' },
  { value: 'high', label: 'High Priority' },
  { value: 'normal', label: 'Normal Priority' },
  { value: 'low', label: 'Low Priority' },
];

const STATUSES: { value: Status | ''; label: string }[] = [
  { value: '', label: 'All Statuses' },
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'rejected', label: 'Rejected' },
];

export const FilterBar: React.FC<FilterBarProps> = ({
  category,
  priority,
  status,
  onCategoryChange,
  onPriorityChange,
  onStatusChange,
  onReset,
}) => {
  const hasActiveFilters = Boolean(category || priority || status);

  return (
    <div
      className="card"
      style={{
        padding: '1.25rem 1.5rem',
        marginBottom: '1.5rem',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem',
      }}
      data-testid="filter-bar"
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)' }}>
        <Filter size={18} />
        <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Filters</span>
      </div>

      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: '1rem',
          flex: 1,
          justifyContent: 'flex-start',
        }}
      >
        <div style={{ minWidth: '160px', flex: '1 1 160px' }}>
          <label
            htmlFor="category-filter"
            style={{
              display: 'block',
              fontSize: '0.75rem',
              fontWeight: 600,
              color: 'var(--text-muted)',
              marginBottom: '0.25rem',
            }}
          >
            Category
          </label>
          <select
            id="category-filter"
            aria-label="Category"
            className="form-select"
            value={category}
            onChange={(e) => onCategoryChange(e.target.value)}
          >
            {CATEGORIES.map((cat) => (
              <option key={cat.value} value={cat.value}>
                {cat.label}
              </option>
            ))}
          </select>
        </div>

        <div style={{ minWidth: '160px', flex: '1 1 160px' }}>
          <label
            htmlFor="priority-filter"
            style={{
              display: 'block',
              fontSize: '0.75rem',
              fontWeight: 600,
              color: 'var(--text-muted)',
              marginBottom: '0.25rem',
            }}
          >
            Priority
          </label>
          <select
            id="priority-filter"
            aria-label="Priority"
            className="form-select"
            value={priority}
            onChange={(e) => onPriorityChange(e.target.value)}
          >
            {PRIORITIES.map((pri) => (
              <option key={pri.value} value={pri.value}>
                {pri.label}
              </option>
            ))}
          </select>
        </div>

        <div style={{ minWidth: '160px', flex: '1 1 160px' }}>
          <label
            htmlFor="status-filter"
            style={{
              display: 'block',
              fontSize: '0.75rem',
              fontWeight: 600,
              color: 'var(--text-muted)',
              marginBottom: '0.25rem',
            }}
          >
            Status
          </label>
          <select
            id="status-filter"
            aria-label="Status"
            className="form-select"
            value={status}
            onChange={(e) => onStatusChange(e.target.value)}
          >
            {STATUSES.map((st) => (
              <option key={st.value} value={st.value}>
                {st.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <button
          type="button"
          onClick={onReset}
          disabled={!hasActiveFilters}
          style={{
            background: 'transparent',
            border: '1px solid var(--border-subtle)',
            color: hasActiveFilters ? 'var(--text-primary)' : 'var(--text-muted)',
            padding: '0.65rem 1rem',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: hasActiveFilters ? 'pointer' : 'not-allowed',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            transition: 'all 0.2s ease',
          }}
          aria-label="Reset filters"
        >
          <RotateCcw size={14} /> Reset
        </button>
      </div>
    </div>
  );
};
