import React from 'react';
import { Status } from '../api/types';

interface StatusBadgeProps {
  status: Status;
  className?: string;
}

const STATUS_LABELS: Record<Status, string> = {
  open: 'Open',
  in_progress: 'In Progress',
  resolved: 'Resolved',
  rejected: 'Rejected',
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const label = STATUS_LABELS[status] || status;
  return (
    <span
      className={`badge badge-${status} ${className}`.trim()}
      data-testid={`status-badge-${status}`}
    >
      {label}
    </span>
  );
};
