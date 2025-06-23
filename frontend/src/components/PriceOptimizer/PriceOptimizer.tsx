import React, { useState } from 'react';
import './PriceOptimizer.css';

interface OptimizationSettings {
  strategy: 'competitive' | 'profit' | 'volume' | 'custom';
  minPrice: number;
  maxPrice: number;
  targetMargin: number;
  competitorWeight: number;
  demandElasticity: number;
}

const PriceOptimizer: React.FC = () => {
  const [settings, setSettings] = useState<OptimizationSettings>({
    strategy: 'competitive',
    minPrice: 0,
    maxPrice: 1000,
    targetMargin: 30,
    competitorWeight: 0.5,
    demandElasticity: 1.2,
  });

  const handleStrategyChange = (strategy: OptimizationSettings['strategy']) => {
    setSettings({ ...settings, strategy });
  };

  const handleSettingChange = (key: keyof OptimizationSettings, value: number) => {
    setSettings({ ...settings, [key]: value });
  };

  const handleOptimize = () => {
    console.log('Optimizing with settings:', settings);
    // Implement optimization logic
  };

  return (
    <div className="price-optimizer">
      <h2>Price Optimization</h2>
      
      <div className="optimizer-section">
        <h3>Optimization Strategy</h3>
        <div className="strategy-grid">
          <div
            className={`strategy-card ${settings.strategy === 'competitive' ? 'active' : ''}`}
            onClick={() => handleStrategyChange('competitive')}
          >
            <h4>Competitive</h4>
            <p>Match or beat competitor prices while maintaining minimum margins</p>
          </div>
          <div
            className={`strategy-card ${settings.strategy === 'profit' ? 'active' : ''}`}
            onClick={() => handleStrategyChange('profit')}
          >
            <h4>Profit Maximization</h4>
            <p>Optimize prices to maximize profit margins</p>
          </div>
          <div
            className={`strategy-card ${settings.strategy === 'volume' ? 'active' : ''}`}
            onClick={() => handleStrategyChange('volume')}
          >
            <h4>Volume Optimization</h4>
            <p>Price to maximize sales volume and market share</p>
          </div>
          <div
            className={`strategy-card ${settings.strategy === 'custom' ? 'active' : ''}`}
            onClick={() => handleStrategyChange('custom')}
          >
            <h4>Custom Rules</h4>
            <p>Define custom pricing rules and constraints</p>
          </div>
        </div>
      </div>

      <div className="optimizer-section">
        <h3>Optimization Parameters</h3>
        <div className="parameters-grid">
          <div className="parameter">
            <label>Minimum Price</label>
            <input
              type="number"
              value={settings.minPrice}
              onChange={(e) => handleSettingChange('minPrice', Number(e.target.value))}
              min="0"
              step="0.01"
            />
          </div>
          <div className="parameter">
            <label>Maximum Price</label>
            <input
              type="number"
              value={settings.maxPrice}
              onChange={(e) => handleSettingChange('maxPrice', Number(e.target.value))}
              min="0"
              step="0.01"
            />
          </div>
          <div className="parameter">
            <label>Target Margin (%)</label>
            <input
              type="number"
              value={settings.targetMargin}
              onChange={(e) => handleSettingChange('targetMargin', Number(e.target.value))}
              min="0"
              max="100"
              step="1"
            />
          </div>
          <div className="parameter">
            <label>Competitor Weight (0-1)</label>
            <input
              type="number"
              value={settings.competitorWeight}
              onChange={(e) => handleSettingChange('competitorWeight', Number(e.target.value))}
              min="0"
              max="1"
              step="0.1"
            />
          </div>
          <div className="parameter">
            <label>Demand Elasticity</label>
            <input
              type="number"
              value={settings.demandElasticity}
              onChange={(e) => handleSettingChange('demandElasticity', Number(e.target.value))}
              min="0"
              step="0.1"
            />
          </div>
        </div>
      </div>

      <div className="optimizer-actions">
        <button className="optimize-btn" onClick={handleOptimize}>
          Run Optimization
        </button>
        <button className="simulate-btn">
          Simulate Impact
        </button>
      </div>

      <div className="optimizer-section">
        <h3>Optimization Preview</h3>
        <div className="preview-message">
          Configure your optimization settings and click "Run Optimization" to see results.
        </div>
      </div>
    </div>
  );
};

export default PriceOptimizer;