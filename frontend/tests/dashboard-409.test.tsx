import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DashboardPage } from '../src/pages/DashboardPage';
import { api } from '../src/api/client';
import { ApiError, Complaint, ComplaintListResponse } from '../src/api/types';

describe('DashboardPage 409 Conflict Handling', () => {
  const mockComplaint: Complaint = {
    id: 'f9999999-8888-7777-6666-555555555555',
    text: 'Streetlight pole broken and wire hanging.',
    location: 'Sector I-8/4',
    reporter_contact: 'citizen@example.com',
    category: 'streetlights',
    priority: 'high',
    status: 'resolved',
    ai_summary: 'Broken streetlight wire',
    triaged_by: 'simulated',
    triage_latency_ms: 25,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const listResponse: ComplaintListResponse = {
    items: [mockComplaint],
    total: 1,
    page: 1,
    page_size: 10,
  };

  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(api, 'getComplaints').mockResolvedValue(listResponse);
  });

  it('displays the exact verbatim 409 error message from server when status transition fails', async () => {
    const verbatimErrorMessage = "cannot transition from 'resolved' to 'in_progress'";

    vi.spyOn(api, 'updateComplaintStatus').mockRejectedValue(
      new ApiError(409, verbatimErrorMessage)
    );

    render(<DashboardPage />);

    // Wait for complaint to be displayed
    await waitFor(() => {
      expect(screen.getByText('Streetlight pole broken and wire hanging.')).toBeInTheDocument();
    });

    // Attempt invalid transition: click "In Progress" button on resolved complaint
    const inProgressBtn = screen.getByRole('button', { name: /set in progress/i });
    expect(inProgressBtn).toBeInTheDocument();
    fireEvent.click(inProgressBtn);

    // Verify verbatim error message appears in the DOM
    await waitFor(() => {
      const errorElements = screen.getAllByText(verbatimErrorMessage);
      expect(errorElements.length).toBeGreaterThan(0);
      expect(errorElements[0]).toBeInTheDocument();
    });
  });
});
