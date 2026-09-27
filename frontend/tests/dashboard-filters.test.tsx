import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DashboardPage } from '../src/pages/DashboardPage';
import { api } from '../src/api/client';
import { Complaint, ComplaintListResponse } from '../src/api/types';

describe('DashboardPage Filter Controls', () => {
  const mockComplaints: Complaint[] = [
    {
      id: 'c1-1111-2222',
      text: 'Water pipe leak on 5th avenue.',
      location: 'Sector G-9/1',
      reporter_contact: 'resident@example.com',
      category: 'water',
      priority: 'high',
      status: 'open',
      ai_summary: 'Water leakage',
      triaged_by: 'simulated',
      triage_latency_ms: 30,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];

  const emptyResponse: ComplaintListResponse = {
    items: mockComplaints,
    total: 1,
    page: 1,
    page_size: 10,
  };

  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(api, 'getComplaints').mockResolvedValue(emptyResponse);
  });

  it('renders filter dropdowns and fetches complaints initially', async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(api.getComplaints).toHaveBeenCalledTimes(1);
    });

    expect(screen.getByLabelText(/category/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/priority/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/status/i)).toBeInTheDocument();
    expect(screen.getByText('Water pipe leak on 5th avenue.')).toBeInTheDocument();
  });

  it('filters by category and triggers refetch with category query parameter', async () => {
    render(<DashboardPage />);

    const categorySelect = screen.getByLabelText(/category/i);
    fireEvent.change(categorySelect, { target: { value: 'water' } });

    await waitFor(() => {
      expect(api.getComplaints).toHaveBeenCalledWith(
        expect.objectContaining({
          category: 'water',
          page: 1,
        })
      );
    });
  });

  it('filters by priority and triggers refetch with priority parameter', async () => {
    render(<DashboardPage />);

    const prioritySelect = screen.getByLabelText(/priority/i);
    fireEvent.change(prioritySelect, { target: { value: 'high' } });

    await waitFor(() => {
      expect(api.getComplaints).toHaveBeenCalledWith(
        expect.objectContaining({
          priority: 'high',
          page: 1,
        })
      );
    });
  });

  it('filters by status and triggers refetch with status parameter', async () => {
    render(<DashboardPage />);

    const statusSelect = screen.getByLabelText(/status/i);
    fireEvent.change(statusSelect, { target: { value: 'in_progress' } });

    await waitFor(() => {
      expect(api.getComplaints).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 'in_progress',
          page: 1,
        })
      );
    });
  });

  it('resets filters when Reset button is clicked', async () => {
    render(<DashboardPage />);

    const categorySelect = screen.getByLabelText(/category/i);
    fireEvent.change(categorySelect, { target: { value: 'sanitation' } });

    const resetBtn = screen.getByRole('button', { name: /reset/i });
    expect(resetBtn).not.toBeDisabled();
    fireEvent.click(resetBtn);

    await waitFor(() => {
      expect(api.getComplaints).toHaveBeenLastCalledWith(
        expect.objectContaining({
          category: undefined,
          priority: undefined,
          status: undefined,
          page: 1,
        })
      );
    });
  });
});
