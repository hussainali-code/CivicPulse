import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SubmitPage } from '../src/pages/SubmitPage';
import { api } from '../src/api/client';

describe('SubmitPage Client Validation', () => {
  it('displays client-side validation errors when submitting invalid text or location without calling API', async () => {
    const createSpy = vi.spyOn(api, 'createComplaint').mockResolvedValue({} as any);

    render(<SubmitPage />);

    const submitBtn = screen.getByRole('button', { name: /submit complaint/i });
    fireEvent.click(submitBtn);

    // Expect validation errors in DOM
    expect(screen.getByText(/complaint description must be at least 10 characters/i)).toBeInTheDocument();
    expect(screen.getByText(/location details must be at least 3 characters/i)).toBeInTheDocument();

    // Verify API was NOT called
    expect(createSpy).not.toHaveBeenCalled();
  });
});
