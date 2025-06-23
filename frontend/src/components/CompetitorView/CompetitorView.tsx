import React, { useState } from 'react';
import './CompetitorView.css';

interface Competitor {
  id: string;
  name: string;
  url: string;
  lastScraped: Date;
  productsTracked: number;
  status: 'active' | 'inactive' | 'error';
}

interface CompetitorPrice {
  productSku: string;
  productName: string;
  ourPrice: number;
  competitorPrice: number;
  priceDiff: number;
  priceDiffPercent: number;
}

const CompetitorView: React.FC = () => {
  const [selectedCompetitor, setSelectedCompetitor] = useState<string | null>(null);

  // Mock data
  const competitors: Competitor[] = [
    {
      id: '1',
      name: 'Competitor A',
      url: 'https://competitor-a.com',
      lastScraped: new Date(),
      productsTracked: 150,
      status: 'active',
    },
    {
      id: '2',
      name: 'Competitor B',
      url: 'https://competitor-b.com',
      lastScraped: new Date(Date.now() - 3600000),
      productsTracked: 200,
      status: 'active',
    },
  ];

  const competitorPrices: CompetitorPrice[] = [
    {
      productSku: 'SKU001',
      productName: 'Product 1',
      ourPrice: 29.99,
      competitorPrice: 27.99,
      priceDiff: 2.00,
      priceDiffPercent: 7.1,
    },
    {
      productSku: 'SKU002',
      productName: 'Product 2',
      ourPrice: 49.99,
      competitorPrice: 52.99,
      priceDiff: -3.00,
      priceDiffPercent: -5.7,
    },
  ];

  return (
    <div className="competitor-view">
      <h2>Competitor Analysis</h2>
      
      <div className="competitor-overview">
        <h3>Tracked Competitors</h3>
        <div className="competitor-grid">
          {competitors.map(competitor => (
            <div
              key={competitor.id}
              className={`competitor-card ${selectedCompetitor === competitor.id ? 'selected' : ''}`}
              onClick={() => setSelectedCompetitor(competitor.id)}
            >
              <div className="competitor-header">
                <h4>{competitor.name}</h4>
                <span className={`status-badge ${competitor.status}`}>
                  {competitor.status}
                </span>
              </div>
              <div className="competitor-info">
                <p>URL: {competitor.url}</p>
                <p>Products Tracked: {competitor.productsTracked}</p>
                <p>Last Scraped: {competitor.lastScraped.toLocaleString()}</p>
              </div>
              <div className="competitor-actions">
                <button className="action-btn">Rescrape</button>
                <button className="action-btn">Configure</button>
              </div>
            </div>
          ))}
        </div>
        <button className="add-competitor-btn">+ Add New Competitor</button>
      </div>

      <div className="price-comparison">
        <h3>Price Comparison</h3>
        {selectedCompetitor ? (
          <div className="comparison-table-container">
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Product Name</th>
                  <th>Our Price</th>
                  <th>Competitor Price</th>
                  <th>Difference</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {competitorPrices.map(item => (
                  <tr key={item.productSku}>
                    <td>{item.productSku}</td>
                    <td>{item.productName}</td>
                    <td>${item.ourPrice.toFixed(2)}</td>
                    <td>${item.competitorPrice.toFixed(2)}</td>
                    <td className={item.priceDiff > 0 ? 'higher' : 'lower'}>
                      ${Math.abs(item.priceDiff).toFixed(2)} ({item.priceDiffPercent > 0 ? '+' : ''}{item.priceDiffPercent.toFixed(1)}%)
                    </td>
                    <td>
                      <button className="match-price-btn">Match Price</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="no-selection">
            Select a competitor to view price comparisons
          </div>
        )}
      </div>

      <div className="competitor-insights">
        <h3>Market Insights</h3>
        <div className="insights-grid">
          <div className="insight-card">
            <h4>Average Price Position</h4>
            <p className="insight-value">+2.3%</p>
            <p className="insight-description">Above market average</p>
          </div>
          <div className="insight-card">
            <h4>Products Below Competition</h4>
            <p className="insight-value">42</p>
            <p className="insight-description">Out of 150 tracked</p>
          </div>
          <div className="insight-card">
            <h4>Price Match Opportunities</h4>
            <p className="insight-value">18</p>
            <p className="insight-description">Products to review</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompetitorView;