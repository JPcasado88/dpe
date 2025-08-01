import React, { useState, useEffect } from 'react';
import './PriceOptimizer.css';
import { productAPI, analyticsAPI } from '../../services/api';
import { Product } from '../../types';

interface OptimizationSettings {
  strategy: 'competitive' | 'profit' | 'volume' | 'custom';
  minPrice: number;
  maxPrice: number;
  targetMargin: number;
  competitorWeight: number;
  demandElasticity: number;
}

interface OptimizationResult {
  productId: string;
  currentPrice: number;
  optimalPrice: number;
  expectedRevenueIncrease: number;
  confidence: number;
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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProducts, setSelectedProducts] = useState<string[]>([]);
  const [optimizationResults, setOptimizationResults] = useState<OptimizationResult[]>([]);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await productAPI.getAll();
      setProducts(response.data);
      // Select first 3 products by default
      setSelectedProducts(response.data.slice(0, 3).map((p: Product) => p.id));
    } catch (err) {
      console.error('Error fetching products:', err);
      setError('Failed to load products');
    }
  };

  const handleStrategyChange = (strategy: OptimizationSettings['strategy']) => {
    setSettings({ ...settings, strategy });
  };

  const handleSettingChange = (key: keyof OptimizationSettings, value: number) => {
    setSettings({ ...settings, [key]: value });
  };

  const handleOptimize = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('Optimizing with settings:', settings);
      
      // Make API call to optimize prices
      const apiUrl = process.env.REACT_APP_API_URL || 
        (window.location.hostname === 'dpe-fe-production.up.railway.app' 
          ? 'https://web-production-343d.up.railway.app' 
          : 'http://localhost:8000');
      const response = await fetch(`${apiUrl}/api/v1/optimize/price-recommendations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          product_ids: selectedProducts,
          strategy: settings.strategy === 'profit' ? 'maximize_profit' : 
                    settings.strategy === 'volume' ? 'maximize_volume' : 
                    settings.strategy === 'competitive' ? 'competitive' : 'balanced',
          constraints: {
            min_price: settings.minPrice,
            max_price: settings.maxPrice,
            min_margin: settings.targetMargin / 100,
            competitor_weight: settings.competitorWeight,
          }
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      // Map the response to match our expected format
      const mappedResults = data.recommendations.map((item: any) => ({
        productId: item.productId,
        productName: item.productName,
        currentPrice: item.currentPrice,
        optimalPrice: item.optimalPrice,
        expectedRevenueIncrease: item.expectedRevenueIncrease,
        confidence: item.confidence
      }));
      setOptimizationResults(mappedResults);
    } catch (err) {
      console.error('Optimization error:', err);
      setError('Failed to optimize prices. Please ensure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateImpact = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Get current analytics data
      const analyticsResponse = await analyticsAPI.getDashboard();
      console.log('Analytics data:', analyticsResponse.data);
      
      // Simulate impact based on optimization results
      if (optimizationResults.length > 0) {
        const totalRevenueIncrease = optimizationResults.reduce(
          (sum, result) => sum + result.expectedRevenueIncrease, 
          0
        );
        alert(`Simulated Revenue Impact: +${totalRevenueIncrease.toFixed(2)}%`);
      } else {
        alert('Please run optimization first to simulate impact');
      }
    } catch (err) {
      console.error('Simulation error:', err);
      setError('Failed to simulate impact. Please ensure the backend is running.');
    } finally {
      setLoading(false);
    }
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
        <button 
          className="optimize-btn" 
          onClick={handleOptimize}
          disabled={loading}
        >
          {loading ? 'Optimizing...' : 'Run Optimization'}
        </button>
        <button 
          className="simulate-btn"
          onClick={handleSimulateImpact}
          disabled={loading}
        >
          {loading ? 'Simulating...' : 'Simulate Impact'}
        </button>
      </div>

      {error && (
        <div className="error-message" style={{ color: 'red', margin: '10px 0' }}>
          {error}
        </div>
      )}

      <div className="optimizer-section">
        <h3>Optimization Results</h3>
        {optimizationResults.length > 0 ? (
          <div className="results-grid">
            {optimizationResults.map((result) => (
              <div key={result.productId} className="result-card">
                <h4>Product {result.productId}</h4>
                <p>Current Price: ${result.currentPrice.toFixed(2)}</p>
                <p>Optimal Price: ${result.optimalPrice.toFixed(2)}</p>
                <p>Revenue Increase: +{result.expectedRevenueIncrease.toFixed(1)}%</p>
                <p>Confidence: {(result.confidence * 100).toFixed(0)}%</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="preview-message">
            Configure your optimization settings and click "Run Optimization" to see results.
          </div>
        )}
      </div>
    </div>
  );
};

export default PriceOptimizer;