import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ErrorBoundary } from '../src/components/ErrorBoundary';

const ProblemChild: React.FC = () => {
  throw new Error('Test crash in component');
};

describe('ErrorBoundary', () => {
  it('catches render errors and displays fallback UI', () => {
    // Suppress console.error during expected crash test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ProblemChild />
      </ErrorBoundary>
    );

    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    expect(screen.getByText(/test crash in component/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /reload application/i })).toBeInTheDocument();

    consoleSpy.mockRestore();
  });
});
