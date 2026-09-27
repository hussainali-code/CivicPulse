import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught unhandled error:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div style={{ padding: '3rem 1.5rem', textAlign: 'center', maxWidth: '600px', margin: '0 auto' }}>
          <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
            <div style={{ color: 'var(--color-high)', background: 'rgba(239, 68, 68, 0.15)', padding: '1rem', borderRadius: '50%' }}>
              <AlertTriangle size={36} />
            </div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: '700' }}>Something went wrong</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
              {this.state.error?.message || 'An unexpected rendering error occurred in the application.'}
            </p>
            <button onClick={this.handleReset} className="btn-primary" style={{ marginTop: '0.5rem' }}>
              <RefreshCw size={18} /> Reload Application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
