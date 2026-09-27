import React, { useState } from 'react';
import { BarChart3, LayoutDashboard, PlusCircle, ShieldCheck } from 'lucide-react';
import { ErrorBoundary } from './components/ErrorBoundary';
import { DashboardPage } from './pages/DashboardPage';
import { StatsPage } from './pages/StatsPage';
import { SubmitPage } from './pages/SubmitPage';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'submit' | 'dashboard' | 'stats'>('submit');

  return (
    <ErrorBoundary>
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <header className="navbar">
          <a href="#" className="brand" onClick={() => setActiveTab('submit')}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #3b82f6, #6366f1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
              }}
            >
              <ShieldCheck size={22} />
            </div>
            <span>CivicPulse</span>
            <span className="brand-badge">AI Intake</span>
          </a>

          <nav>
            <ul className="nav-links">
              <li>
                <button
                  className={`nav-btn ${activeTab === 'submit' ? 'active' : ''}`}
                  onClick={() => setActiveTab('submit')}
                >
                  <PlusCircle size={18} /> New Complaint
                </button>
              </li>
              <li>
                <button
                  className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
                  onClick={() => setActiveTab('dashboard')}
                >
                  <LayoutDashboard size={18} /> Staff Dashboard
                </button>
              </li>
              <li>
                <button
                  className={`nav-btn ${activeTab === 'stats' ? 'active' : ''}`}
                  onClick={() => setActiveTab('stats')}
                >
                  <BarChart3 size={18} /> Analytics & Cache
                </button>
              </li>
            </ul>
          </nav>
        </header>

        <main style={{ flex: 1, paddingBottom: '3rem' }}>
          {activeTab === 'submit' && <SubmitPage />}
          {activeTab === 'dashboard' && <DashboardPage />}
          {activeTab === 'stats' && <StatsPage />}
        </main>
      </div>
    </ErrorBoundary>
  );
};
