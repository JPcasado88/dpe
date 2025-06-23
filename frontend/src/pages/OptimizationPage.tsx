import React from 'react';
import PriceOptimizer from '../components/PriceOptimizer';
import CompetitorView from '../components/CompetitorView';

const OptimizationPage: React.FC = () => {
  return (
    <div className="optimization-page">
      <div style={{ marginBottom: '40px' }}>
        <PriceOptimizer />
      </div>
      <CompetitorView />
    </div>
  );
};

export default OptimizationPage;