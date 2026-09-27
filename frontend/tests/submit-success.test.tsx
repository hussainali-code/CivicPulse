import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SubmitPage } from '../src/pages/SubmitPage';
import { api } from '../src/api/client';
import { Complaint } from '../src/api/types';

describe('SubmitPage Success & AI Result Presentation', () => {
  it('renders triage result card with category, priority, summary, provider, and latency on 201 response', async () => {
    const mockComplaint: Complaint = {
      id: '11111111-2222-3333-4444-555555555555',
      text: 'Main water pipeline burst near Street 12 flooding houses.',
      location: 'Sector F-7/2',
      reporter_contact: 'citizen@example.com',
      category: 'water',
      priority: 'high',
      status: 'open',
      ai_summary: 'Burst pipeline flooding residential street.',
      triaged_by: 'simulated',
      triage_latency_ms: 45,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    vi.spyOn(api, 'createComplaint').mockResolvedValue(mockComplaint);

    render(<SubmitPage />);

    // Fill form
    const textInput = screen.getByLabelText(/describe the issue/i);
    const locationInput = screen.getByLabelText(/location & sector/i);

    fireEvent.change(textInput, { target: { value: 'Main water pipeline burst near Street 12 flooding houses.' } });
    fireEvent.change(locationInput, { target: { value: 'Sector F-7/2' } });

    // Submit
    const submitBtn = screen.getByRole('button', { name: /submit complaint/i });
    fireEvent.click(submitBtn);

    // Verify Result Presentation
    await waitFor(() => {
      expect(screen.getByTestId('triage-result-card')).toBeInTheDocument();
      expect(screen.getByText(/complaint lodged & triaged successfully/i)).toBeInTheDocument();
      expect(screen.getByText('water')).toBeInTheDocument();
      expect(screen.getByText('high')).toBeInTheDocument();
      expect(screen.getByText(/simulated/i)).toBeInTheDocument();
      expect(screen.getByText(/45 ms/i)).toBeInTheDocument();
      expect(screen.getByText('Burst pipeline flooding residential street.')).toBeInTheDocument();
    });
  });
});
