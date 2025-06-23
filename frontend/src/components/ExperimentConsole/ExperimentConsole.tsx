import React, { useState } from 'react';
import './ExperimentConsole.css';

interface Experiment {
  id: string;
  name: string;
  status: 'running' | 'completed' | 'paused' | 'draft';
  startDate: Date;
  endDate?: Date;
  products: number;
  strategy: string;
  uplift?: number;
}

const ExperimentConsole: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'active' | 'completed' | 'draft'>('active');

  // Mock data
  const experiments: Experiment[] = [
    {
      id: '1',
      name: 'Summer Sale Price Test',
      status: 'running',
      startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
      products: 50,
      strategy: 'A/B Test - 10% discount',
      uplift: 15.3,
    },
    {
      id: '2',
      name: 'Premium Products Optimization',
      status: 'completed',
      startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
      endDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
      products: 25,
      strategy: 'Dynamic pricing based on demand',
      uplift: 22.7,
    },
    {
      id: '3',
      name: 'Competitor Price Matching',
      status: 'paused',
      startDate: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000),
      products: 100,
      strategy: 'Match lowest competitor price',
      uplift: -5.2,
    },
  ];

  const filteredExperiments = experiments.filter(exp => {
    if (activeTab === 'active') return exp.status === 'running' || exp.status === 'paused';
    if (activeTab === 'completed') return exp.status === 'completed';
    if (activeTab === 'draft') return exp.status === 'draft';
    return false;
  });

  return (
    <div className="experiment-console">
      <div className="console-header">
        <h2>Experiment Console</h2>
        <button className="create-experiment-btn">+ Create New Experiment</button>
      </div>

      <div className="experiment-tabs">
        <button
          className={`tab ${activeTab === 'active' ? 'active' : ''}`}
          onClick={() => setActiveTab('active')}
        >
          Active Experiments
        </button>
        <button
          className={`tab ${activeTab === 'completed' ? 'active' : ''}`}
          onClick={() => setActiveTab('completed')}
        >
          Completed
        </button>
        <button
          className={`tab ${activeTab === 'draft' ? 'active' : ''}`}
          onClick={() => setActiveTab('draft')}
        >
          Drafts
        </button>
      </div>

      <div className="experiments-list">
        {filteredExperiments.map(experiment => (
          <div key={experiment.id} className="experiment-card">
            <div className="experiment-header">
              <div>
                <h3>{experiment.name}</h3>
                <span className={`experiment-status ${experiment.status}`}>
                  {experiment.status}
                </span>
              </div>
              {experiment.uplift !== undefined && (
                <div className={`uplift ${experiment.uplift > 0 ? 'positive' : 'negative'}`}>
                  {experiment.uplift > 0 ? '+' : ''}{experiment.uplift}% Revenue Impact
                </div>
              )}
            </div>
            
            <div className="experiment-details">
              <div className="detail-item">
                <span className="detail-label">Strategy:</span>
                <span className="detail-value">{experiment.strategy}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Products:</span>
                <span className="detail-value">{experiment.products}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Start Date:</span>
                <span className="detail-value">{experiment.startDate.toLocaleDateString()}</span>
              </div>
              {experiment.endDate && (
                <div className="detail-item">
                  <span className="detail-label">End Date:</span>
                  <span className="detail-value">{experiment.endDate.toLocaleDateString()}</span>
                </div>
              )}
            </div>

            <div className="experiment-actions">
              {experiment.status === 'running' && (
                <>
                  <button className="action-btn pause">Pause</button>
                  <button className="action-btn">View Results</button>
                </>
              )}
              {experiment.status === 'paused' && (
                <>
                  <button className="action-btn resume">Resume</button>
                  <button className="action-btn">View Results</button>
                </>
              )}
              {experiment.status === 'completed' && (
                <>
                  <button className="action-btn">View Report</button>
                  <button className="action-btn">Clone</button>
                </>
              )}
              <button className="action-btn">Edit</button>
            </div>
          </div>
        ))}
      </div>

      {filteredExperiments.length === 0 && (
        <div className="no-experiments">
          No {activeTab} experiments found. Create a new experiment to get started.
        </div>
      )}

      <div className="experiment-insights">
        <h3>Experiment Insights</h3>
        <div className="insights-summary">
          <div className="insight-metric">
            <h4>Active Experiments</h4>
            <p className="metric-value">2</p>
          </div>
          <div className="insight-metric">
            <h4>Average Revenue Uplift</h4>
            <p className="metric-value positive">+10.9%</p>
          </div>
          <div className="insight-metric">
            <h4>Products Under Test</h4>
            <p className="metric-value">175</p>
          </div>
          <div className="insight-metric">
            <h4>Success Rate</h4>
            <p className="metric-value">73%</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExperimentConsole;