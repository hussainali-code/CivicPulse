import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { StatsPage } from '../src/pages/StatsPage';
import { api } from '../src/api/client';
import { StatsResponse } from '../src/api/types';

describe('StatsPage X-Cache Badge & Metrics Presentation', () => {
  const mockStats: StatsResponse = {
    total: { total: 42 },
    by_status: {
      open: 15,
      in_progress: 12,
      resolved: 10,
      rejected: 5,
    },
    by_priority: {
      high: 8,
      normal: 24,
      low: 10,
    },
    by_category: {
      water: 14,
      electricity: 10,
      sanitation: 8,
      roads: 5,
      streetlights: 3,
      other: 2,
    },
  };

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders green badge-hit when X-Cache response header is HIT', async () => {
    vi.spyOn(api, 'getStats').mockResolvedValue({
      data: mockStats,
      xCache: 'HIT',
    });

    render(<StatsPage />);

    await waitFor(() => {
      const badge = screen.getByTestId('x-cache-badge');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('badge-hit');
      expect(badge).toHaveTextContent(/x-cache:\s*hit/i);
    });

    // Check stats counts rendered
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('Breakdown by Status')).toBeInTheDocument();
    expect(screen.getByText('Breakdown by Priority')).toBeInTheDocument();
  });

  it('renders red badge-miss when X-Cache response header is MISS', async () => {
    vi.spyOn(api, 'getStats').mockResolvedValue({
      data: mockStats,
      xCache: 'MISS',
    });

    render(<StatsPage />);

    await waitFor(() => {
      const badge = screen.getByTestId('x-cache-badge');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('badge-miss');
      expect(badge).toHaveTextContent(/x-cache:\s*miss/i);
    });
  });

  it('refreshes stats on clicking Refresh button', async () => {
    const getStatsSpy = vi.spyOn(api, 'getStats').mockResolvedValue({
      data: mockStats,
      xCache: 'MISS',
    });

    render(<StatsPage />);

    await waitFor(() => {
      expect(getStatsSpy).toHaveBeenCalledTimes(1);
    });

    const refreshBtn = screen.getByRole('button', { name: /refresh/i });
    fireEvent.click(refreshBtn);

    await waitFor(() => {
      expect(getStatsSpy).toHaveBeenCalledTimes(2);
    });
  });
});
