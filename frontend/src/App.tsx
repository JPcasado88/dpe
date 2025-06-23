import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import './App.css';

// Import pages
import HomePage from './pages/HomePage';
import ProductsPage from './pages/ProductsPage';
import OptimizationPage from './pages/OptimizationPage';
import ExperimentsPage from './pages/ExperimentsPage';
import AnalyticsPage from './pages/AnalyticsPage';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="app-nav">
          <div className="nav-container">
            <div className="nav-brand">
              <h2>Dynamic Pricing Engine</h2>
            </div>
            <ul className="nav-links">
              <li>
                <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>
                  Dashboard
                </NavLink>
              </li>
              <li>
                <NavLink to="/products" className={({ isActive }) => isActive ? 'active' : ''}>
                  Products
                </NavLink>
              </li>
              <li>
                <NavLink to="/optimization" className={({ isActive }) => isActive ? 'active' : ''}>
                  Optimization
                </NavLink>
              </li>
              <li>
                <NavLink to="/experiments" className={({ isActive }) => isActive ? 'active' : ''}>
                  Experiments
                </NavLink>
              </li>
              <li>
                <NavLink to="/analytics" className={({ isActive }) => isActive ? 'active' : ''}>
                  Analytics
                </NavLink>
              </li>
            </ul>
          </div>
        </nav>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/products" element={<ProductsPage />} />
            <Route path="/optimization" element={<OptimizationPage />} />
            <Route path="/experiments" element={<ExperimentsPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
